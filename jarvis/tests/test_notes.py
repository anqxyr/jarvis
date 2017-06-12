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


def test_masstell():
    assert (
        run('.masstell --cc user1 user2 user3 user4 --text MASSTELL',
            _user='masstell_user') ==
        lex.tell.send)
    assert run('.out', _user='masstell_user') == lex.outbound.count(count=4)


def test_masstell_missing_args():
    assert run('.masstell') == lex.masstell.missing_args
    assert run('.masstell --cc name') == lex.masstell.missing_args
    assert run('.masstell --text text') == lex.masstell.missing_args

###############################################################################
# Outbound
###############################################################################


def test_outbound_empty():
    assert run('.out') == lex.outbound.empty


def test_outbound_simple():
    run('.tell user test3')
    assert run('.out') == lex.outbound.count(count=1, users={'user'})


def test_outbound_jinja2():
    str(run('.out'))


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
    assert run('.out') == lex.outbound.count(count=1, users={'user2'})


def test_outbound_purge_case_insensitive():
    assert run('.out -p USER2') == lex.outbound.purged(user='user2')
    assert run('.out') == lex.outbound.empty


###############################################################################
# Seen
###############################################################################


def test_seen_simple():
    run('1', _user='user3')
    assert run('.seen user3') == lex.seen.last(user='user3', text='1')


def test_seen_first():
    run('1', _user='user4')
    run('2', _user='user4')
    assert run('.seen user4 -f') == lex.seen.first(user='user4', text='1')


def test_seen_self():
    assert run('.seen', core.config.irc.nick) == lex.seen.self


def test_seen_case_insensitive():
    assert run('.seen USER') == lex.seen.last(user='user')


def test_seen_total():
    assert run('.seen test-user -t') == lex.seen.total(user='test-user')


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
    assert run('.q 20') == lex.quote.index_error


def test_quote_get_index_negative():
    assert run('.q -4') == lex.quote.not_found


def test_quote_get_user():
    assert run('.q user') == lex.quote.get(user='user', total=4)


def test_quote_get_nonexistent_user():
    assert run('.q user5') == lex.quote.not_found


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


def test_memo_add():
    assert run('.memo add user1 memo1') == lex.memo.saved


def test_memo_add_no_overwrite():
    assert run('.memo add user1 memo2') == lex.memo.already_exists


def test_memo_add_quick():
    assert run('.rem user2 memo2') == lex.memo.saved


def test_memo_get():
    assert run('.memo user1') == lex.memo.get(text='memo1')


def test_memo_get_quick():
    assert run('?user1') == lex.memo.get(text='memo1')


def test_memo_get_case_insensitive():
    assert run('.memo USER1') == lex.memo.get(text='memo1')


def test_memo_get_quick_case_insensitive():
    assert run('?USER1') == lex.memo.get(text='memo1')


def test_memo_add_case_insensitive():
    run('.memo add USER3 memo3')
    assert run('?user3') == lex.memo.get(text='memo3')


def test_memo_append():
    assert run('.memo append user1 part2') == lex.memo.appended
    assert run('?user1') == lex.memo.get(text='memo1 part2')


def test_memo_append_case_insensitive():
    assert run('.MEMO APPEND USER1 part3') == lex.memo.appended
    assert run('?user1') == lex.memo.get(text='memo1 part2 part3')


def test_memo_not_found():
    assert run('?user4') == lex.memo.not_found


def test_memo_delete():
    assert run('.memo del user1') == lex.memo.deleted(text='memo1 part2 part3')
    assert run('?user1') == lex.memo.not_found


def test_memo_delete_not_found():
    assert run('.memo del user5') == lex.memo.not_found


def test_memo_count():
    assert run('.memo count') == lex.memo.count
