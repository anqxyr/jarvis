#!/usr/bin/env python3

###############################################################################
# Module Imports
###############################################################################

import arrow
import peewee
import sopel
import re

import pyscp_bot.jarvis as vocab

###############################################################################

db = peewee.SqliteDatabase('jarvis.db')


class BaseModel(peewee.Model):

    class Meta:
        database = db


class Tell(BaseModel):
    sender = peewee.CharField()
    recipient = peewee.CharField()
    message = peewee.TextField()
    time = peewee.DateTimeField()


class Message(BaseModel):
    user = peewee.CharField()
    channel = peewee.CharField()
    time = peewee.CharField()
    text = peewee.TextField()

###############################################################################


def setup(bot):
    db.connect()
    Tell.create_table(True)
    Message.create_table(True)
    sopel.bot.Sopel._say = sopel.bot.Sopel.say
    sopel.bot.Sopel.say = log_and_say


@sopel.module.commands('tell')
@sopel.module.example('!tell anqxyr there is a bug in the bot.')
def tell(bot, trigger):
    """
    Send a message to the user.

    The message will be delivered the next time the user is active in any
    of the channels where the bot is present.
    """
    name, text = trigger.group(2).split(maxsplit=1)
    name = name.strip().lower()
    now = arrow.utcnow().timestamp
    Tell.create(
        sender=str(trigger.nick), recipient=name, message=text, time=now)
    bot.say(vocab.tell_stored(trigger.nick))


@sopel.module.thread(False)
@sopel.module.rule('.*')
@sopel.module.priority('low')
def chat_activity(bot, trigger):
    user = trigger.nick.strip()
    channel = trigger.sender
    time = arrow.utcnow().timestamp
    message = trigger.group(0)
    Message.create(user=user, channel=channel, time=time, text=message)
    if not re.match(r'[!\.](st|showt|showtells)$', trigger.group(0)):
        deliver_tells(bot, trigger.nick)


def log_and_say(bot, text, recipient, max_messages=1):
    if recipient in bot.config.core.channels:
        time = arrow.utcnow().timestamp
        Message.create(
            user=bot.config.core.nick, channel=recipient, time=time, text=text)
    bot._say(text, recipient, max_messages)


@sopel.module.commands('showtells', 'showt', 'st')
def showtells(bot, trigger):
    """
    Show messages sent to you by other users.

    IRC notice is issued in the channel stating the number of queued messages.
    This notice is visible only to the recipient of the messages.

    The tells themselves are delivered via irc private messages.
    """
    if Tell.select().where(Tell.recipient == trigger.nick.lower()).exists():
        deliver_tells(bot, trigger.nick)
    else:
        bot.notice(vocab.no_tells(trigger.nick), trigger.nick)


@sopel.module.commands('seen')
def seen(bot, trigger):
    """
    Check when the user was last seen.

    Results are channel specific. You must issue the command in the same
    channel where you want to check for the user.
    """
    name = trigger.group(2).strip().lower()
    channel = trigger.sender
    try:
        message = (
            Message.select()
            .where(
                peewee.fn.Lower(Message.user) == name,
                Message.channel == channel)
            .limit(1).order_by(Message.time.desc()).get())
        time = arrow.get(message.time).humanize()
        bot.say('{}: I saw {} {} saying "{}"'.format(
            trigger.nick, message.user, time, message.text))
    except Message.DoesNotExist:
        bot.say(vocab.user_never_seen(trigger.nick))


def deliver_tells(bot, name):
    query = Tell.select().where(Tell.recipient == name.lower())
    if not query.exists():
        return
    bot.notice(
        '{}: you have {} new messages.'.format(name, query.count()), name)
    for tell in query:
        time_passed = arrow.get(tell.time).humanize()
        msg = '{} said {}: {}'.format(tell.sender, time_passed, tell.message)
        bot.say(msg, name)
    Tell.delete().where(Tell.recipient == name.lower()).execute()
