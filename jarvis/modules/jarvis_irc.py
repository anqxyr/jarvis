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

from jarvis import core, notes, scp, tools

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
        bot.send(tools.choose_input([f.commands[0] for f in funcs]))
    else:
        wrapper = bot.SopelWrapper(bot, tr)
        bot.call(funcs[0], wrapper, tr)


def send(bot, text, private=False, notice=False):
    """Send irc message."""
    tr = bot._trigger
    if tr.sender in bot.config.core.channels:
        text = '{}: {}'.format(tr.nick, text)
    mode = 'NOTICE' if notice else 'PRIVMSG'
    recipient = tr.nick if private or notice else tr.sender
    text = text[:400]
    try:
        bot.sending.acquire()
        bot.write((mode, recipient), text)
    finally:
        bot.sending.release()


def register(trtype, group, trigger, fn, *args, priority='medium', **kwargs):
    """Register new callable."""
    @trtype(*trigger.split())
    @sopel.module.priority(priority)
    def inner(bot, tr):
        inp = core.Inp(
            tr.group(group), tr.nick, tr.sender, functools.partial(send, bot))
        return fn(inp, *args, **kwargs)
    globals()[fn.__name__] = inner

command = functools.partial(register, sopel.module.commands, 2)
rule = functools.partial(register, sopel.module.rule, 1)


###############################################################################
# Notes
###############################################################################


command('tell', notes.send_tell)
command('outboundtells', notes.outbound_tells)
command('seen', notes.get_user_seen)
command('quote', notes.dispatch_quote)
command('remember', notes.remember_user)
command('subscribe', notes.subscribe_to_topic)
command('unsubscribe', notes.unsubscribe_from_topic)
command('topics', notes.get_topics_count)
command('restrict', notes.restrict_topic)
command('unrestrict', notes.unrestrict_topic)
command('alert', notes.set_alert)

rule('(.*)', notes.logevent, priority='low')
rule('(.*)', notes.get_tells, priority='low')
rule(r'(\?[\w\[\]{}^|-]+)$', notes.recall_user)


###############################################################################
# SCP
###############################################################################


command('search s', scp.find_page_by_title)
command('tale', scp.find_tale_by_title)
command('tags', scp.find_page_by_tags)
command('author', scp.author)
command('ad', scp.author_details)
command('author', scp.author)
command('lastcreated lc', scp.last_created)
command('random', scp.get_random_page)
command('errors', scp.get_error_report)

rule(r'(?i).*http[s]?://www\.scp-wiki\.net/([^/]+)', scp.find_page_by_url)
rule(r'(?i)^(scp-[\d]+(?:-[\w]+)?)$', scp.find_page_by_url)
rule(r'(?i).*!(scp-\d+(?:-[\w]+)?)', scp.find_page_by_url)

###############################################################################
