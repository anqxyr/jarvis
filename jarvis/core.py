#!/usr/bin/env python3

###############################################################################
# Module Imports
###############################################################################

import collections
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


Inp = collections.namedtuple('Inp', 'text user channel send')


EXPR = {
    'user': r'(?P<user>[\w\[\]{}^|-]+)',
    'topic': r'@?(?P<topic>[\w\[\]{}^|-]+)',
    'message': r'(?P<message>.*)',
    'index': r'(?P<index>\d+)'}


@funcy.decorator
def command(call):
    """Enable generic command functionality."""
    text = call.inp.text.strip()
    user = str(call.inp.user).strip()
    channel = str(call.inp.channel).strip()
    inp = Inp(text, user, channel, call.inp.send)
    call._args[0] = inp
    result = call()
    if result:
        call.inp.send(result)
    return result


@funcy.decorator
def parse_input(call, regex):
    """Parse input text and suppy necessary function arguments."""
    regex = regex.format(**EXPR)
    match = re.match(regex, call.inp.text)
    if not match:
        if call.inp.text:
            return lexicon.input.incorrect
        doc = call.__func__.__doc__
        if doc:
            return doc.split('\n')[0] or doc.split('\n')[1]
        return lexicon.input.incorrect
    return call(**match.groupdict())


@funcy.decorator
def lower_input(call):
    """Turn input into lowercase."""
    user = call.inp.user.lower()
    text = call.inp.text.lower()
    call._args[0] = call._args[0]._replace(user=user, text=text)
    return call()


@funcy.decorator
def private(call):
    send = funcy.partial(call.inp.send, private=True)
    call._args[0] = call._args[0]._replace(send=send)
    return call()


@funcy.decorator
def notice(call):
    send = funcy.partial(call.inp.send, notice=True)
    call._args[0] = call._args[0]._replace(send=send)
    return call()


@funcy.decorator
def multiline(call):

    def send(text, **kwargs):
        for line in text:
            call.inp.send(line)

    call._args[0] = call._args[0]._replace(send=send)
    return call()
