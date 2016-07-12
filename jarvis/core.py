#!/usr/bin/env python3

###############################################################################
# Module Imports
###############################################################################

import configparser
import functools
import pyscp
import logbook

from . import ext, lex

###############################################################################
# Logging
###############################################################################

logbook.FileHandler('jarvis.log').push_application()
log = logbook.Logger(__name__)

###############################################################################
# Config and Cache
###############################################################################

config = configparser.ConfigParser()
config.read('jarvis.cfg')

wiki = pyscp.wikidot.Wiki('www.scp-wiki.net')
wlwiki = pyscp.wikidot.Wiki('wanderers-library')


def refresh():
    global pages
    global wlpages
    kwargs = dict(body='title created_by created_at rating tags', category='*')
    if config['wiki'].getboolean('debug'):
        pyscp.utils.default_logging(True)
        data = wiki._list_pages_parsed(author='anqxyr', **kwargs)
    else:
        data = wiki.list_pages(**kwargs)
    pages = ext.PageView(data)
    wiki.titles.cache_clear()
    wiki.metadata.cache_clear()

    if not config['wiki'].getboolean('debug'):
        wlpages = ext.PageView(wlwiki.list_pages(**kwargs))


refresh()

###############################################################################
# Command Decorators
###############################################################################


class Inp:
    """Wrap input data."""

    def __init__(self, text, user, channel, send, privileges):
        """Clean input values."""
        self.text = text.strip() if text else ''
        self.user = str(user).strip()
        self.channel = str(channel).strip()
        self._send = send
        self._priv = privileges

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
        log.info('{}: {}'.format(inp.user, inp.text))
        try:
            result = func(inp, *args, **kwargs)
            if result:
                inp.send(result)
        except Exception as e:
            log.exception(e)
            inp.send(lex.error)
    return inner


def private(func):
    @functools.wraps(func)
    def inner(inp, *args, **kwargs):
        inp.private = True
        return func(inp, *args, **kwargs)
    return inner


def notice(func):
    @functools.wraps(func)
    def inner(inp, *args, **kwargs):
        inp.notice = True
        return func(inp, *args, **kwargs)
    return inner


def multiline(func):
    @functools.wraps(func)
    def inner(inp, *args, **kwargs):
        inp.multiline = True
        return func(inp, *args, **kwargs)
    return inner
