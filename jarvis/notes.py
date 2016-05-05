#!/usr/bin/env python3

###############################################################################
# Module Imports
###############################################################################

import arrow
import random
import re
import peewee
import playhouse.sqlite_ext

from . import core, lexicon


###############################################################################
# Database ORM Classes
###############################################################################


db = playhouse.sqlite_ext.SqliteExtDatabase('jarvis.db', journal_mode='WAL')


class BaseModel(peewee.Model):

    class Meta:
        database = db


class Tell(BaseModel):
    sender = peewee.CharField()
    recipient = peewee.CharField(index=True)
    topic = peewee.CharField(null=True)
    text = peewee.TextField()
    time = peewee.DateTimeField()


class Message(BaseModel):
    user = peewee.CharField(index=True)
    channel = peewee.CharField()
    time = peewee.CharField()
    text = peewee.TextField()


class Quote(BaseModel):
    user = peewee.CharField(index=True)
    channel = peewee.CharField()
    time = peewee.CharField()
    text = peewee.TextField()


class Rem(BaseModel):
    user = peewee.CharField(index=True)
    channel = peewee.CharField()
    text = peewee.TextField()


class Subscriber(BaseModel):
    user = peewee.CharField()
    topic = peewee.CharField(index=True)


class Restricted(BaseModel):
    topic = peewee.CharField(index=True)


class Alert(BaseModel):
    user = peewee.CharField(index=True)
    time = peewee.DateTimeField()
    text = peewee.TextField()

###############################################################################


def init():
    db.connect()
    db.create_tables(
        [Tell, Message, Quote, Rem, Subscriber, Restricted, Alert], safe=True)


def logevent(inp):
    Message.create(
        user=inp._user, channel=inp._channel,
        time=arrow.utcnow().timestamp, text=inp._text)


###############################################################################
# Tells
###############################################################################


@core.command
@core.parse_input(r'(?P<topic>@)?{name}[:,]? {text}')
def send_tell(inp):

    if inp.topic:
        users = Subscriber.select().where(Subscriber.topic == inp.name)
        users = [i.user for i in users]
        if not users:
            return lexicon.topic.no_subscribers
    else:
        users = [inp.name]

    data = dict(
        sender=inp._user,
        text=inp.text,
        time=arrow.utcnow().timestamp,
        topic=bool(inp.topic))
    Tell.insert_many(dict(recipient=i, **data) for i in users)

    if inp.topic:
        return lexicon.topic.send.format(count=len(users))
    else:
        return lexicon.tell.send


@core.command
@core.private
@core.multiline
@core.case_insensitive
def get_tells(inp):
    query = Tell.select().where(Tell.recipient == inp._user).execute()
    for tell in query:

        time = arrow.get(tell.time).humanize()
        msg = lexicon.topic.get if tell.topic else lexicon.tell.get

        yield msg.format(
            name=tell.sender,
            time=time,
            topic=tell.topic,
            text=tell.text)
        tell.delete_instance()


@core.command
@core.notice
@core.case_insensitive
def get_outbound_tells_count(inp):

    query = Tell.select().where(
        peewee.fn.Lower(Tell.sender) == inp._user,
        Tell.topic.is_null())

    if not query.exists():
        return lexicon.tell.outbound_empty

    users = ', '.join(sorted({i.recipient for i in query}))
    return lexicon.tell.outbound_count.format(
        total=query.count(),
        users=users)


@core.command
@core.notice
@core.case_insensitive
def purge_outbound_tells(inp):
    where_clause = peewee.fn.Lower(Tell.sender) == inp._user
    query = Tell.select().where(
        where_clause,
        Tell.topic.is_null())

    if not query.exists():
        return lexicon.tell.outbound_empty

    Tell.delete().where(where_clause).execute()
    return lexicon.tell.outbound_purged.format(count=query.count())


###############################################################################
# Seen
###############################################################################


@core.command
@core.case_insensitive
@core.parse_input(r'{name} ?(?P<first>--first|-f)?')
def get_user_seen(inp):
    if inp.name == core.config['irc']['nick']:
        return lexicon.seen.self
    order = Message.time if inp.first else Message.time.desc()
    query = Message.select().where(
        peewee.fn.Lower(Message.user) == inp.name,
        Message.channel == inp._channel).order_by(order)
    if not query.exists():
        return lexicon.seen.never
    seen = query.get()
    time = arrow.get(seen.time).humanize()
    msg = lexicon.seen.first if inp.first else lexicon.seen.last
    return msg.format(user=seen.user, time=time, text=seen.text)


###############################################################################
# Quotes
###############################################################################


@core.command
@core.parse_input(r'(?P<cmd>add|del)?.*')
def dispatch_quote(inp):
    if inp.cmd == 'add':
        return add_quote(inp)
    elif inp.cmd == 'del':
        return del_quote(inp)
    return get_quote(inp)


@core.parse_input(r'add ?{date}? {name} {text}')
def add_quote(inp):

    if Quote.select().where(
            Quote.user == inp.name.lower(),
            Quote.channel == inp._channel,
            Quote.text == inp.text).exists():
        return lexicon.quote.already_exists

    Quote.create(
        user=inp.name.lower(),
        channel=inp._channel,
        time=inp.time or arrow.utcnow().format('YYYY-MM-DD'),
        text=inp.text)

    return lexicon.quote.saved


@core.parse_input('del {name} {text}')
def del_quote(inp):

    query = Quote.select().where(
        Quote.user == inp.name.lower(),
        Quote.channel == inp._channel,
        Quote.text == inp.text)

    if not query.exists():
        return lexicon.quote.not_found

    query.get().delete_instance()
    return lexicon.quote.deleted


@core.case_insensitive
@core.parse_input(r'{name}? ?{index}?')
def get_quote(inp):

    query = Quote.select().where(Quote.channel == inp._channel)
    if inp.name:
        query = query.where(Quote.user == inp.name)

    if not query.exists():
        return lexicon.quote.none_saved

    index = int(inp.index or random.randint(1, query.count()))
    if index > query.count():
        return lexicon.input.bad_index
    quote = query.order_by(Quote.time).offset(index - 1).limit(1).get()

    return '[{}/{}] {} {}: {}'.format(
        index, query.count(), quote.time, quote.user, quote.text)


###############################################################################
# Memos
###############################################################################


@core.command
@core.parse_input('{name} {text}')
def remember_user(inp):

    Rem.delete().where(
        Rem.user == inp.name.lower(),
        Rem.channel == inp._channel).execute()

    Rem.create(
        user=inp.name.lower(),
        channel=inp._channel,
        text=inp.text)

    return lexicon.quote.saved


@core.command
@core.case_insensitive
@core.parse_input(r'\?{name}')
def recall_user(inp):

    rem = Rem.select().where(
        Rem.user == inp.name,
        Rem.channel == inp._channel)

    if rem.exists():
        return rem.get().text
    else:
        return lexicon.not_found.generic


###############################################################################
# Topics
###############################################################################


@core.command
@core.case_insensitive
@core.parse_input(r'@?{name}')
def subscribe_to_topic(inp):

    if inp._channel != core.config['irc']['sssc']:
        if Restricted.select().where(
                Restricted.topic == inp.name).exists():
            return lexicon.denied

    if Subscriber.select().where(
            Subscriber.user == inp._user,
            Subscriber.topic == inp.name).exists():
        return lexicon.topic.already_subscribed

    Subscriber.create(user=inp._user, topic=inp.name)
    return lexicon.topic.subscribed.format(topic=inp.name)


@core.command
@core.case_insensitive
@core.parse_input(r'@?{name}')
def unsubscribe_from_topic(inp):

    query = Subscriber.select().where(
        Subscriber.user == inp._user,
        Subscriber.topic == inp.name)

    if not query.exists():
        return lexicon.topic.not_subscribed

    query.get().delete_instance()
    return lexicon.topic.unsubscribed.format(topic=inp.name)


@core.command
@core.notice
@core.case_insensitive
def get_topics_count(inp):

    query = Subscriber.select().where(Subscriber.user == inp._user)

    if not query.exists():
        return lexicon.topic.user_has_no_topics

    topics = [i.topic for i in query]
    return lexicon.topic.count.format(topics=', '.join(topics))


@core.command
@core.case_insensitive
@core.parse_input(r'@?{name}')
def restrict_topic(inp):

    if inp._channel != core.config['irc']['sssc']:
        return lexicon.denied

    if Restricted.select().where(Restricted.topic == inp.name).exists():
        return lexicon.topic.already_restricted

    Restricted.create(topic=inp.name)
    return lexicon.topic.restricted


@core.command
@core.case_insensitive
@core.parse_input(r'@?{name}')
def unrestrict_topic(inp):

    if inp._channel != core.config['irc']['sssc']:
        return lexicon.denied

    query = Restricted.select().where(Restricted.topic == inp.name)
    if not query.exists():
        return lexicon.topic.not_restricted

    query.get().delete_instance()
    return lexicon.topic.unrestricted


###############################################################################
# Alerts
###############################################################################


@core.command
@core.parse_input(r'{date}|(?P<span>(\d+[dhm])+) {text}')
def set_alert(inp):
    if inp.date:
        alert = arrow.get(inp.date)
        if alert < arrow.utcnow():
            return lexicon.alert.past
    else:
        alert = arrow.utcnow()
        for length, unit in re.findall(r'(\d+)([dhm])', inp.span):
            unit = dict(d='days', h='hours', m='minutes')[unit]
            alert = alert.replace(**{unit: int(length)})
    Alert.create(user=inp._user.lower(), time=alert.timestamp, text=inp.text)
    return lexicon.alert.set


@core.command
@core.private
@core.multiline
@core.case_insensitive
def get_alerts(inp):
    now = arrow.utcnow()
    for alert in Alert.select().where(Alert.user == inp._user):
        if arrow.get(alert.time) < now:
            yield alert.text
            alert.delete_instance()
