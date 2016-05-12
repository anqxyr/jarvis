#!/usr/bin/env python3
"""Test jarvis.notes module."""

###############################################################################
# Module Imports
###############################################################################

import hypothesis as hy
import hypothesis.strategies as st

from hypothesis.extra import datetime as hydt

from jarvis import core, notes

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

notes.lexicon = lexicon = MockLexicon()

###############################################################################


def run(fn, inp, *args, **kwargs):
    results = []
    inp = core.Inp(
        inp, 'test-user', 'test-channel',
        lambda x, private, notice: results.append(x))
    fn(inp, *args, **kwargs)
    return results[0] if len(results) == 1 else results

###############################################################################


def st_user():
    user = st.characters(blacklist_categories=['Cc', 'Cs', 'Zs', 'Zl', 'Zp'])
    user = user.filter(lambda x: x.strip().rstrip(':,'))
    user = user.filter(lambda x: not x.strip().startswith('@'))
    user = user.filter(lambda x: not x.isdigit())
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
def test_tell_send_user_successful(user, msg):
    count = notes.Tell.select().count()
    inp = user + ' ' + msg
    assert run(notes.tell, inp) == lexicon.tell.send
    assert notes.Tell.select().count() == count + 1


@hy.given(st.none() | st_user())
def test_tell_send_failed(inp):
    """Test notes.tell command."""
    assert run(notes.tell, inp) == notes.tell._usage


@hy.given(st.lists(st.text()))
def test_get_tells_successful(messages):
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
    assert run(notes.get_tells, '').text == inp.strip()

###############################################################################
# Outbound
###############################################################################


@hy.given(st.text())
def test_outbound_random_input(inp):
    run(notes.outbound, inp)


@hy.given(st.sampled_from(['-c', '--count', '-p', '--purge']))
def test_outbound_options(inp):
    assert run(notes.outbound, inp).route.startswith('lexicon.tell.outbound')


def test_outbound_count_successful():
    run(notes.tell, 'test tell')
    assert run(notes.outbound, '--count') == lexicon.tell.outbound.count


def test_outbound_purge_successful():
    run(notes.tell, 'test tell')
    assert run(notes.outbound, '--purge') == lexicon.tell.outbound.purged
    query = notes.Tell.select().where(notes.Tell.sender == 'test-user')
    assert query.count() == 0


def test_outbound_count_empty():
    run(notes.outbound, '--purge')
    assert run(notes.outbound, '--count') == lexicon.tell.outbound.empty

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
    assert run(notes.seen, '   ') == lexicon.seen.never


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


def test_quote_usage_messages():
    assert run(notes.quote, '--help') == notes.quote._usage
    assert run(notes.quote, 'add') == notes.quote_add._usage
    assert run(notes.quote, 'del') == notes.quote_del._usage


@hy.given(st_user(), st_msg())
def test_quote_add_successful(user, msg):
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
def test_quote_get_index_negative_fail(index):
    assert run(notes.quote, str(index)) == notes.quote_get._usage


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
    assert quote.user.lower() == user.lower()


@hy.given(st_user(), st.integers().filter(lambda x: x > 0))
def test_quote_get_user_and_index(user, index):
    query = (
        notes.Quote.select()
        .where(notes.Quote.channel == 'test-channel')
        .where(notes.peewee.fn.Lower(notes.Quote.user) == user.lower()))
    hy.assume(index <= query.count())
    quote = run(notes.quote, user + ' ' + str(index))
    assert quote == lexicon.quote.get
    assert quote.user.lower() == user.lower()

###############################################################################
