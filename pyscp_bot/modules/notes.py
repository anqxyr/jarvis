#!/usr/bin/env python3

###############################################################################
# Module Imports
###############################################################################

import arrow
import peewee
import sopel
import re

from pyscp_bot import snark

###############################################################################

db = peewee.SqliteDatabase('notes.db')


class BaseModel(peewee.Model):

    class Meta:
        database = db


class Tell(BaseModel):
    sender = peewee.CharField()
    recipient = peewee.CharField(index=True)
    text = peewee.TextField()
    time = peewee.DateTimeField()


###############################################################################


def setup(bot):
    db.connect()
    Tell.create_table(True)
    bot._tells_recipients = {
        i.recipient for i in
        Tell.select(Tell.recipient).distinct(Tell.recipient)}


@sopel.module.commands('tell')
def tell(bot, trigger):
    name, text = trigger.group(2).split(maxsplit=1)
    now = arrow.now().format('YYYY-MM-DD hh:mm:ss')
    Tell.create(sender=trigger.nick, recipient=name, text=text, time=now)
    bot._tells_recipients.add(name)
    bot.say(snark.tell_stored(trigger.nick))


@sopel.module.rule('.*')
def user_active(bot, trigger):
    if re.match(r'[!\.](st|showt|showtells)', trigger.group(0)):
        return
    if trigger.nick in bot._tells_recipients:
        deliver_tells(bot, trigger.nick)


@sopel.module.commands('st', 'showt', 'showtells')
def showtells(bot, trigger):
    if trigger.nick in bot._tells_recipients:
        deliver_tells(bot, trigger.nick)
    else:
        bot.notice(snark.no_tells(trigger.nick), trigger.nick)


def deliver_tells(bot, name):
    tells = Tell.select().where(Tell.recipient == name)
    for tell in tells:
        time_passed = arrow.get(tell.time).humanize()
        msg = '{} said {}: {}'.format(tell.sender, time_passed, tell.text)
        bot.notice(msg, name)
    Tell.delete().where(Tell.recipient == name).execute()
    bot._tells_recipients -= {name}
