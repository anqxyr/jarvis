#!/usr/bin/env python3
"""Test jarvis.notes module."""

###############################################################################
# Module Imports
###############################################################################

import functools

from jarvis import core, lex
from jarvis.tests.utils import run

###############################################################################

run = functools.partial(run, _channel='#conftest')

###############################################################################


def test_configure_memos_alphanumeric():
    assert run('.conf memos alphanumeric') == lex.configure.memos.alphanumeric
    assert run('.rem ??? test') == lex.denied
    assert run('.rem abc test') == lex.memo.added


def test_configure_memos_all():
    assert run('.conf memos all') == lex.configure.memos.all
    assert run('.rem ??? test') == lex.memo.added


def test_configure_memos_off():
    assert run('.conf memos') == lex.configure.memos.off
    assert run('.rem test test') == lex.denied


def test_configure_lcratings_on():
    assert run('.conf lcratings on') == lex.configure.lcratings.true


def test_configure_lcratings_off():
    assert run('.conf lcratings off') == lex.configure.lcratings.false
    assert run('.lc') == [lex.show_page.nr_summary] * 3


def test_configure_keeplogs():
    run('.conf keeplogs yes')
    run('message one', _user='seentest')
    assert run('.seen seentest') == lex.seen.last(text='message one')
    run('.conf keeplogs no')
    run('message two', _user='seentest')
    assert run('.seen seentest') == lex.seen.last(text='message one')


def test_configure_urbandict():
    assert run('.conf urbandict off') == lex.configure.urbandict.false
    assert run('.urban test') == lex.denied


def test_configure_gibber():
    assert run('.conf gibber off') == lex.configure.gibber.false
    assert run('.gib') == lex.denied
