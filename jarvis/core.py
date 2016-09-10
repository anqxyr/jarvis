#!/usr/bin/env python3

###############################################################################
# Module Imports
###############################################################################

import arrow
import collections
import functools
import logbook
import pyscp
import re
import yaml

from . import ext, lex

###############################################################################
# Logging
###############################################################################

logbook.FileHandler('jarvis.log').push_application()
log = logbook.Logger(__name__)

###############################################################################
# Config
###############################################################################


class _AttributeDict(dict):

    def __getattr__(self, name):
        value = self[name]
        if isinstance(value, dict):
            return self.__class__(value)
        return value


with open('config.yaml') as file:
    config = _AttributeDict(yaml.load(file))

###############################################################################
# Page Cache
###############################################################################

wiki = pyscp.wikidot.Wiki('www.scp-wiki.net')
wlwiki = pyscp.wikidot.Wiki('wanderers-library')


def refresh():
    global pages
    global wlpages
    kwargs = dict(body='title created_by created_at rating tags', category='*')
    if config.debug:
        pyscp.utils.default_logging(True)
        data = wiki._list_pages_parsed(author='anqxyr', **kwargs)
    else:
        data = wiki.list_pages(**kwargs)
    pages = ext.PageView(data)
    wiki.titles.cache_clear()
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
        self.text = text.strip() if text else ''
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
            if hasattr(line, 'compose'):
                line = line.compose(self)
            if self.user != self.channel and not (notice or private):
                line = '{}: {}'.format(self.user, line)
            self._send(line, private=private, notice=notice)

    @property
    def privileges(self):
        return self._priv()


def choose_input(options):
    options = list(map('\x02{}\x02'.format, options))
    if len(options) <= 5:
        head, tail = options[:-1], options[-1]
        msg = lex.input.options
    else:
        head, tail = options[:5], len(options[5:])
        msg = lex.input.cropped_options
    return msg(head=', '.join(head), tail=tail)


def dispatcher(inp):
    """
    Dispatch the correct command based on the input text.

    This is the main entry point for the jarvis' commands. It also acts as
    an autocompleter, automatically executing the commands if their partial
    name is used, or returning a disambiguation prompt if multiple commands
    match the partial input.
    """
    funcs = collections.OrderedDict()

    name = inp.text.split(' ')[0]
    name = name[1:] if name[0] in '.!' else None
    text = ' '.join(inp.text.split(' ')[1:])

    if name in COMMANDS:
        funcs[COMMANDS[name]] = text
    elif name:
        cmds = {v for k, v in COMMANDS.items() if k.startswith(name)}
        if len(cmds) > 1:
            inp.send(choose_input([f.__name__ for f in cmds]))
        elif cmds:
            funcs[next(iter(cmds))] = text

    for k, v in RULES:
        match = re.match(k, inp.text)
        if match:
            funcs[v] = match.group(1)

    for func, text in funcs.items():
        inp.text = text
        inp.private = inp.notice = inp.multiline = False
        try:
            inp.send(func(inp))
        except Exception as e:
            if config.debug:
                raise e
            log.exception(e)
            inp.send(lex.error, private=False, notice=False, multiline=False)


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


def require(channel, level=0):
    def decorator(func):
        @functools.wraps(func)
        def inner(inp, *args, **kwargs):
            if inp.privileges.get(channel, -1) < level:
                return lex.denied
            return func(inp, *args, **kwargs)
        return inner
    return decorator


def crosschannel(func):
    @functools.wraps(func)
    def inner(inp, *args, channel, **kwargs):
        if channel:
            if channel not in inp.privileges:
                return lex.denied
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
