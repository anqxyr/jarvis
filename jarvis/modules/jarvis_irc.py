#!/usr/bin/env python3
"""
Jarvis IRC Wrapper.

This module contains irc-specific functionality such as autocomplete, and
connects jarvis functions to allow them to be called from irc.
"""


###############################################################################
# Module Imports
###############################################################################

import functools
import sopel

from jarvis import core, notes, scp, websearch, tools

###############################################################################
# Core Wrapper Functions
###############################################################################


@sopel.module.commands('\w+')
def autocomplete(bot, tr):
    """Automatically complete partially entered commands."""
    funcs = [f for group in bot._callables.values() for f in group.values()]
    funcs = {f for l in funcs for f in l if hasattr(f, 'commands')}
    partial = tr.group(1)
    if any(partial in f.commands for f in funcs):
        return
    funcs = [
        f for f in funcs if any(c.startswith(partial) for c in f.commands)]
    if not funcs:
        return
    if len(funcs) > 1:
        send(bot, tools.choose_input([f.commands[0] for f in funcs]))
    else:
        wrapper = bot.SopelWrapper(bot, tr)
        bot.call(funcs[0], wrapper, tr)


def send(bot, text, private=False, notice=False):
    """Send irc message."""
    tr = bot._trigger
    mode = 'NOTICE' if notice else 'PRIVMSG'
    recipient = tr.nick if private or notice else tr.sender
    text = text[:400]
    try:
        bot.sending.acquire()
        bot.write((mode, recipient), text)
    finally:
        bot.sending.release()


def wrapper(fn, group, *args, **kwargs):

    def inner(bot, tr):
        inp = core.Inp(
            tr.group(group), tr.nick, tr.sender, functools.partial(send, bot))
        return fn(inp, *args, **kwargs)
    return inner


def command(trigger, fn, *args, **kwargs):
    globals()[fn.__name__] = sopel.module.commands(
        *trigger.split())(wrapper(fn, 2, *args, **kwargs))


def rule(trigger, fn, *args, priority='medium', **kwargs):
    inner = wrapper(fn, 1, *args, **kwargs)
    for tr in trigger:
        inner = sopel.module.rule(tr)(inner)
    inner = sopel.module.priority(priority)(inner)
    globals()[fn.__name__] = inner


###############################################################################
# Notes
###############################################################################


command('tell', notes.tell)
command('outbound', notes.outbound)
command('seen', notes.seen)
command('quote', notes.quote)
command('remember', notes.save_memo)
command('topic', notes.topic)
command('alert', notes.alert)

rule(['(.*)'], notes.logevent, priority='low')
rule(['(.*)'], notes.get_tells, priority='low')
rule([r'(\?[\w\[\]{}^|-]+)$'], notes.load_memo)


###############################################################################
# SCP
###############################################################################


command('search s', scp.search)
command('tale', scp.tale)
command('tags', scp.tags)
command('wandererslibrary wl', scp.wanderers_library)
command('author', scp.author)
command('ad', scp.author_details)
command('lastcreated lc', scp.last_created)
command('random', scp.random_page)
command('errors', scp.errors)

rule([
    r'(?i).*http[s]?://www\.scp-wiki\.net/([^/]+)',
    r'(?i)^(scp-[\d]+(?:-[\w]+)?)$',
    r'(?i).*!(scp-\d+(?:-[\w]+)?)'], scp.name_lookup)


###############################################################################
# Tools
###############################################################################


command('showmore sm', tools.showmore)
command('choose', tools.choose)
command('roll dice', tools.roll_dice)


###############################################################################
# Websearch
###############################################################################


command('google g', websearch.google_search)
command('gis', websearch.google_image_search)
command('youtube yt', websearch.youtube)
command('wikipedia', websearch.wikipedia)
command('definition define dictionary', websearch.dictionary)
command('urbandictionary', websearch.urbandictionary)

rule([
    r'.*youtube\.com/watch\?v=([-_a-z0-9]+)',
    r'.*youtu\.be/([-_a-z0-9]+)'], websearch.youtube_lookup)
