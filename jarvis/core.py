#!/usr/bin/env python3

###############################################################################
# Module Imports
###############################################################################

import arrow
import collections
import functools
import logbook
import pathlib
import pyscp
import re
import yaml

from playhouse import dataset
from . import ext, lex, utils, db

###############################################################################
# Logging
###############################################################################

logdir = pathlib.Path('logs')
if not logdir.exists():
    logdir.mkdir()
logbook.FileHandler('logs/jarvis.log').push_application()
log = logbook.Logger(__name__)

###############################################################################
# Config
###############################################################################

with open('config.yaml') as file:
    config = utils.AttrDict.from_nested_dict(yaml.safe_load(file))

###############################################################################
# Page Cache
###############################################################################

wiki = pyscp.wikidot.Wiki('www.scp-wiki.net')
wlwiki = pyscp.wikidot.Wiki('wanderers-library')
stats_wiki = pyscp.wikidot.Wiki('scp-stats')
stats_wiki.auth(config.wiki.name, config.wiki.password)


def refresh():
    global pages
    global wlpages
    kwargs = dict(body='title created_by created_at rating tags', category='*')
    if config.debug:
        db = dataset.DataSet('sqlite:///jarvis/tests/resources/snapshot.db')
        data = []
        for p in db['page'].all():
            page = wiki(p['url'])
            for k, v in p.items():
                page._body[k] = v
            data.append(page)
        wiki.titles = lambda: {}
        pyscp.utils.default_logging(True)
    else:
        data = wiki.list_pages(**kwargs)
        wiki.titles.cache_clear()
    pages = ext.PageView(data)
    wiki.metadata.cache_clear()

    if not config.debug:
        wlpages = ext.PageView(wlwiki.list_pages(**kwargs))


refresh()


###############################################################################
# Core Functions
###############################################################################


COMMANDS = {}
RULES = []


class Inp:
    """Wrap input data."""

    def __init__(self, text, user, channel, send, privileges, raw):
        """Clean input values."""
        self.text = text or ''
        self.user = str(user).strip().lower()
        self.channel = str(channel).strip().lower()
        self._send = send
        self._priv = privileges
        self.raw = raw

        self.private = self.notice = self.multiline = False

    def send(self, text, private=None, notice=None, multiline=None):
        """Send output data."""
        if not text:
            return

        private = private if private is not None else self.private
        notice = notice if notice is not None else self.notice
        multiline = multiline if multiline is not None else self.multiline

        text = text if multiline else [text]
        for line in text:
            line = str(line)
            if self.user != self.channel and not (notice or private):
                line = '{}: {}'.format(self.user, line)
            self._send(line, private=private, notice=notice)

    @property
    def privileges(self):
        return self._priv()

    @property
    def config(self):
        return CachedConfig(self.channel, self.user)


class CachedConfig:

    _cache = collections.defaultdict(dict)
    _CHANCONF = dict(
        memos='all',
        lcratings=True,
        keeplogs=True,
        urbandict=True,
        gibber=True)

    def __init__(self, channel, user):
        self.channel, self.user = channel, user

    def _get_channel_config(self, name, default):
        cache = self._cache[self.channel]
        if name not in cache:
            inst = db.ChannelConfig.find_one(channel=self.channel)
            value = getattr(inst, name) if inst else None
            cache[name] = value if value is not None else default
        return cache[name]

    def _set_channel_config(self, name, value):
        cache = self._cache[self.channel]
        inst = db.ChannelConfig.find_one(channel=self.channel)
        if not inst:
            inst = db.ChannelConfig.create(channel=self.channel)
        setattr(inst, name, value)
        inst.save()
        cache[name] = value

    def __getattr__(self, attr):
        if attr in self._CHANCONF:
            return self._get_channel_config(attr, self._CHANCONF[attr])
        else:
            return super().__getattr__(attr)

    def __setattr__(self, attr, value):
        if attr in self._CHANCONF:
            self._set_channel_config(attr, value)
        else:
            super().__setattr__(attr, value)


def _call_func(inp, func, text):
    inp.text = text
    inp.private = inp.notice = inp.multiline = False
    try:
        inp.send(func(inp))
    except Exception as e:
        if config.debug:
            raise e
        log.exception(e)
        inp.send(lex.error, private=False, notice=False, multiline=False)


def _get_command_func(inp):
    name = re.match(r'[\.!]([^\s]+)', inp.text.lower())
    if not name:
        return
    name = name.group(1)

    if name in COMMANDS:
        return COMMANDS[name]

    commands = [k for k in COMMANDS if k.startswith(name)]
    commands = list({COMMANDS[k] for k in commands})

    if len(commands) == 1:
        return commands[0]
    if len(commands) > 1:
        names = {f.__name__ for f in commands}
        inp.send(lex.unclear(options=sorted(names)))


def dispatcher(inp):
    """
    Dispatch the correct command based on the input text.

    This is the main entry point for the jarvis' commands. It also acts as
    an autocompleter, automatically executing the commands if their partial
    name is used, or returning a disambiguation prompt if multiple commands
    match the partial input.
    """
    funcs = collections.OrderedDict()

    command = _get_command_func(inp)
    if command:
        funcs[command] = ' '.join(inp.text.strip().split(' ')[1:])

    for k, v in RULES:
        match = re.match(k, inp.text)
        if match:
            funcs[v] = match.group(1)

    for func, text in funcs.items():
        _call_func(inp, func, text)


###############################################################################
# Command Decorators
###############################################################################


def command(func):
    """Register a new command."""
    COMMANDS[func.__name__] = func
    return func


def alias(name):
    """Add another alias to the command."""
    def inner(func):
        COMMANDS[name] = func
        return func
    return inner


def rule(regex):
    """Add a regex rule which would trigger the command."""
    def inner(func):
        RULES.append((regex, func))
        return func
    return inner


def require(channel=None, level=0):
    def decorator(func):
        @functools.wraps(func)
        def inner(inp, *args, **kwargs):
            if inp.privileges.get(channel or inp.channel, -1) < level:
                return lex.denied.low_level
            return func(inp, *args, **kwargs)
        return inner
    return decorator


def crosschannel(func):
    @functools.wraps(func)
    def inner(inp, *args, channel, **kwargs):
        if channel:
            if channel not in inp.privileges:
                return lex.denied.not_in_channel
            inp.channel = channel
            inp.notice = True
        return func(inp, *args, **kwargs)
    return inner


def sendmode(mode):
    def decorator(func):
        @functools.wraps(func)
        def inner(inp, *args, **kwargs):
            setattr(inp, mode, True)
            return func(inp, *args, **kwargs)
        return inner
    return decorator


private = sendmode('private')
notice = sendmode('notice')
multiline = sendmode('multiline')


def cooldown(time):
    def decorator(func):
        func._cooldown = {}

        @functools.wraps(func)
        def inner(inp, *args, **kwargs):
            now = arrow.now()

            if inp.channel not in func._cooldown:
                pass
            elif (now - func._cooldown[inp.channel]).seconds < time:
                inp.multiline = False
                return lex.cooldown

            func._cooldown[inp.channel] = now
            return func(inp, *args, **kwargs)
        return inner
    return decorator
