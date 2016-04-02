#!/usr/bin/env python3

###############################################################################
# Module Imports
###############################################################################

import pytest
import pyscp_bot as pbot

###############################################################################


def test_choose():
    r = pbot.tools.choose('yellow, green, red')
    assert r in ['yellow', 'green', 'red']


def test_roll_dice():
    r = pbot.tools.roll_dice('d10')
    assert 1 <= int(r.split()[0]) <= 10

    r = pbot.tools.roll_dice('10df')
    assert -10 <= int(r.split()[0]) <= 10

    r = pbot.tools.roll_dice('2d5+40')
    assert 42 <= int(r.split()[0]) <= 50

    r = pbot.tools.roll_dice('2d1000-400d50')
    assert -19998 <= int(r.split()[0]) <= 1600

