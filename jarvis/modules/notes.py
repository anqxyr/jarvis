#!/usr/bin/env python3

###############################################################################
# Module Imports
###############################################################################

import arrow
import sopel
import re

import jarvis

###############################################################################


def setup(bot):
    jarvis.db.db.connect()
    jarvis.db.Tell.create_table(True)
    jarvis.db.Message.create_table(True)
    sopel.bot.Sopel.SopelWrapper.send = send


def send(bot, text, private=False):
    tr = bot._trigger
    if tr.sender in bot.config.core.channels:
        text = '{}: {}'.format(tr.nick, text)
        time = arrow.utcnow().timestamp
        jarvis.db.Message.create(
            user=bot.config.core.nick, channel=tr.sender, time=time, text=text)
    bot.say(text, tr.nick if private else tr.sender)


###############################################################################


@sopel.module.commands('tell')
def tell(bot, tr):
    """
    Send a message to the user.

    The message will be delivered the next time the user is active in any
    of the channels where the bot is present.
    """
    name, text = tr.group(2).split(maxsplit=1)
    name = name.strip().lower()
    now = arrow.utcnow().timestamp
    jarvis.db.Tell.create(
        sender=str(tr.nick), recipient=name, message=text, time=now)
    bot.send(jarvis.lexicon.tell_stored())


@sopel.module.rule('.*')
@sopel.module.priority('low')
def chat_activity(bot, tr):
    user = tr.nick.strip()
    channel = tr.sender
    time = arrow.utcnow().timestamp
    message = tr.group(0)
    jarvis.db.Message.create(
        user=user, channel=channel, time=time, text=message)
    if not re.match(r'[!\.](st|showt|showtells)$', tr.group(0)):
        deliver_tells(bot, tr.nick)


@sopel.module.commands('showtells', 'showt', 'st')
def showtells(bot, tr):
    """
    Show messages sent to you by other users.

    IRC notice is issued in the channel stating the number of queued messages.
    This notice is visible only to the recipient of the messages.

    The tells themselves are delivered via irc private messages.
    """
    if jarvis.db.Tell.select().where(
            jarvis.db.Tell.recipient == tr.nick.lower()).exists():
        deliver_tells(bot, tr.nick)
    else:
        bot.notice(jarvis.lexicon.no_tells(), tr.nick)


@sopel.module.commands('seen')
def seen(bot, tr):
    """
    Check when the user was last seen.

    Results are channel specific. You must issue the command in the same
    channel where you want to check for the user.
    """
    name = tr.group(2).strip().lower()
    channel = tr.sender
    try:
        message = (
            jarvis.db.Message.select()
            .where(
                jarvis.db.peewee.fn.Lower(jarvis.db.Message.user) == name,
                jarvis.db.Message.channel == channel)
            .limit(1).order_by(jarvis.db.Message.time.desc()).get())
        time = arrow.get(message.time).humanize()
        bot.send('I saw {} {} saying "{}"'.format(
            message.user, time, message.text))
    except jarvis.db.Message.DoesNotExist:
        bot.send(jarvis.lexicon.user_never_seen())


def deliver_tells(bot, name):
    query = jarvis.db.Tell.select().where(
        jarvis.db.Tell.recipient == name.lower())
    if not query.exists():
        return
    bot.notice(
        '{}: you have {} new messages.'.format(name, query.count()), name)
    for tell in query:
        time_passed = arrow.get(tell.time).humanize()
        msg = '{} said {}: {}'.format(tell.sender, time_passed, tell.message)
        bot.send(msg, private=True)
    jarvis.db.Tell.delete().where(
        jarvis.db.Tell.recipient == name.lower()).execute()
