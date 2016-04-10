#!/usr/bin/env python3

###############################################################################
# Module Imports
###############################################################################

import arrow
import random
import re

from . import db, tools, lexicon

###############################################################################


def init():
    db.db.connect()
    db.Tell.create_table(True)
    db.Message.create_table(True)
    db.Quote.create_table(True)
    db.Rem.create_table(True)


def log_message(user, channel, text):
    db.Message.create(
        user=user.strip(), channel=channel,
        time=arrow.utcnow().timestamp, text=text)


def store_tell(sender, recipient, text):
    recipient = recipient.strip().lower()
    db.Tell.create(
        sender=str(sender), recipient=recipient,
        message=text, time=arrow.utcnow().timestamp)
    return lexicon.tell_stored()


def get_tells(user):
    user = user.strip().lower()
    query = db.Tell.select().where(db.Tell.recipient == user)
    for tell in query.execute():
        time = arrow.get(tell.time).humanize()
        yield '{} said {}: {}'.format(tell.sender, time, tell.message)
        tell.delete_instance()


def get_notdelivered_count(user):
    user = user.strip().lower()
    query = db.Tell.select().where(db.peewee.fn.Lower(db.Tell.sender) == user)
    if not query.exists():
        return lexicon.all_tells_delivered()
    users = sorted({i.recipient for i in query})
    return lexicon.undelivered_tells(query.count(), users)


def user_last_seen(user, channel):
    user = user.strip().lower()
    query = db.Message.select().where(
        db.peewee.fn.Lower(db.Message.user) == user,
        db.Message.channel == channel).order_by(db.Message.time.desc())
    try:
        msg = query.get()
    except db.Message.DoesNotExist:
        return lexicon.user_never_seen()
    time = arrow.get(msg.time).humanize()
    return 'I saw {} {} saying: {}'.format(msg.user, time, msg.text)


def quote(inp, channel):
    inp = inp.strip() if inp else ''
    parsed = re.match(r'^ *[0-9]* *$', inp)
    if parsed:
        return get_quote(None, channel, parsed.group(0).strip())
    parsed = re.match(
        r'^(add|del)? ?(\d{4}-\d{2}-\d{2})? ?([\w\d<>^{}[\]\\-]+)(.*)$', inp)
    if not parsed:
        return lexicon.not_found()
    cmd, time, name, text = parsed.groups()
    text = text.strip()
    channel = str(channel)
    if cmd == 'add':
        return add_quote(name, channel, text, time)
    if cmd == 'del':
        return delete_quote(name, channel, text)
    if name == channel:
        name = None
    return get_quote(name, channel, text)


def add_quote(user, channel, text, time=None):
    user = user.strip().lower()
    if db.Quote.select().where(
            db.Quote.user == user,
            db.Quote.channel == channel, db.Quote.text == text).exists():
        return lexicon.quote_exists()
    if not time:
        time = arrow.utcnow().format('YYYY-MM-DD')
    db.Quote.create(user=user, channel=channel, time=time, text=text)
    return lexicon.quote_added()


def get_quote(user, channel, index=None):
    query = db.Quote.select().where(db.Quote.channel == channel)
    if user:
        user = user.strip().lower()
        query = query.where(db.Quote.user == user)
    if not query.exists():
        return lexicon.no_quotes()
    if not index:
        index = random.randint(1, query.count())
    else:
        try:
            index = int(index)
        except ValueError:
            return lexicon.bad_index()
        if index not in range(1, query.count() + 1):
            return lexicon.bad_index()
    quote = list(query.order_by(db.Quote.id))[int(index) - 1]
    return '[{}/{}] {} {}: {}'.format(
        index, query.count(), quote.time, quote.user, quote.text)


def delete_quote(user, channel, text):
    user = user.strip().lower()
    query = db.Quote.select().where(
        db.Quote.user == user,
        db.Quote.channel == channel,
        db.Quote.text == text)
    if not query.exists():
        return lexicon.quote_not_found()
    query.get().delete_instance()
    return lexicon.quote_deleted()


def add_rem(inp, channel):
    user, text = inp.split(maxsplit=1)
    user = user.strip().lower()
    text = text.strip()
    db.Rem.delete().where(
        db.Rem.user == user, db.Rem.channel == channel).execute()
    db.Rem.create(user=user, channel=channel, text=text)
    return lexicon.quote_added()


def get_rem(user, channel):
    user = user.strip().lower()
    try:
        rem = db.Rem.select().where(
            db.Rem.user == user, db.Rem.channel == channel).get()
    except db.Rem.DoesNotExist:
        return lexicon.not_found()
    return rem.text
