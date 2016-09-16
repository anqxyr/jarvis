#!/usr/bin/env python3
"""Test jarvis.notes module."""

###############################################################################
# Module Imports
###############################################################################


from jarvis import core, lex
from jarvis.tests.utils import run


###############################################################################
# Tell
###############################################################################


def test_tell_send():
    assert run('!tell user test1') == lex.tell.send


def test_tell_receive():
    assert run('-', _user='user') == [
        lex.tell.new(count=1),
        lex.tell.get(name='test-user', text='test1')]


def test_tell_no_new_tells():
    assert not run('-')


def test_tell_case_insensitive():
    run('!tell USERNAME test2')
    assert run('-', _user='Username') == [
        lex.tell.new(count=1),
        lex.tell.get(name='test-user', text='test2')]


def test_tell_multiple():
    for i in range(50):
        run('!tell user test number', i)
    tells = run('-', _user='user')
    assert tells[0] == lex.tell.new(count=50)
    assert tells[1:] == [lex.tell.get for _ in range(50)]


def test_showtells_no_new():
    assert run('.st') == lex.tell.no_new


def test_showtells_have_tells():
    run('.tell user st1')
    run('.tell user st2')
    run('.tell user st3')
    assert run('.st', _user='user') == [
        lex.tell.new(count=3),
        lex.tell.get(text='st1'),
        lex.tell.get(text='st2'),
        lex.tell.get(text='st3')]


###############################################################################
# Outbound
###############################################################################


def test_outbound_empty():
    assert run('.out') == lex.outbound.empty


def test_outbound_simple():
    run('.tell user test3')
    assert run('.out') == lex.outbound.count(count=1, users='user')


def test_outbound_echo_one():
    assert run('.out -e') == lex.outbound.echo(user='user', message='test3')


def test_outbound_echo_multiple():
    run('.tell user2 test4')
    assert run('.out -e') == [
        lex.outbound.echo(user='user', message='test3'),
        lex.outbound.echo(user='user2', message='test4')]


def test_outbound_purge_all():
    assert run('.out -p') == lex.outbound.purged
    assert run('.out') == lex.outbound.empty


def test_outbound_purge_one():
    run('.tell user test5')
    run('.tell user2 test6')
    assert run('.out -p user') == lex.outbound.purged(user='user')
    assert run('.out') == lex.outbound.count(count=1, users='user2')


def test_outbound_purge_case_insensitive():
    assert run('.out -p USER2') == lex.outbound.purged(user='user2')
    assert run('.out') == lex.outbound.empty


###############################################################################
# Seen
###############################################################################


def test_seen_simple():
    assert run('.seen user') == lex.seen.last(user='user', text='.st')


def test_seen_first():
    assert run('.seen test-user -f') == lex.seen.first(
        user='test-user', text='!tell user test1')


def test_seen_self():
    assert run('.seen', core.config.irc.nick) == lex.seen.self


def test_seen_case_insensitive():
    assert run('.seen USER') == lex.seen.last(user='user', text='.st')


def test_seen_total():
    assert run('.seen test-user -t') == lex.seen.total(
        user='test-user', total=75)


def test_seen_never():
    assert run('.seen -') == lex.seen.never

###############################################################################
# Quote
###############################################################################


def test_quote_add():
    assert run('.q add user quote1') == lex.quote.added
    assert run('.q add user quote2') == lex.quote.added
    assert run('.q add user quote3') == lex.quote.added
    assert run('.q add user quote4') == lex.quote.added
    assert run('.q add user2 quote5') == lex.quote.added
    assert run('.q add user2 quote6') == lex.quote.added


def test_quote_already_exists():
    assert run('.q add user quote1') == lex.quote.already_exists


def test_quote_add_date():
    assert run('.q add 2020-01-01 user3 quote7') == lex.quote.added


def test_quote_add_cross_channel():
    assert run(
        '.q #chan2 add user3 quote8',
        _channels=['#chan2']) == lex.quote.added


def test_quote_add_numeric_username():
    assert run('.q add 100 quote9') == lex.quote.added


def test_quote_get_simple():
    assert run('.q') == lex.quote.get


def test_quote_get_index():
    assert run('.q 4') == lex.quote.get(text='quote4')


def test_quote_get_index_too_big():
    assert run('.q 20') == lex.input.bad_index


def test_quote_get_index_negative():
    assert run('.q -4') == lex.quote.none_saved


def test_quote_get_user():
    assert run('.q user') == lex.quote.get(user='user', total=4)


def test_quote_get_nonexistent_user():
    assert run('.q user5') == lex.quote.none_saved


def test_quote_get_user_and_index():
    assert run('.q user2 2') == lex.quote.get(text='quote6')


def test_quote_get_user_case_insensitive():
    assert run('.q USER 3') == lex.quote.get(text='quote3')


def test_quote_get_cross_channel():
    assert run(
        '.q #chan2', _channels=['#chan2']) == lex.quote.get(text='quote8')


###############################################################################
# Memos
###############################################################################
