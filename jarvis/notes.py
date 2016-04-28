#!/usr/bin/env python3

###############################################################################
# Module Imports
###############################################################################

import arrow
import random
import re
import peewee
import playhouse

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


def log_message(user, channel, text):
    Message.create(
        user=user.strip(), channel=channel,
        time=arrow.utcnow().timestamp, text=text)

###############################################################################


def sanitize(fn):
    return lambda x, *y: (fn(x, *y) if x else lexicon.input.missing)


@sanitize
def send_tell(inp, sender):
    recipient, text = inp.split(maxsplit=1)
    recipient = recipient.strip().rstrip(':,').lower()
    if not re.match(r'^@?[\w\[\]{}^|-]+$', recipient) or not text:
        return lexicon.input.incorrect
    sender = str(sender)
    time = arrow.utcnow().timestamp
    if not recipient.startswith('@'):
        Tell.create(
            sender=sender, recipient=recipient,
            text=text, time=time, topic=None)
        return lexicon.tell.send
    else:
        topic = recipient.lstrip('@')
        users = Subscriber.select().where(Subscriber.topic == topic)
        users = [i.user for i in users]
        if not users:
            return lexicon.topic.no_subscribers
        Tell.insert_many(dict(
            sender=sender, recipient=user, text=text,
            time=time, topic=topic) for user in users).execute()
        return lexicon.topic.send.format(count=len(users))


def get_tells(user):
    user = user.strip().lower()
    query = Tell.select().where(Tell.recipient == user).execute()
    tells = []
    for tell in query:
        time = arrow.get(tell.time).humanize()
        if not tell.topic:
            tells.append('{} said {}: {}'.format(tell.sender, time, tell.text))
        else:
            tells.append('{} said {} via @{}: {}'.format(
                tell.sender, time, tell.topic, tell.text))
        tell.delete_instance()
    return tells


def get_outbound_tells_count(user):
    user = user.strip().lower()
    query = Tell.select().where(
        peewee.fn.Lower(Tell.sender) == user, Tell.topic.is_null())
    if not query.exists():
        return lexicon.tell.outbound_empty
    users = ', '.join(sorted({i.recipient for i in query}))
    return lexicon.tell.outbound_count.format(total=query.count(), users=users)


def purge_outbound_tells(user):
    user = user.strip().lower()
    query = Tell.select().where(
        peewee.fn.Lower(Tell.sender) == user, Tell.topic.is_null())
    if not query.exists():
        return lexicon.tell.outbound_empty
    count = query.count()
    Tell.delete().where(peewee.fn.Lower(Tell.sender) == user).execute()
    return lexicon.tell.outbound_purged.format(count=count)

###############################################################################


def get_user_seen(user, channel, last=True):
    if not user:
        return lexicon.input.incorrect
    user = user.strip().lower()
    if user == core.config['irc']['nick']:
        return lexicon.seen.self
    order = Message.time.desc() if last else Message.time
    query = Message.select().where(
        peewee.fn.Lower(Message.user) == user,
        Message.channel == channel).order_by(order)
    try:
        msg = query.get()
    except Message.DoesNotExist:
        return lexicon.seen.never
    time = arrow.get(msg.time).humanize()
    result = lexicon.seen.last if last else lexicon.seen.first
    return result.format(user=msg.user, time=time, text=msg.text)


###############################################################################


def dispatch_quote(inp, channel):
    inp = inp.strip() if inp else ''
    parsed = re.match(r'^ *[0-9]* *$', inp)
    if parsed:
        return get_quote(None, channel, parsed.group(0).strip())
    parsed = re.match(
        r'^(add|del)? ?(\d{4}-\d{2}-\d{2})? ?([\w\d<>^{}[\]\\-]+)(.*)$', inp)
    if not parsed:
        return lexicon.input.incorrect
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
    if Quote.select().where(
            Quote.user == user,
            Quote.channel == channel, Quote.text == text).exists():
        return lexicon.quote.already_exists
    if not time:
        time = arrow.utcnow().format('YYYY-MM-DD')
    Quote.create(user=user, channel=channel, time=time, text=text)
    return lexicon.quote.saved


def get_quote(user, channel, index=None):
    query = Quote.select().where(Quote.channel == channel)
    if user:
        user = user.strip().lower()
        query = query.where(Quote.user == user)
    if not query.exists():
        return lexicon.quote.none_saved
    if not index:
        index = random.randint(1, query.count())
    else:
        try:
            index = int(index)
        except ValueError:
            return lexicon.input.bad_index
        if index not in range(1, query.count() + 1):
            return lexicon.input.bad_index
    quote = list(query.order_by(Quote.time))[int(index) - 1]
    return '[{}/{}] {} {}: {}'.format(
        index, query.count(), quote.time, quote.user, quote.text)


def delete_quote(user, channel, text):
    user = user.strip().lower()
    query = Quote.select().where(
        Quote.user == user, Quote.channel == channel, Quote.text == text)
    if not query.exists():
        return lexicon.quote.not_found
    query.get().delete_instance()
    return lexicon.quote.deleted

###############################################################################


def remember_user(inp, channel):
    user, text = inp.split(maxsplit=1)
    user = user.strip().lower()
    text = text.strip()
    Rem.delete().where(Rem.user == user, Rem.channel == channel).execute()
    Rem.create(user=user, channel=channel, text=text)
    return lexicon.quote.saved


def recall_user(user, channel):
    user = user.strip().lower()
    try:
        rem = Rem.select().where(
            Rem.user == user, Rem.channel == channel).get()
    except Rem.DoesNotExist:
        return lexicon.not_found.generic
    return rem.text

###############################################################################


def subscribe_to_topic(user, topic, super):
    user = user.strip().lower()
    if not topic:
        return lexicon.input.missing
    topic = topic.strip().lower().lstrip('@')
    if (not super and Restricted.select().where(
            Restricted.topic == topic).exists()):
        return lexicon.denied
    if Subscriber.select().where(
            Subscriber.user == user, Subscriber.topic == topic).exists():
        return lexicon.topic.already_subscribed
    Subscriber.create(user=user, topic=topic)
    return lexicon.topic.subscribed.format(topic=topic)


def unsubscribe_from_topic(user, topic):
    user = user.strip().lower()
    if not topic:
        return lexicon.input.missing
    topic = topic.strip().lower().lstrip('@')
    query = Subscriber.select().where(
        Subscriber.user == user, Subscriber.topic == topic)
    if not query.exists():
        return lexicon.topic.not_subscribed
    query.get().delete_instance()
    return lexicon.topic.unsubscribed.format(topic=topic)


def get_topics_count(user):
    user = user.strip().lower()
    query = Subscriber.select().where(Subscriber.user == user)
    if not query.exists():
        return lexicon.topic.user_has_no_topics
    topics = [i.topic for i in query]
    return lexicon.topic.count.format(topics=', '.join(topics))


def restrict_topic(topic, super):
    if not super:
        return lexicon.denied
    topic = topic.strip().lower().lstrip('@')
    if Restricted.select().where(Restricted.topic == topic).exists():
        return lexicon.topic.already_restricted
    Restricted.create(topic=topic)
    return lexicon.topic.restricted


def unrestrict_topic(topic, super):
    if not super:
        return lexicon.denied
    topic = topic.strip().lower().lstrip('@')
    query = Restricted.select().where(Restricted.topic == topic)
    if not query.exists():
        return lexicon.topic.not_restricted
    query.get().delete_instance()
    return lexicon.topic.unrestricted


###############################################################################


def set_alert(user, inp):
    if not inp:
        return lexicon.input.missing
    try:
        time, text = inp.split(maxsplit=1)
    except ValueError:
        return lexicon.input.missing
    text = text.strip()
    user = user.strip().lower()
    if not text:
        return lexicon.input.missing
    if re.match(r'\d{4}-\d{2}-\d{2}$', time):
        alert = arrow.get(time)
        if alert < arrow.utcnow():
            return lexicon.alert.past
    elif re.match(r'(\d+[dhm])+$', time):
        intervals = re.findall(r'(\d+)([dhm])', time)
        alert = arrow.utcnow()
        for length, unit in intervals:
            unit = dict(d='days', h='hours', m='minutes')[unit]
            alert = alert.replace(**{unit: int(length)})
    else:
        return lexicon.input.incorrect
    Alert.create(user=user, time=alert.timestamp, text=text)
    return lexicon.alert.set


def get_alerts(user):
    user = user.strip().lower()
    now = arrow.utcnow()
    results = []
    for alert in Alert.select().where(Alert.user == user):
        if arrow.get(alert.time) < now:
            results.append(alert.text)
            alert.delete_instance()
    return results
