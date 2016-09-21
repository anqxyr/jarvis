#!/usr/bin/env python3
"""Test jarvis.tools module."""

###############################################################################
# Module Imports
###############################################################################


from jarvis import tools, lex
from jarvis.tests.utils import run


###############################################################################
# Showmore
###############################################################################


###############################################################################
# Choose
###############################################################################


###############################################################################
# Dice
###############################################################################


def test_dice_simple():
    assert run('.dice 2d4') == lex.dice.output.simple


def test_dice_implied_count():
    assert run('.dice d10') == lex.dice.output.simple


def test_dice_multiple():
    assert run('.dice 2d4 3d6 d20') == lex.dice.output.simple


def test_dice_negative():
    assert run('.dice 2d10 -4d5') == lex.dice.output.simple


def test_dice_one_side():
    assert run('.dice 5d1') == lex.dice.bad_side_count


def test_dice_zero_sides():
    assert run('.dice 2d0') == lex.dice.bad_side_count


def test_dice_too_many_dice():
    assert run('.dice 1000000d10') == lex.dice.too_many_dice


def test_dice_too_many_sides():
    assert run('.roll 10d99999') == lex.dice.bad_side_count


def test_dice_bonus():
    assert run('.dice 2d10 100') == lex.dice.output.simple


def test_dice_bonus_negative():
    assert run('.dice 5d20 -200') == lex.dice.output.simple


def test_dice_fudge():
    assert run('.dice 5df') == lex.dice.output.simple


def test_dice_tail_garbage():
    assert run('.roll 5d5d5') == tools.dice._parser.usage('dice')


###############################################################################
# Misc
###############################################################################
