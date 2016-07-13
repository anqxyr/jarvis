#!/usr/bin/env python3
"""
Jarvis Notes Module.

All commands that require persistent storage belong here. This includes
logging, tells, and quotes.
"""
###############################################################################
# Module Imports
###############################################################################

import arrow
import random
import re
import peewee
import playhouse.sqlite_ext
import playhouse.migrate
import itertools

from . import core, lex, parser


###############################################################################
# Database ORM Classes
###############################################################################


db = playhouse.sqlite_ext.SqliteExtDatabase('jarvis.db', journal_mode='WAL')


class BaseModel(peewee.Model):
    """Peewee Base Table/Model Class."""

    class Meta:
        """Bind Model definitions to the database."""

        database = db


class Tell(BaseModel):
    """Database Tell Table."""

    sender = peewee.CharField()
    recipient = peewee.CharField(index=True)
    topic = peewee.CharField(null=True)
    text = peewee.TextField()
    time = peewee.DateTimeField()


class Message(BaseModel):
    """Database Message Table."""

    user = peewee.CharField(index=True, null=True)
    channel = peewee.CharField(index=True)
    time = peewee.DateTimeField()
    text = peewee.TextField()


class Quote(BaseModel):
    """Database Quote Table."""

    user = peewee.CharField(index=True)
    channel = peewee.CharField()
    time = peewee.DateTimeField()
    text = peewee.TextField()


class Rem(BaseModel):
    """Database Rem Table."""

    user = peewee.CharField(index=True)
    channel = peewee.CharField()
    text = peewee.TextField()


class Subscriber(BaseModel):
    """Database Subscriber Table."""

    user = peewee.CharField()
    topic = peewee.CharField(index=True)


class Restricted(BaseModel):
    """Database Restricted Table."""

    topic = peewee.CharField(index=True)


class Alert(BaseModel):
    """Database Alert Table."""

    user = peewee.CharField(index=True)
    time = peewee.DateTimeField()
    text = peewee.TextField()

###############################################################################


def init():
    """Initialize the database, create missing tables."""
    db.connect()
    db.create_tables(
        [Tell, Message, Quote, Rem, Subscriber, Restricted, Alert], safe=True)


init()


def logevent(inp):
    """Log input into the database."""
    Message.create(
        user=inp.user.lower(), channel=inp.channel,
        time=arrow.utcnow().timestamp, text=inp.text)


###############################################################################
# Tells
###############################################################################


@core.command
@parser.tell
def tell(inp, *, user, topic, message):
    """
    Send messages to other users.

    Saves the message and delivers them to the target next time they're in
    the same channel with the bot. The target is either a single user, or a
    tell topic. In the later case, all users subscribed to the topic at the
    moment the tell it sent will recieve the message.
    """
    if topic:
        users = Subscriber.select().where(Subscriber.topic == topic)
        users = [i.user for i in users]
        if not users:
            return lex.topic.no_subscribers
    else:
        users = [user]

    data = dict(
        sender=inp.user,
        text=message,
        time=arrow.utcnow().timestamp,
        topic=topic)
    Tell.insert_many(dict(recipient=i, **data) for i in users).execute()

    msg = lex.topic.send if topic else lex.tell.send
    return msg(count=len(users))


@core.command
@core.private
@core.multiline
def get_tells(inp):
    """Retrieve incoming messages."""
    tells = list(Tell.select().where(Tell.recipient == inp.user.lower()))
    Tell.delete().where(Tell.recipient == inp.user.lower()).execute()

    if tells:
        inp._send(
            lex.tell.new(count=len(tells)).compose(inp),
            notice=True, private=False)

    for tell in tells:

        time = arrow.get(tell.time).humanize()
        msg = lex.topic.get if tell.topic else lex.tell.get

        yield msg(
            name=tell.sender,
            time=time,
            topic=tell.topic,
            text=tell.text)


@core.command
@core.notice
def show_tells(inp):
    query = Tell.select().where(Tell.recipient == inp.user.lower())
    if not query.exists():
        return lex.tell.no_new


@core.command
@core.notice
@parser.outbound
def outbound(inp, *, action):
    """
    Access outbound tells.

    Outband tells are tells sent by the input user, which haven't been
    delivered to their targets yet.

    Ignores messages sent to tell topics.
    """
    query = Tell.select().where(
        peewee.fn.Lower(Tell.sender) == inp.user.lower(),
        Tell.topic.is_null())

    if not query.exists():
        return lex.tell.outbound.empty

    if action == 'count':
        msg = lex.tell.outbound.count
    elif action == 'purge':
        Tell.delete().where(
            peewee.fn.Lower(Tell.sender) == inp.user.lower(),
            Tell.topic.is_null()).execute()
        msg = lex.tell.outbound.purged
    elif action == 'echo':
        inp.multiline = True
        msg = lex.tell.outbound.echo
        return [msg(
            time=arrow.get(t.time).humanize(),
            user=t.recipient, message=t.text) for t in query]

    users = ', '.join(sorted({i.recipient for i in query}))
    return msg(count=query.count(), users=users)


###############################################################################
# Seen
###############################################################################


@core.command
@parser.seen
def seen(inp, *, channel, user, first, total):
    """Retrieve the first or the last message said by the user."""
    if user == core.config['irc']['nick']:
        return lex.seen.self

    if channel:
        if channel not in inp.privileges:
            return lex.denied
        inp.channel = channel
        inp.notice = True

    query = Message.select().where(
        Message.user == user, Message.channel == inp.channel)
    if not query.exists():
        return lex.seen.never

    if total:
        total = query.count()
        time = arrow.get(arrow.now().format('YYYY-MM'), 'YYYY-MM')
        this_month = query.where(Message.time > time.timestamp).count()
        return lex.seen.total(
            user=user, total=total, this_month=this_month)

    seen = query.order_by(Message.time if first else Message.time.desc()).get()
    time = arrow.get(seen.time).humanize()
    msg = lex.seen.first if first else lex.seen.last
    return msg(user=user, time=time, text=seen.text)


###############################################################################
# Quotes
###############################################################################


@core.command
@parser.quote
def quote(inp, *, channel, mode):
    if inp.channel in core.config['irc']['quotes_disabled']:
        return

    if channel:
        if channel not in inp.privileges:
            return lex.denied
        inp.channel = channel
        inp.notice = True

    if mode == 'add':
        return quote_add(inp)
    elif mode == 'del':
        return quote_del(inp)
    return quote_get(inp)


@parser.quote_add
def quote_add(inp, *, date, user, message):
    """!quote add [<date>] <user> <message> -- Save user's quote."""
    if Quote.select().where(
            Quote.user == user,
            Quote.channel == inp.channel,
            Quote.text == message).exists():
        return lex.quote.already_exists

    Quote.create(
        user=user,
        channel=inp.channel,
        time=(date or arrow.utcnow()).format('YYYY-MM-DD'),
        text=message)

    return lex.quote.saved


@parser.quote_del
def quote_del(inp, *, user, message):
    """!quote del <user> <message> -- Delete the matching quote."""
    query = Quote.select().where(
        Quote.user == user,
        Quote.channel == inp.channel,
        Quote.text == message)

    if not query.exists():
        return lex.quote.not_found

    query.get().delete_instance()
    return lex.quote.deleted


@parser.quote_get
def quote_get(inp, *, user, index):
    """Retrieve a quote."""
    if index is not None and index <= 0:
        return lex.input.bad_index

    query = Quote.select().where(Quote.channel == inp.channel)
    if user:
        query = query.where(Quote.user == user)

    if not query.exists():
        return lex.quote.none_saved

    index = index or random.randint(1, query.count())
    if index > query.count():
        return lex.input.bad_index
    quote = query.order_by(Quote.time).limit(1).offset(index - 1)[0]

    return lex.quote.get(
        index=index,
        total=query.count(),
        time=str(quote.time)[:10],
        user=quote.user,
        text=quote.text)


###############################################################################
# Memos
###############################################################################


@core.command
@parser.save_memo
def save_memo(inp, *, user, message, purge):
    """!rem <user> <message> -- Make a memo about the user."""
    if inp.channel in core.config['irc']['quotes_disabled']:
        return

    Rem.delete().where(
        peewee.fn.Lower(Rem.user) == user,
        Rem.channel == inp.channel).execute()

    if purge:
        return lex.quote.deleted

    Rem.create(user=user, channel=inp.channel, text=message)

    return lex.quote.saved


@core.command
def load_memo(inp):
    """?<user> -- Display the user's memo."""
    if inp.channel in core.config['irc']['quotes_disabled']:
        return

    rem = Rem.select().where(
        Rem.user == inp.text.lower()[1:],
        Rem.channel == inp.channel)

    if rem.exists():
        return rem.get().text
    else:
        return lex.not_found.generic


###############################################################################
# Topics
###############################################################################


@core.command
@parser.topic
def topic(inp, *, topic, action):

    if action == 'list':
        return topic_list(inp)

    if action in ['unsubscribe', 'unsub']:
        return topic_sub(inp, topic, True)

    if action in ['subscribe', 'sub']:
        return topic_sub(inp, topic, False)

    if action in ['restrict', 'res']:
        return topic_restrict(inp, topic, False)

    if action in ['unrestrict', 'unres']:
        return topic_restrict(inp, topic, True)


@core.notice
def topic_list(inp):
    query = Subscriber.select().where(
        Subscriber.user == inp.user.lower())

    if not query.exists():
        return lex.topic.user_has_no_topics

    topics = [i.topic for i in query]
    return lex.topic.count(topics=', '.join(topics))


def topic_sub(inp, topic, remove):
    if (inp.channel != core.config['irc']['sssc'] and
        Restricted.select().where(Restricted.topic == topic).exists() and
            not remove):
        return lex.denied

    query = Subscriber.select().where(
        Subscriber.user == inp.user.lower(),
        Subscriber.topic == topic)

    if remove:
        if not query.exists():
            return lex.topic.not_subscribed
        query.get().delete_instance()
        return lex.topic.unsubscribed(topic=topic)
    else:
        if query.exists():
            return lex.topic.already_subscribed
        Subscriber.create(user=inp.user.lower(), topic=topic)
        return lex.topic.subscribed(topic=topic)


def topic_restrict(inp, topic, remove):
    if inp.channel != core.config['irc']['sssc']:
        return lex.denied

    query = Restricted.select().where(Restricted.topic == topic)

    if remove:
        if not query.exists():
            return lex.topic.not_restricted
        query.get().delete_instance()
        return lex.topic.unrestricted
    else:
        if query.exists():
            return lex.topic.already_restricted
        Restricted.create(topic=topic)
        return lex.topic.restricted

###############################################################################
# Alerts
###############################################################################


@core.command
@parser.alert
def alert(inp, *, date, span, message):
    """!alert [<date>|<delay>] <message> -- Remind your future self."""
    if date and date < arrow.utcnow():
        return lex.alert.past

    if span:
        date = arrow.utcnow()
        for length, unit in re.findall(r'(\d+)([dhm])', span):
            unit = dict(d='days', h='hours', m='minutes')[unit]
            date = date.replace(**{unit: int(length)})

    Alert.create(user=inp.user.lower(), time=date.timestamp, text=message)
    return lex.alert.set


@core.command
@core.private
@core.multiline
def get_alerts(inp):
    """Retrieve stored alerts."""
    now = arrow.utcnow().timestamp
    where = ((Alert.user == inp.user.lower()) & (Alert.time < now))
    alerts = [i.text for i in Alert.select().where(where)]
    Alert.delete().where(where)
    return alerts


def backport(name):
    start = arrow.now()

    def parse_line(line):
        line = line.split()
        time = arrow.get(line[0]).timestamp
        if line[1].startswith('<') and line[1].endswith('>'):
            user = line[1][1:-1]
            text = line[2:]
        else:
            user = None
            text = line[1:]
        text = ' '.join(text)
        return time, user, text

    with open(name) as file:
        lines = (parse_line(i) for i in file)
        lines = (
            {'time': a, 'user': b, 'text': c, 'channel': name}
            for a, b, c in lines)

        idx = 0
        chunk = list(itertools.islice(lines, 500))
        with db.atomic():
            while chunk:
                print(idx)
                idx += 500
                Message.insert_many(chunk).execute()
                chunk = list(itertools.islice(lines, 500))
            print(arrow.now() - start)

    print('Done!')
    print(arrow.now() - start)
