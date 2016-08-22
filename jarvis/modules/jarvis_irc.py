#!/usr/bin/env python3
"""
Jarvis IRC Wrapper.

This module connects jarvis functions to allow them to be called from irc.
"""


###############################################################################
# Module Imports
###############################################################################

import arrow
import functools
import sopel
import textwrap

import jarvis

###############################################################################


def send(bot, text, private=False, notice=False):
    """Send irc message."""
    tr = bot._trigger
    jarvis.notes.Message.create(
        user=bot.config.core.nick,
        channel=tr.sender,
        time=arrow.utcnow().timestamp,
        text=text)
    mode = 'NOTICE' if notice else 'PRIVMSG'
    recipient = tr.nick if private or notice else tr.sender
    try:
        bot.sending.acquire()
        for line in textwrap.wrap(text, width=420):
            bot.write((mode, recipient), line)
    finally:
        bot.sending.release()


def privileges(bot, nick):
    channels = bot.privileges.items()
    return {str(k): v[nick] for k, v in channels if nick in v}


@sopel.module.rule('.*')
def dispatcher(bot, tr):
    inp = jarvis.core.Inp(
        tr.group(0), tr.nick, tr.sender,
        functools.partial(send, bot),
        functools.partial(privileges, bot, tr.nick),
        bot.write)
    jarvis.core.dispatcher(inp)


@sopel.module.interval(3600)
def refresh(bot):
    jarvis.core.refresh()


@sopel.module.interval(28800)
def tweet(bot):
    jarvis.tools.tweet()


@sopel.module.event('JOIN')
@sopel.module.rule('.*')
def ban_on_join(bot, tr):
    inp = jarvis.core.Inp(
        None, tr.nick, tr.sender,
        functools.partial(send, bot),
        functools.partial(privileges, bot, tr.nick),
        bot.write)
    inp.send(jarvis.autoban.autoban(inp, tr.nick, tr.host))
