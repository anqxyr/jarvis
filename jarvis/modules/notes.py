#!/usr/bin/env python3

###############################################################################
# Module Imports
###############################################################################

import sopel
import jarvis

###############################################################################


def setup(bot):
    jarvis.notes.init()
    sopel.bot.Sopel.SopelWrapper.send = send


def send(bot, text, private=False, force=False):
    tr = bot._trigger
    if tr.sender in bot.config.core.channels:
        text = '{}: {}'.format(tr.nick, text)
        jarvis.notes.log_message(bot.config.core.nick, tr.sender, text)

    def say(text, recipient):
        lines = [text[i:i + 400] for i in range(0, len(text), 400)]
        try:
            bot.sending.acquire()
            for line in lines:
                bot.write(('PRIVMSG', recipient), line)
        finally:
            bot.sending.release()

    (say if force else bot.say)(text, tr.nick if private else tr.sender)


###############################################################################


@sopel.module.rule('.*')
@sopel.module.priority('low')
def chat_activity(bot, tr):
    jarvis.notes.log_message(tr.nick, tr.sender, tr.group(0))
    tells = list(jarvis.notes.get_tells(tr.nick))
    if tells:
        bot.notice('You have {} new messages'.format(len(tells)), tr.nick)
    for t in tells:
        bot.send(t, private=True, force=True)


@sopel.module.commands('tell')
def tell(bot, tr):
    """
    Send a message to the user.

    The message will be delivered the next time the user is active in any
    of the channels where the bot is present.
    """
    bot.send(jarvis.notes.store_tell(tr.nick, *tr.group(2).split(maxsplit=1)))


@sopel.module.commands('showtells', 'showt', 'st')
def showtells(bot, tr):
    """
    Show messages sent to you by other users.

    IRC notice is issued in the channel stating the number of queued messages.
    This notice is visible only to the recipient of the messages.

    The tells themselves are delivered via irc private messages.
    """
    tells = list(jarvis.notes.get_tells(tr.nick))
    if not tells:
        bot.notice(jarvis.lexicon.no_tells(), tr.nick)
    else:
        bot.notice('You have {} new messages'.format(len(tells)), tr.nick)
        for t in tells:
            bot.send(t, private=True, force=True)


@sopel.module.commands('notdelivered', 'nd')
def notdelivered(bot, tr):
    bot.notice(jarvis.notes.get_notdelivered_count(tr.nick), tr.nick)


@sopel.module.commands('seen')
def seen(bot, tr):
    """
    Check when the user was last seen.

    Results are channel specific. You must issue the command in the same
    channel where you want to check for the user.
    """
    bot.send(jarvis.notes.user_last_seen(tr.group(2), tr.sender))


def channel_quotes_enabled(bot, tr):
    sssc = bot.channels.get(bot.config.scp.sssc)
    if tr.sender in bot.config.scp.quotes:
        return tr.sender
    elif sssc and tr.sender in sssc.users:
        return sssc.name
    else:
        return


@sopel.module.require_admin(message='Nope')
@sopel.module.commands('qw')
def qw(bot, tr):
    with open('quotes.txt') as file:
        quotes = [i for i in file]
    for q in quotes:
        jarvis.notes.quote(q, bot.config.scp.sssc)
    bot.send('FINISHED ADDING {}'.format(len(quotes)))


@sopel.module.commands('quote', 'q')
def quote(bot, tr):
    channel = channel_quotes_enabled(bot, tr)
    if channel:
        bot.send(jarvis.notes.quote(tr.group(2), channel))


@sopel.module.commands('rem')
def rem(bot, tr):
    channel = channel_quotes_enabled(bot, tr)
    if channel:
        bot.send(jarvis.notes.add_rem(tr.group(2), channel))


@sopel.module.rule(r'^\?([\w\d-]+)$')
def get_rem(bot, tr):
    channel = channel_quotes_enabled(bot, tr)
    if channel:
        bot.send(jarvis.notes.get_rem(tr.group(1), channel))
