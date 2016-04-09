#!/usr/bin/env python3

###############################################################################
# Module Imports
###############################################################################

import jarvis

###############################################################################

jarvis.notes.init()


def test_tells():
    for i in range(200):
        jarvis.notes.store_tell('test', 'test', i)
    #for i in jarvis.notes.get_tells('test'):
    #    jarvis.notes.store_tell('test', 'test', i)
    assert list(jarvis.notes.get_tells('test'))
    assert not list(jarvis.notes.get_tells('test'))


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
