#!/usr/bin/env python3

###############################################################################
# Module Imports
###############################################################################

import jarvis

###############################################################################


def inlex(res, *args, **kwargs):
    data = jarvis.lexicon.data
    for i in args:
        data = data[i]
    if kwargs:
        data = [i.format(**kwargs) for i in data]
    return res in data


def test_remember_and_recall():
    r = jarvis.tools.recall(1, 'test-key')
    assert inlex(r, 'not_found', 'generic')
    jarvis.tools.remember([1, 2, 3], 'test-key')
    r = jarvis.tools.recall(1, 'test-key')
    assert r == 1
    r = jarvis.tools.recall(' 2  ', 'test-key')
    assert r == 2
    r = jarvis.tools.recall(0, 'test-key')
    assert inlex(r, 'input', 'bad_index')
    r = jarvis.tools.recall(20, 'test-key')
    assert inlex(r, 'input', 'bad_index')
    r = jarvis.tools.recall(None, 'test-key')
    assert inlex(r, 'input', 'bad_index')
    r = jarvis.tools.recall('buggy_string_index', 'test-key')
    assert inlex(r, 'input', 'bad_index')


def test_choose():
    r = jarvis.tools.choose('yellow, green, red')
    assert r in {'yellow', 'green', 'red'}
    r = jarvis.tools.choose('yellow')
    assert r == 'yellow'
    r = jarvis.tools.choose('yellow, ,red')
    assert r in {'yellow', 'red'}
    r = jarvis.tools.choose(None)
    assert inlex(r, 'input', 'missing')


def test_roll_dice():
    r = jarvis.tools.roll_dice('d10')
    assert 1 <= int(r.split()[0]) <= 10

    r = jarvis.tools.roll_dice('10df')
    assert -10 <= int(r.split()[0]) <= 10

    r = jarvis.tools.roll_dice('2d5+40')
    assert 42 <= int(r.split()[0]) <= 50

    r = jarvis.tools.roll_dice('2d1000-400d50')
    assert -19998 <= int(r.split()[0]) <= 1600

    jarvis.tools.roll_dice('10000d5')
    jarvis.tools.roll_dice('5d0')
    jarvis.tools.roll_dice('0d5')
    jarvis.tools.roll_dice('2d5**5')
    jarvis.tools.roll_dice('here are some words for you')
    jarvis.tools.roll_dice(None)
