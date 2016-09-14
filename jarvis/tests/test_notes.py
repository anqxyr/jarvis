#!/usr/bin/env python3
"""Test jarvis.notes module."""

###############################################################################
# Module Imports
###############################################################################

from jarvis import core, notes, parser, lex
from jarvis.tests.utils import run

###############################################################################


###############################################################################
# Tell
###############################################################################


def test_tell_send():
    assert run('!tell user test1') == lex.tell.send


def test_tell_receive():
    assert run('-', _user='user') == [
        lex.tell.new(count=1),
        lex.tell.get(name='test-user', time='just now', text='test1')]


def test_tell_no_new_tells():
    assert not run('-')


def test_tell_case_insensitive():
    run('!tell USERNAME test2')
    assert run('-', _user='Username') == [
        lex.tell.new(count=1),
        lex.tell.get(name='test-user', time='just now', text='test2')]


def test_tell_multiple():
    for i in range(50):
        run('!tell user test number', i)
    tells = run('-', _user='user')
    assert tells[0] == lex.tell.new(count=50)
    assert tells[1:] == [
        lex.tell.get(
            name='test-user',
            time='just now',
            text='test number ' + str(i))
        for i in range(50)]


###############################################################################
# Outbound
###############################################################################


