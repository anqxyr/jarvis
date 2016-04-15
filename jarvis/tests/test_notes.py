#!/usr/bin/env python3

###############################################################################
# Module Imports
###############################################################################

import jarvis

###############################################################################

jarvis.notes.init()


def inlex(res, *args, **kwargs):
    data = jarvis.lexicon.data
    for i in args:
        data = data[i]
    if kwargs:
        data = [i.format(**kwargs) for i in data]
    return res in data


def test_tells():
    jarvis.notes.purge_outbound_tells('sender')
    for i in range(200):
        r = jarvis.notes.send_tell('sender', 'recipient', 'text')
        assert inlex(r, 'tell', 'send')
    r = jarvis.notes.get_outbound_tells_count('sender')
    assert inlex(r, 'tell', 'outbound_count', total=200, users='recipient')
    r = jarvis.notes.get_tells('RECIPIENT')
    assert len(r) == 200
    for i in range(50):
        jarvis.notes.send_tell('sender', 'recipient', 'text')
    r = jarvis.notes.purge_outbound_tells('sender')
    assert inlex(r, 'tell', 'outbound_purged', count=50)
    r = jarvis.notes.purge_outbound_tells('sender')
    assert inlex(r, 'tell', 'outbound_empty')

    r = jarvis.notes.send_tell('sender', '!!!', 'text')
    assert inlex(r, 'bad_input')
    r = jarvis.notes.send_tell('sender', 'recipient', '')
    assert inlex(r, 'bad_input')
    r = jarvis.notes.send_tell('sender', None, None)
    assert inlex(r, 'bad_input')
    assert not jarvis.notes.get_tells('recipient')


def test_seen():
    jarvis.notes.user_last_seen('test', 'test')
    jarvis.notes.log_message('test', 'test', 'test-message')
    jarvis.notes.user_last_seen('test', 'test')


def test_quotes():
    jarvis.notes.quote('test', 'test')
    jarvis.notes.quote('test 2', 'test')
    jarvis.notes.quote('test blah', 'test')
    jarvis.notes.quote('del test blah', 'test')
    for i in range(200):
        jarvis.notes.quote('add test ' + str(i), 'test')
    jarvis.notes.quote('del test 35', 'test')
    jarvis.notes.quote('test', 'test')
    jarvis.notes.quote('test 80', 'test')
