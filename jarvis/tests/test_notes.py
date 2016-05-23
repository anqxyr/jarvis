#!/usr/bin/env python3
"""Test jarvis.notes module."""

###############################################################################
# Module Imports
###############################################################################

import hypothesis as hy
import hypothesis.strategies as st

from hypothesis.extra import datetime as hydt

from jarvis import core, notes, parser

###############################################################################


class MockLexicon:

    def __init__(self, route='lexicon'):
        self.route = route

    def __getattr__(self, value):
        return self.__class__(self.route + '.' + value)

    def __eq__(self, value):
        return self.route == value

    def format(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
        return self

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, self.route)

notes.lexicon = parser.lexicon = lexicon = MockLexicon()

###############################################################################


def run(fn, inp, *args, user='test-user', channel='test-channel', **kwargs):
    results = []
    inp = core.Inp(
        inp, user, channel, lambda x, private, notice: results.append(x))
    fn(inp, *args, **kwargs)
    return results[0] if len(results) == 1 else results

###############################################################################


def st_user():
    user = st.characters(blacklist_categories=['Cc', 'Cs', 'Zs', 'Zl', 'Zp'])
    user = user.filter(lambda x: x.strip() == x)
    user = user.filter(lambda x: not x.isdigit())
    user = user.filter(lambda x: x[0].isalpha())

    return user


def st_msg():
    return st.text().filter(str.strip)

###############################################################################
# Tell
###############################################################################


@hy.given(st.text())
def test_tell_random_input(inp):
    run(notes.tell, inp)


@hy.given(st_user(), st_msg())
def test_tell_send_user(user, msg):
    count = notes.Tell.select().count()
    inp = user + ' ' + msg
    assert run(notes.tell, inp) == lexicon.tell.send
    assert notes.Tell.select().count() == count + 1


@hy.given(st.none() | st_user())
def test_tell_send_fail(inp):
    """Test notes.tell command."""
    assert run(notes.tell, inp) == lexicon.input.incorrect


@hy.given(st.lists(st.text()))
def test_get_tells(messages):
    run(notes.get_tells, '')
    for m in messages:
        hy.assume(m.strip())
        run(notes.tell, 'test-user ' + m)
    query = notes.Tell.select().where(notes.Tell.recipient == 'test-user')
    assert query.count() == len(messages)
    tells = run(notes.get_tells, '')
    tells = tells if len(messages) != 1 else [tells]
    assert all(t == lexicon.tell.get for t in tells)
    assert query.count() == 0


@hy.given(st.text())
def test_tell_case_insensitive(inp):
    hy.assume(inp.strip())
    run(notes.get_tells, '')
    run(notes.tell, 'TEst-UsER {}'.format(inp))
    assert run(notes.get_tells, '').text == inp.rstrip()

###############################################################################
# Outbound
###############################################################################


@hy.given(st.text())
def test_outbound_random_input(inp):
    run(notes.outbound, inp)


@hy.given(st.sampled_from(['count', 'purge']))
def test_outbound_options(inp):
    assert run(notes.outbound, inp).route.startswith('lexicon.tell.outbound')


def test_outbound_count():
    run(notes.tell, 'test tell')
    assert run(notes.outbound, 'count') == lexicon.tell.outbound.count


def test_outbound_purge():
    run(notes.tell, 'test tell')
    assert run(notes.outbound, 'purge') == lexicon.tell.outbound.purged
    query = notes.Tell.select().where(notes.Tell.sender == 'test-user')
    assert query.count() == 0


def test_outbound_count_empty():
    run(notes.outbound, 'purge')
    assert run(notes.outbound, 'count') == lexicon.tell.outbound.empty

###############################################################################
# Seen
###############################################################################


@hy.given(st.text())
def test_seen_random_input(inp):
    run(notes.seen, inp)


def test_seen_last():
    run(notes.logevent, '_')
    assert run(notes.seen, 'test-user') == lexicon.seen.last


def test_seen_first():
    assert run(notes.seen, 'test-user -f') == lexicon.seen.first


def test_seen_never():
    assert run(notes.seen, '----') == lexicon.seen.never


@hy.given(st_user())
@hy.example('anqxyr')
@hy.example('test-user')
def test_seen_case_insensitive(user):
    upper = run(notes.seen, user.upper())
    lower = run(notes.seen, user.lower())
    assert upper == lower
    assert upper.user == lower.user
    assert upper.text == lower.text

###############################################################################
# Quote
###############################################################################


@hy.given(st.text())
@hy.settings(suppress_health_check=[hy.HealthCheck.random_module])
def test_quote_random_input(inp):
    run(notes.quote, inp)


@hy.given(st_user(), st_msg())
def test_quote_add(user, msg):
    inp = ' {} {}'.format(user, msg)
    run(notes.quote, 'del' + inp)
    assert run(notes.quote, 'add' + inp) == lexicon.quote.saved


@hy.given(st_user(), st_msg())
def test_quote_add_already_exists(user, msg):
    inp = ' {} {}'.format(user, msg)
    run(notes.quote, 'add' + inp)
    assert run(notes.quote, 'add' + inp) == lexicon.quote.already_exists


@hy.given(hydt.dates(), st_user(), st_msg())
def test_quote_add_date(date, user, msg):
    run(notes.quote, 'del {} {}'.format(user, msg))
    assert run(notes.quote, 'add {} {} {}'.format(
        date.isoformat(), user, msg)) == lexicon.quote.saved


@hy.settings(suppress_health_check=[hy.HealthCheck.random_module])
def test_quote_get_random():
    quote = run(notes.quote, '')
    assert quote == lexicon.quote.get
    assert quote.text


@hy.given(st.integers().filter(lambda x: x > 0))
def test_quote_get_index(index):
    query = notes.Quote.select().where(notes.Quote.channel == 'test-channel')
    hy.assume(index <= query.count())
    quote = run(notes.quote, str(index))
    assert quote == lexicon.quote.get
    assert quote.index == index


@hy.given(st.integers().filter(lambda x: x <= 0))
def test_quote_get_index_negative(index):
    r = run(notes.quote, str(index))
    assert r == lexicon.input.bad_index


@hy.given(st.integers().filter(lambda x: x > 0))
def test_quote_get_index_too_big(index):
    query = notes.Quote.select().where(notes.Quote.channel == 'test-channel')
    hy.assume(index > query.count())
    assert run(notes.quote, str(index)) == lexicon.input.bad_index


@hy.settings(suppress_health_check=[hy.HealthCheck.random_module])
@hy.given(st_user())
def test_quote_get_user(user):
    run(notes.quote, 'add {} test-quote'.format(user))
    quote = run(notes.quote, user)
    assert quote.user == user.lower()


@hy.given(st_user(), st.integers().filter(lambda x: x > 0))
def test_quote_get_user_and_index(user, index):
    query = (
        notes.Quote.select()
        .where(notes.Quote.channel == 'test-channel')
        .where(notes.Quote.user == user.lower()))
    hy.assume(index <= query.count())
    quote = run(notes.quote, user + ' ' + str(index))
    assert quote == lexicon.quote.get
    assert quote.user == user.lower()

###############################################################################
# Memos
###############################################################################


@hy.given(st.text())
def test_save_memo_random_input(inp):
    run(notes.save_memo, inp)


@hy.given(st_user(), st_msg())
def test_save_memo(user, msg):
    assert run(notes.save_memo, user + ' ' + msg) == lexicon.quote.saved

###############################################################################
# Topics
###############################################################################


@hy.given(st.text())
def test_topic_random_input(inp):
    run(notes.topic, inp)


@hy.given(st_user())
def test_topic_subscribe(topic):
    run(notes.topic, 'unsub {}'.format(topic))
    r = run(notes.topic, 'sub {}'.format(topic), channel='sssc-test')
    assert r == lexicon.topic.subscribed


@hy.given(st_user())
def test_topic_already_subscribed(topic):
    run(notes.topic, 'unres {}'.format(topic), channel='sssc-test')
    run(notes.topic, 'sub {}'.format(topic))
    r = run(notes.topic, 'sub {}'.format(topic))
    assert r == lexicon.topic.already_subscribed


@hy.given(st_user())
def test_topic_restrict(topic):
    run(notes.topic, 'unres {}'.format(topic), channel='sssc-test')
    r = run(notes.topic, 'res {}'.format(topic), channel='sssc-test')
    assert r == lexicon.topic.restricted


@hy.given(st_user())
def test_topic_restrict_denied(topic):
    run(notes.topic, 'unres {}'.format(topic), channel='sssc-test')
    r = run(notes.topic, 'res {}'.format(topic))
    assert r == lexicon.denied


@hy.given(st_user(), st_msg())
def test_topic_send(topic, msg):
    run(notes.topic, 'sub {}'.format(topic), channel='sssc-test')
    run(notes.get_tells, '')
    run(notes.tell, '@{} {}'.format(topic, msg))
    r = run(notes.get_tells, '')
    assert r == lexicon.topic.get
    assert r.text == msg.rstrip()
    assert r.topic == topic

###############################################################################
# Alert
###############################################################################


@hy.given(st.text())
def test_alert_random_input(inp):
    run(notes.alert, inp)
