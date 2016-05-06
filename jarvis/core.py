#!/usr/bin/env python3

###############################################################################
# Module Imports
###############################################################################

import configparser
import funcy
import pyscp
import re

from . import ext, lexicon

###############################################################################
# Config and Cache
###############################################################################

config = configparser.ConfigParser()
config.read('jarvis.cfg')

wiki = pyscp.wikidot.Wiki('www.scp-wiki.net')
pages = None


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

    def __init__(self, text, user, channel, send):
        self.text = text.strip() if text else ''
        self.user = str(user).strip()
        self.channel = str(channel).strip()
        self._send = send

        self.private = False
        self.notice = False
        self.multiline = False

    def send(self, text):
        text = text if self.multiline else [text]
        for line in text:
            self._send(line, private=self.private, notice=self.notice)


EXPR = {
    'user': r'(?P<user>[\w\[\]{}^|-]+)',
    'topic': r'@?(?P<topic>[\w\[\]{}^|-]+)',
    'message': r'(?P<message>.*)',
    'index': r'(?P<index>\d+)',
    'date': r'(?P<date>\d{4}-\d{2}-\d{2})'}


@funcy.decorator
def command(call):
    """Enable generic command functionality."""
    result = call()
    if result:
        call._args[0].send(result)
    return result


@funcy.decorator
def parse_input(call, regex):
    """Parse input text and suppy necessary function arguments."""
    inp = call._args[0]
    regex = regex.format(**EXPR)
    match = re.match(regex, inp.text)
    if not match:
        if inp.text:
            return lexicon.input.incorrect
        doc = call._func.__doc__
        if doc:
            return doc.split('\n')[0] or doc.split('\n')[1]
        return lexicon.input.incorrect
    return call(**match.groupdict())


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
