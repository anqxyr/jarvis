#!/usr/bin/env python3

###############################################################################
# Module Imports
###############################################################################

import arrow
import peewee
import sopel
import re
import collections

import pyscp_bot.jarvis as vocab

###############################################################################

db = peewee.SqliteDatabase('notes.db')


class BaseModel(peewee.Model):

    class Meta:
        database = db


class Tell(BaseModel):
    sender = peewee.CharField()
    recipient = peewee.CharField(index=True)
    message = peewee.TextField()
    time = peewee.DateTimeField()


###############################################################################

MemTell = collections.namedtuple('MemTell', 'sender recipient message time')


def setup(bot):
    db.connect()
    Tell.create_table(True)
    bot.memory['tells'] = collections.defaultdict(list)
    for tell in Tell.select():
        memtell = MemTell(tell.sender, tell.recipient, tell.message, tell.time)
        bot.memory['tells'][tell.recipient].append(memtell)


@sopel.module.commands('tell')
def tell(bot, trigger):
    name, text = trigger.group(2).split(maxsplit=1)
    name = name.strip().lower()
    now = arrow.utcnow().format('YYYY-MM-DD hh:mm:ss')
    tell = MemTell(str(trigger.nick), name, text, now)
    Tell.create(**tell._asdict())
    bot.memory['tells'][name].append(tell)
    bot.say(vocab.tell_stored(trigger.nick))


@sopel.module.rule('.*')
def user_active(bot, trigger):
    if re.match(r'[!\.](st|showt|showtells)', trigger.group(0)):
        return  # avoid double dipping
    if trigger.nick.strip().lower() in bot.memory['tells']:
        deliver_tells(bot, trigger.nick)


@sopel.module.commands('st', 'showt', 'showtells')
def showtells(bot, trigger):
    print(bot.memory['tells'])
    print(trigger.nick.lower())
    if trigger.nick.lower() in bot.memory['tells']:
        deliver_tells(bot, trigger.nick)
    else:
        bot.notice(vocab.no_tells(trigger.nick), trigger.nick)


def deliver_tells(bot, name):
    for tell in bot.memory['tells'][name.lower()]:
        time_passed = arrow.get(tell.time).humanize()
        msg = '{} said {}: {}'.format(tell.sender, time_passed, tell.message)
        bot.notice(msg, name)
    del bot.memory['tells'][name.lower()]
    Tell.delete().where(Tell.recipient == name.lower()).execute()
