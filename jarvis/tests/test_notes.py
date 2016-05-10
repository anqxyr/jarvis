#!/usr/bin/env python3
"""Test jarvis.notes module."""

###############################################################################
# Module Imports
###############################################################################

import hypothesis as hy
import hypothesis.strategies as st

from jarvis import core, notes

###############################################################################


class MockLexicon:

    def __init__(self, path='lexicon'):
        self.path = path

    def __getattr__(self, value):
        return self.__class__(self.path + '.' + value)

    def format(self, **kwargs):
        return self.path

    def __str__(self):
        return self.path

notes.lexicon = MockLexicon()

###############################################################################


def run(fn, inp, *args, **kwargs):
    results = []
    inp = core.Inp(
        inp, 'test-user', 'test-channel',
        lambda x, private, notice: results.append(x))
    fn(inp, *args, **kwargs)
    if len(results) == 1:
        return str(results[0])
    return list(map(str, results))

###############################################################################


@hy.given(st.text())
def test_tell_random_input(inp):
    run(notes.tell, inp)


@hy.given(st.text())
def test_tell_send_user_successful(inp):
    """Test notes.tell command."""
    hy.assume(not inp.startswith('@'))
    hy.assume(len(inp.split()) > 1)
    count = notes.Tell.select().count()
    assert run(notes.tell, inp) == 'lexicon.tell.send'
    assert notes.Tell.select().count() == count + 1


@hy.given(st.none())
def test_tell_send_failed(inp):
    """Test notes.tell command."""
    assert run(notes.tell, inp) == notes.tell._usage


@hy.given(st.lists(st.text()))
def test_get_tells(messages):
    run(notes.get_tells, '')
    for m in messages:
        hy.assume(m.strip())
        run(notes.tell, 'test-user ' + m)
    query = notes.Tell.select().where(notes.Tell.recipient == 'test-user')
    assert query.count() == len(messages)
    tells = run(notes.get_tells, '')
    if len(messages) != 1:
        assert tells == ['lexicon.tell.get'] * len(messages)
    else:
        assert tells == 'lexicon.tell.get'
    assert query.count() == 0

###############################################################################


@hy.given(st.text())
def test_outbound_random_input(inp):
    run(notes.outbound, inp)


def test_outbound_count_successful():
    run(notes.tell, 'test tell')
    assert run(notes.outbound, '--count') == 'lexicon.tell.outbound.count'


def test_outbound_purge_successful():
    run(notes.tell, 'test tell')
    assert run(notes.outbound, '--purge') == 'lexicon.tell.outbound.purged'
    query = notes.Tell.select().where(notes.Tell.sender == 'test-user')
    assert query.count() == 0


def test_outbound_count_empty():
    run(notes.outbound, '--purge')
    assert run(notes.outbound, '--count') == 'lexicon.tell.outbound.empty'

###############################################################################
