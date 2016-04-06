#!/usr/bin/env python3

###############################################################################
# Module Imports
###############################################################################

import pytest
import jarvis

###############################################################################


def test_remember_and_recall():
    jarvis.tools.recall(1, 'test')
    jarvis.tools.remember([1, 2, 3], 'test')
    jarvis.tools.recall(1, 'test')
    jarvis.tools.recall(' 2  ', 'test')
    jarvis.tools.recall(0, 'test')
    jarvis.tools.recall(20, 'test')
    jarvis.tools.recall(None, 'test')
    jarvis.tools.recall(1, 'test')
    jarvis.tools.recall(1, 'blah')
    jarvis.tools.recall('buggy_string_index', 'test')


def test_choose():
    jarvis.tools.choose('yellow, green, red')
    jarvis.tools.choose('yellow')
    jarvis.tools.choose('yellow, ,red')
    jarvis.tools.choose(None)


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
