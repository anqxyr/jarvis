#!/usr/bin/env python3

###############################################################################
# Module Imports
###############################################################################

import functools
import logbook
import pyscp
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
# Command Decorators
###############################################################################


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

        self.private = False
        self.notice = False
        self.multiline = False

    def send(self, text):
        """Send output data."""
        text = text if self.multiline else [text]
        for line in text:
            if hasattr(line, 'compose'):
                line = line.compose(self)
            if self.user != self.channel and not (self.notice or self.private):
                line = '{}: {}'.format(self.user, line)
            self._send(line, private=self.private, notice=self.notice)

    @property
    def privileges(self):
        return self._priv()


def command(func):
    """Enable generic command functionality."""
    @functools.wraps(func)
    def inner(inp, *args, **kwargs):
        try:
            result = func(inp, *args, **kwargs)
            if result:
                inp.send(result)
        except Exception as e:
            log.exception(e)
            inp._send(lex.error.compose(inp), private=False, notice=False)
    return inner


def require(channel=None, level=0):
    def decorator(func):
        @functools.wraps(func)
        def inner(inp, *args, **kwargs):
            ch = channel or inp.channel
            if inp.privileges.get(ch, -1) < level:
                return lex.denied
            return func(inp, *args, **kwargs)
        return inner
    return decorator


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
