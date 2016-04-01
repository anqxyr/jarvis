#!/usr/bin/env python3

###############################################################################
# Module Imports
###############################################################################

import arrow
import sopel
import re

import pyscp_bot.jarvis as lexicon
import pyscp_bot.db as db

###############################################################################


def setup(bot):
    db.db.connect()
    db.Tell.create_table(True)
    db.Message.create_table(True)
    sopel.bot.Sopel.SopelWrapper.send = send


def send(bot, text, private=False):
    tr = bot._trigger
    if tr.sender in bot.config.core.channels:
        text = '{}: {}'.format(tr.nick, text)
        time = arrow.utcnow().timestamp
        db.Message.create(
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
    db.Tell.create(
        sender=str(tr.nick), recipient=name, message=text, time=now)
    bot.send(lexicon.tell_stored())


@sopel.module.rule('.*')
@sopel.module.priority('low')
def chat_activity(bot, tr):
    user = tr.nick.strip()
    channel = tr.sender
    time = arrow.utcnow().timestamp
    message = tr.group(0)
    db.Message.create(user=user, channel=channel, time=time, text=message)
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
    if db.Tell.select().where(
            db.Tell.recipient == tr.nick.lower()).exists():
        deliver_tells(bot, tr.nick)
    else:
        bot.notice(lexicon.no_tells(), tr.nick)


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
            db.Message.select()
            .where(
                db.peewee.fn.Lower(db.Message.user) == name,
                db.Message.channel == channel)
            .limit(1).order_by(db.Message.time.desc()).get())
        time = arrow.get(message.time).humanize()
        bot.send('I saw {} {} saying "{}"'.format(
            message.user, time, message.text))
    except db.Message.DoesNotExist:
        bot.send(lexicon.user_never_seen())


def deliver_tells(bot, name):
    query = db.Tell.select().where(db.Tell.recipient == name.lower())
    if not query.exists():
        return
    bot.notice(
        '{}: you have {} new messages.'.format(name, query.count()), name)
    for tell in query:
        time_passed = arrow.get(tell.time).humanize()
        msg = '{} said {}: {}'.format(tell.sender, time_passed, tell.message)
        bot.send(msg, private=True)
    db.Tell.delete().where(db.Tell.recipient == name.lower()).execute()
