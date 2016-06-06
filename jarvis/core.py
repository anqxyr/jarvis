#!/usr/bin/env python3

###############################################################################
# Module Imports
###############################################################################

import configparser
import functools
import pyscp

from . import ext

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

    def __init__(self, text, user, channel, send):
        """Clean input values."""
        self.text = text.strip() if text else ''
        self.user = str(user).strip()
        self.channel = str(channel).strip()
        self._send = send

        self.private = False
        self.notice = False
        self.multiline = False

    def send(self, text):
        """Send output data."""
        text = text if self.multiline else [text]
        for line in text:
            if self.user != self.channel and not (self.notice or self.private):
                line = '{}: {}'.format(self.user, line)
            self._send(line, private=self.private, notice=self.notice)


def command(func):
    """Enable generic command functionality."""
    @functools.wraps(func)
    def inner(inp, *args, **kwargs):
        result = func(inp, *args, **kwargs)
        if result:
            inp.send(result)
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
