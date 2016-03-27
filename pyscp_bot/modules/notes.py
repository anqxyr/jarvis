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

db = peewee.SqliteDatabase('notes.db')


class BaseModel(peewee.Model):

    class Meta:
        database = db


class Tell(BaseModel):
    sender = peewee.CharField()
    recipient = peewee.CharField()
    message = peewee.TextField()
    time = peewee.DateTimeField()


class Seen(BaseModel):
    user = peewee.CharField()
    channel = peewee.CharField()
    time = peewee.CharField()
    message = peewee.TextField()


###############################################################################

def setup(bot):
    db.connect()
    Tell.create_table(True)
    Seen.create_table(True)


@sopel.module.commands('tell')
def tell(bot, trigger):
    name, text = trigger.group(2).split(maxsplit=1)
    name = name.strip().lower()
    now = arrow.utcnow().timestamp
    Tell.create(
        sender=str(trigger.nick), recipient=name, message=text, time=now)
    bot.say(vocab.tell_stored(trigger.nick))


@sopel.module.rule('.*')
def update_seen(bot, trigger):
    user = trigger.nick.lower()
    channel = trigger.sender
    time = arrow.utcnow().timestamp
    message = trigger.group(0)
    try:
        Seen.get(Seen.user == user, Seen.channel == channel).delete_instance()
    except Seen.DoesNotExist:
        pass
    Seen.create(user=user, channel=channel, time=time, message=message)


@sopel.module.rule('.*')
def showtells_on_activity(bot, trigger):
    if re.match(r'[!\.](st|showt|showtells)', trigger.group(0)):
        return  # avoid double dipping
    name = trigger.nick.strip().lower()
    if Tell.select().where(Tell.recipient == name).exists():
        deliver_tells(bot, trigger.nick)


@sopel.module.commands('showtells', 'showt', 'st')
def showtells(bot, trigger):
    if Tell.select().where(Tell.recipient == trigger.nick.lower()).exists():
        deliver_tells(bot, trigger.nick)
    else:
        bot.notice(vocab.no_tells(trigger.nick), trigger.nick)


@sopel.module.commands('seen')
def seen(bot, trigger):
    name = trigger.group(2).strip().lower()
    channel = trigger.sender
    try:
        seen = Seen.get(Seen.user == name, Seen.channel == channel)
        time = arrow.get(seen.time).humanize()
        bot.say('{}: I saw {} {} saying "{}"'.format(
            trigger.nick, seen.user, time, seen.message))
    except Seen.DoesNotExist:
        bot.say(vocab.user_never_seen(trigger.nick))


def deliver_tells(bot, name):
    for tell in Tell.select().where(Tell.recipient == name.lower()):
        time_passed = arrow.get(tell.time).humanize()
        msg = '{} said {}: {}'.format(tell.sender, time_passed, tell.message)
        bot.notice(msg, name)
    Tell.delete().where(Tell.recipient == name.lower()).execute()
