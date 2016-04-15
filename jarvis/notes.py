#!/usr/bin/env python3

###############################################################################
# Module Imports
###############################################################################

import arrow
import random
import re
from peewee import fn
from playhouse import migrate
import peewee

from . import db, tools, lexicon

###############################################################################


def init():
    db.db.connect()
    db.Tell.create_table(True)
    db.Message.create_table(True)
    db.Quote.create_table(True)
    db.Rem.create_table(True)

    try:
        migrator = migrate.SqliteMigrator(db.db)
        migrate.migrate(
            migrator.add_column('Tell', 'topic', peewee.CharField(null=True)),
            migrator.rename_column('Tell', 'message', 'text'))
    except:
        pass


def log_message(user, channel, text):
    db.Message.create(
        user=user.strip(), channel=channel,
        time=arrow.utcnow().timestamp, text=text)


def send_tell(sender, recipient, text):
    recipient = recipient.strip().lower()
    sender = str(sender)
    time = arrow.utcnow().timestamp
    if not re.match(r'^@?[\w\[\]{}^]+$', recipient):
        return lexicon.bad_input
    if not recipient.startswith('@'):
        db.Tell.create(
            sender=sender, recipient=recipient,
            text=text, time=time, topic=None)
        return lexicon.tell.send
    else:
        users = db.Subscriber.select().where(db.Subscriber.topic == recipient)
        users = [i.user for i in users]
        if not users:
            return lexicon.topic.no_subscribers
        db.Tell.insert_many(dict(
            sender=sender, recipient=user, text=text,
            time=time, topic=recipient) for user in users)
        return lexicon.topic.send.format(count=len(users))


def get_tells(user):
    user = user.strip().lower()
    query = db.Tell.select().where(db.Tell.recipient == user)
    for tell in query.execute():
        time = arrow.get(tell.time).humanize()
        if not tell.topic:
            yield '{} said {}: {}'.format(tell.sender, time, tell.text)
        else:
            yield '{} said {} via {}: {}'.format(
                tell.sender, time, tell.topic, tell.text)
        tell.delete_instance()


def get_stored_tells_count(user):
    user = user.strip().lower()
    query = db.Tell.select().where(
        fn.Lower(db.Tell.sender) == user, db.Tell.topic.is_null())
    if not query.exists():
        return lexicon.tell.storage_empty
    users = ', '.join(sorted({i.recipient for i in query}))
    return lexicon.tell.storage_count.format(total=query.count(), users=users)


def purge_stored_tells(user):
    user = user.strip().lower()
    query = db.Tell.select().where(
        fn.Lower(db.Tell.sender) == user, db.Tell.topic.is_null())
    if not query.exists():
        return lexicon.tell.storage_empty
    count = query.count()
    db.Tell.delete().where(fn.Lower(db.Tell.sender) == user).execute()
    return lexicon.tell.storage_purged.format(count=count)


def get_user_seen(user, channel):
    user = user.strip().lower()
    query = db.Message.select().where(
        fn.Lower(db.Message.user) == user,
        db.Message.channel == channel).order_by(db.Message.time.desc())
    try:
        msg = query.get()
    except db.Message.DoesNotExist:
        return lexicon.seen.never
    time = arrow.get(msg.time).humanize()
    return lexicon.seen.last.format(user=msg.user, time=time, text=msg.text)


def dispatch_quote(inp, channel):
    inp = inp.strip() if inp else ''
    parsed = re.match(r'^ *[0-9]* *$', inp)
    if parsed:
        return get_quote(None, channel, parsed.group(0).strip())
    parsed = re.match(
        r'^(add|del)? ?(\d{4}-\d{2}-\d{2})? ?([\w\d<>^{}[\]\\-]+)(.*)$', inp)
    if not parsed:
        return lexicon.bad_input
    cmd, time, name, text = parsed.groups()
    text = text.strip()
    channel = str(channel).strip()
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
        return lexicon.quote.already_exists
    if not time:
        time = arrow.utcnow().format('YYYY-MM-DD')
    db.Quote.create(user=user, channel=channel, time=time, text=text)
    return lexicon.quote.saved


def get_quote(user, channel, index=None):
    query = db.Quote.select().where(db.Quote.channel == channel)
    if user:
        user = user.strip().lower()
        query = query.where(db.Quote.user == user)
    if not query.exists():
        return lexicon.quote.none_saved
    if not index:
        index = random.randint(1, query.count())
    else:
        try:
            index = int(index)
        except ValueError:
            return lexicon.bad_index
        if index not in range(1, query.count() + 1):
            return lexicon.bad_index
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
        return lexicon.quote.not_found
    query.get().delete_instance()
    return lexicon.quote.deleted


def remember_user(inp, channel):
    user, text = inp.split(maxsplit=1)
    user = user.strip().lower()
    text = text.strip()
    db.Rem.delete().where(
        db.Rem.user == user, db.Rem.channel == channel).execute()
    db.Rem.create(user=user, channel=channel, text=text)
    return lexicon.quote.saved


def recall_user(user, channel):
    user = user.strip().lower()
    try:
        rem = db.Rem.select().where(
            db.Rem.user == user, db.Rem.channel == channel).get()
    except db.Rem.DoesNotExist:
        return lexicon.not_found
    return rem.text
