#!/usr/bin/env python3

###############################################################################
# Module Imports
###############################################################################


from jarvis import core, lex
from jarvis.tests.utils import run

###############################################################################


def test_seen_simple():
    run('1', _user='user')
    assert run('.seen user') == lex.seen.last(user='user', text='1')


def test_seen_first():
    run('1', _user='user2')
    run('2', _user='user2')
    assert run('.seen user2 -f') == lex.seen.first(user='user2', text='1')


def test_seen_self():
    assert run('.seen', core.config.irc.nick) == lex.seen.self


def test_seen_case_insensitive():
    assert run('.seen USER') == lex.seen.last(user='user')


def test_seen_total():
    assert run('.seen user -t') == lex.seen.total(user='user')


def test_seen_never():
    assert run('.seen -') == lex.seen.never
