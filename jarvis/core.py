#!/usr/bin/env python3

###############################################################################
# Module Imports
###############################################################################

import configparser
import funcy
import functools
import pyscp

from . import ext

###############################################################################
# Config and Cache
###############################################################################

config = configparser.ConfigParser()
config.read('jarvis.cfg')

wiki = pyscp.wikidot.Wiki('www.scp-wiki.net')


def refresh():
    kwargs = dict(body='title created_by created_at rating tags', category='*')
    if config['wiki'].getboolean('debug'):
        pyscp.utils.default_logging(True)
        data = wiki._list_pages_parsed(author='anqxyr', **kwargs)
    else:
        data = wiki.list_pages(**kwargs)
    global pages
    pages = ext.PageView(data)
    wiki.titles.cache_clear()
    wiki.metadata.cache_clear()


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


@funcy.decorator
def lower_input(call):
    """Turn input into lowercase."""
    inp = call._args[0]
    inp.user = inp.user.lower()
    inp.text = inp.text.lower()
    return call()


@funcy.decorator
def private(call):
    call._args[0].private = True
    return call()


@funcy.decorator
def notice(call):
    call._args[0].notice = True
    return call()


@funcy.decorator
def multiline(call):
    call._args[0].multiline = True
    return call()
