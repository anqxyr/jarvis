#!/usr/bin/env python3

###############################################################################
# Module Imports
###############################################################################

import arrow
import jarvis
import uuid

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
        r = jarvis.notes.send_tell('recipient text', 'sender')
        assert inlex(r, 'tell', 'send')
    r = jarvis.notes.get_outbound_tells_count('sender')
    assert inlex(r, 'tell', 'outbound_count', total=200, users='recipient')
    r = jarvis.notes.get_tells('RECIPIENT')
    assert len(r) == 200
    for i in range(50):
        jarvis.notes.send_tell('recipient, text', 'sender')
    r = jarvis.notes.purge_outbound_tells('sender')
    assert inlex(r, 'tell', 'outbound_purged', count=50)
    r = jarvis.notes.purge_outbound_tells('sender')
    assert inlex(r, 'tell', 'outbound_empty')

    r = jarvis.notes.send_tell('!!! text', 'sender')
    assert inlex(r, 'input', 'incorrect')
    r = jarvis.notes.send_tell('', 'sender')
    assert inlex(r, 'input', 'missing')
    assert not jarvis.notes.get_tells('recipient')


def test_seen():
    name = str(uuid.uuid4())
    r = jarvis.notes.get_user_seen(name, 'test-key')
    assert inlex(r, 'seen', 'never')
    time = arrow.utcnow().humanize()
    jarvis.notes.log_message(name, 'test-key', 'test-message')
    r = jarvis.notes.get_user_seen(name, 'test-key')
    assert inlex(r, 'seen', 'last', user=name, time=time, text='test-message')
    r = jarvis.notes.get_user_seen('', 'test-key')
    assert inlex(r, 'input', 'incorrect')


def test_quotes():
    name = str(uuid.uuid4())
    r = jarvis.notes.dispatch_quote(name, 'test-key')
    assert inlex(r, 'quote', 'none_saved')
    r = jarvis.notes.dispatch_quote(
        'add {}      this is a test message   '.format(name), 'test-key')
    assert inlex(r, 'quote', 'saved')
    r = jarvis.notes.dispatch_quote('add {} test #2'.format(name), 'test-key')
    assert inlex(r, 'quote', 'saved')
    r = jarvis.notes.dispatch_quote('add {} test #2'.format(name), 'test-key')
    assert inlex(r, 'quote', 'already_exists')
    r = jarvis.notes.dispatch_quote('{}   2'.format(name), 'test-key')
    assert r == '[2/2] {:YYYY-MM-DD} {}: test #2'.format(arrow.now(), name)
    r = jarvis.notes.dispatch_quote('{} -1'.format(name), 'test-key')
    assert inlex(r, 'input', 'bad_index')
    r = jarvis.notes.dispatch_quote('{} gibberish'.format(name), 'test-key')
    assert inlex(r, 'input', 'bad_index')
    r = jarvis.notes.dispatch_quote('del {} test #2'.format(name), 'test-key')
    assert inlex(r, 'quote', 'deleted')
    r = jarvis.notes.dispatch_quote('del {} test #2'.format(name), 'test-key')
    assert inlex(r, 'quote', 'not_found')
