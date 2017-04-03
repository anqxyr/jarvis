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
import functools
import markovify
import random
import re

from . import core, lex, parser, db


###############################################################################


db.init('jarvis.db')


@core.rule(r'(.*)')
def logevent(inp):
    """Log input into the database."""
    db.Message.create(
        user=inp.user, channel=inp.channel,
        time=arrow.utcnow().timestamp, text=inp.text)


###############################################################################
# Tells
###############################################################################


@core.command
@parser.tell
def tell(inp, *, user, message):
    """
    Send messages to other users.

    Saves the message and delivers them to the target next time they're in
    the same channel with the bot.
    """
    db.Tell.create(
        recipient=user,
        sender=inp.user,
        text=message,
        time=arrow.utcnow().timestamp,
        topic=None)

    return lex.tell.send


@core.command
@parser.masstell
def masstell(inp, *, users, message):
    """Send a single message to several users."""
    if not users or not message:
        return lex.masstell.missing_args
    time = arrow.utcnow().timestamp
    db.Tell.insert_many([dict(
        recipient=user,
        sender=inp.user,
        text=message,
        time=time,
        topic=None) for user in users]).execute()
    return lex.tell.send


@core.rule(r'(.*)')
@core.private
@core.multiline
def get_tells(inp):
    """Retrieve incoming messages."""
    tells = list(db.Tell.find(recipient=inp.user))
    db.Tell.purge(recipient=inp.user)

    if tells:
        inp._send(
            lex.tell.new(count=len(tells)),
            notice=True, private=False)

    for tell in tells:

        yield lex.tell.get(
            name=tell.sender,
            time=arrow.get(tell.time).humanize(),
            text=tell.text)


@core.command
@core.alias('st')
@core.notice
def showtells(inp):
    """Check for incoming messages."""
    if not db.Tell.find_one(recipient=inp.user):
        return lex.tell.no_new


@core.command
@core.notice
@core.multiline
@parser.outbound
def outbound(inp, *, purge, echo):
    """
    Access outbound tells.

    Outband tells are tells sent by the input user, which haven't been
    delivered to their targets yet.

    Ignores messages sent to tell topics.
    """
    query = db.Tell.find(sender=inp.user, topic=None)

    if not query.exists():
        yield lex.outbound.empty

    elif purge is True:
        db.Tell.purge(sender=inp.user, topic=None)
        yield lex.outbound.purged(count=query.count())

    elif purge:
        db.Tell.purge(sender=inp.user, topic=None, recipient=purge)
        yield lex.outbound.purged(count=query.count())

    elif echo:
        for tell in query:
            yield lex.outbound.echo(
                time=arrow.get(tell.time).humanize(),
                user=tell.recipient, message=tell.text)

    else:
        yield lex.outbound.count(
            count=query.count(), users={i.recipient for i in query})


###############################################################################
# Seen
###############################################################################

@core.command
@parser.seen
@core.crosschannel
def seen(inp, *, user, first, total):
    """Show the first message said by the user."""
    if user == core.config.irc.nick:
        return lex.seen.self

    query = db.Message.find(user=user, channel=inp.channel)
    if not query.exists():
        return lex.seen.never

    if total:
        total = query.count()
        time = arrow.get(arrow.now().format('YYYY-MM'), 'YYYY-MM')
        this_month = query.where(db.Message.time > time.timestamp).count()
        return lex.seen.total(
            user=user, total=total, this_month=this_month)

    seen = query.order_by(
        db.Message.time if first else db.Message.time.desc()).get()
    time = arrow.get(seen.time).humanize()
    msg = lex.seen.first if first else lex.seen.last
    return msg(user=user, time=time, text=seen.text)


###############################################################################
# Quotes
###############################################################################


def _memos_allowed(inp, value):
    if inp.config.memos == 'off':
        return False
    if inp.config.memos == 'all':
        return True
    return value.isalnum() if value else True


@core.command
@parser.quote
@core.crosschannel
def quote(inp, mode, **kwargs):
    """
    Manage quotes.

    This command is disabled in #site19.
    """
    if not _memos_allowed(inp, kwargs.get('user', '')):
        return lex.denied
    return quote.dispatch(inp, mode, **kwargs)


@quote.subcommand()
def get_quote(inp, *, user, index):
    """Retrieve a quote."""
    if index is not None and index <= 0:
        return lex.input.bad_index

    if user:
        query = db.Quote.find(channel=inp.channel, user=user)
    else:
        query = db.Quote.find(channel=inp.channel)

    if not query.exists():
        return lex.quote.none_saved

    index = index or random.randint(1, query.count())
    if index > query.count():
        return lex.input.bad_index
    quote = query.order_by(db.Quote.time).limit(1).offset(index - 1)[0]

    return lex.quote.get(
        index=index,
        total=query.count(),
        time=str(quote.time)[:10],
        user=quote.user,
        text=quote.text)


@quote.subcommand('add')
def add_quote(inp, *, date, user, message):
    """Add new quote."""
    if db.Quote.find_one(user=user, channel=inp.channel, text=message):
        return lex.quote.already_exists

    db.Quote.create(
        user=user,
        channel=inp.channel,
        time=(date or arrow.utcnow()).format('YYYY-MM-DD'),
        text=message)

    return lex.quote.added


@quote.subcommand('del')
def delete_quote(inp, *, user, message):
    """
    Delete quote.

    Deletion requires the full text of the quote in order to prevent
    accidental deletions, as well as to provide an additional copy of the
    deleted memo for the logs.
    """
    quote = db.Quote.find_one(user=user, channel=inp.channel, text=message)

    if not quote:
        return lex.quote.not_found

    quote.delete_instance()
    return lex.quote.deleted


###############################################################################
# Memos
###############################################################################


@core.command
@parser.memo
@core.crosschannel
def memo(inp, mode, **kwargs):
    """
    Manage memos.

    This command is disabled in #site19

    Memos are short persistent messages storing useful information about the
    user. Memos are channel-specific and support cross-channel access. Each
    user can have only a single memo stored in a particular channel.

    Unlike quotes, memo creation times are not preserved.
    """
    if not _memos_allowed(inp, kwargs.get('user', '')):
        return lex.denied
    return memo.dispatch(inp, mode, **kwargs)


@memo.subcommand()
def get_memo(inp, *, user):
    """Retrieve the specified user's memo."""
    memo = db.Memo.find_one(user=user, channel=inp.channel)

    if memo:
        return lex.memo.get(user=user, text=memo.text)
    else:
        return lex.memo.not_found


@memo.subcommand('add')
def add_memo(inp, *, user, message):
    """
    Add a new memo.

    If the specified user already has a memo in this channel, the operation
    will be aborted to prevent accidental overwrites.

    If you wish to overwrite an old memo, delete it explicitly and add the
    new memo in its place afterwards.
    """
    if db.Memo.find_one(user=user, channel=inp.channel):
        return lex.memo.already_exists

    db.Memo.create(user=user, channel=inp.channel, text=message)
    return lex.memo.added


@memo.subcommand('del')
def delete_memo(inp, *, user, message):
    """
    Delete memo.

    Deletion requires the full text of the memo in order to prevent accidental
    deletions, as well as to provide an additional copy of the deleted memo
    for the logs.
    """
    memo = db.Memo.find_one(
        user=user, channel=inp.channel, text_lower=message)
    if not memo:
        return lex.memo.not_found

    memo.delete_instance()
    return lex.memo.deleted


@memo.subcommand('append')
def append_memo(inp, *, user, message):
    """
    Append memo.

    Adds additional text to the end of the previously stored memo, without
    deletiing the original.
    """
    memo = db.Memo.find_one(user=user, channel=inp.channel)
    if not memo:
        return lex.memo.not_found

    memo.text += ' ' + message
    memo.save()
    return lex.memo.added


@memo.subcommand('count')
def count_memos(inp):
    """Output the number of memos stored in this channel."""
    return lex.memo.count(count=db.Memo.find(channel=inp.channel).count())


@core.command
@parser.rem
def rem(inp, *, user, message):
    """Shorthand for '!memo add'."""
    if not _memos_allowed(inp, user):
        return lex.denied
    return add_memo(inp, user=user, message=message)


@core.rule(r'^\?([^\s]+)\s*$')
def peek_memo(inp):
    if not _memos_allowed(inp, inp.text):
        return
    return get_memo(inp, user=inp.text.lower())


###############################################################################
# Alerts
###############################################################################


@core.command
@parser.alert
def alert(inp, *, date, span, message):
    """Make a reminder for your future self."""
    if date and date < arrow.utcnow():
        return lex.alert.past

    if span:
        date = arrow.utcnow()
        for length, unit in re.findall(r'(\d+)([dhm])', span):
            unit = dict(d='days', h='hours', m='minutes')[unit]
            date = date.replace(**{unit: int(length)})

    db.Alert.create(user=inp.user, time=date.timestamp, text=message)
    return lex.alert.set


@core.rule(r'(.*)')
@core.private
@core.multiline
def get_alerts(inp):
    """Retrieve stored alerts."""
    now = arrow.utcnow().timestamp
    where = ((db.Alert.user == inp.user) & (db.Alert.time < now))
    alerts = [i.text for i in db.Alert.select().where(where)]
    db.Alert.delete().where(where).execute()
    return alerts


@functools.lru_cache()
def get_text_model(channel, user):
    if user:
        lines = db.Message.find(channel=channel, user=user)
    else:
        lines = db.Message.find(channel=channel)
    lines = lines.order_by(db.Message.id.desc()).limit(10000)
    text = '\n'.join([i.text for i in lines])
    return markovify.NewlineText(text)


#@core.command
@parser.gibber
@core.crosschannel
def gibber(inp, user):
    """
    Generate a message using markov chains, hatbot-like.

    If the user isn't specified, generates the message based on the log of
    the entire channel.
    """
    if user and not db.Message.find_one(channel=inp.channel, user=user):
        return lex.gibber.no_such_user
    model = get_text_model(inp.channel, user)
    return lex.gibber.say(text=model.make_short_sentence(200))
