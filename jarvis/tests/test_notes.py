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
# Tell
###############################################################################


@hy.given(st.text())
def test_tell_random_input(inp):
    run(notes.tell, inp)


@hy.given(st.text())
def test_tell_send_user_successful(inp):
    """Test notes.tell command."""
    hy.assume(not inp.strip().startswith('@'))
    hy.assume(len(inp.split()) > 1)
    hy.assume(inp.split()[0].strip(':,'))
    count = notes.Tell.select().count()
    assert run(notes.tell, inp) == lexicon.tell.send
    assert notes.Tell.select().count() == count + 1


@hy.given(st.none())
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


@hy.given(st.characters(blacklist_categories='ZC'))
@hy.example('anqxyr')
@hy.example('test-user')
def test_seen_case_insensitive(inp):
    upper = run(notes.seen, inp.upper())
    lower = run(notes.seen, inp.lower())
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
    assert run(notes.quote, '') == notes.quote._usage
    assert run(notes.quote, 'add') == notes.quote_add._usage
    assert run(notes.quote, 'del') == notes.quote_del._usage


@hy.given(st.text())
def test_quote_add_successful(inp):
    hy.assume(len(inp.split()) > 1)
    run(notes.quote, 'del ' + inp)
    assert run(notes.quote, 'add ' + inp) == lexicon.quote.saved


@hy.given(st.text())
def test_quote_add_already_exists(inp):
    hy.assume(len(inp.split()) > 1)
    run(notes.quote, 'add ' + inp)
    assert run(notes.quote, 'add ' + inp) == lexicon.quote.already_exists


@hy.given(hydt.dates(), st.text())
def test_quote_add_date(date, inp):
    hy.assume(len(inp.split()) > 1)
    run(notes.quote, 'del ' + inp)
    result = run(notes.quote, 'add {} {}'.format(date.isoformat(), inp))
    assert result == lexicon.quote.saved
