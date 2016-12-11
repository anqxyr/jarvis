#!/usr/bin/env python3
"""Test jarvis.tools module."""

###############################################################################
# Module Imports
###############################################################################

import uuid

from jarvis import tools, lex, core
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


###############################################################################
# Twitter
###############################################################################


def test_twitter_get_new_article():
    page = tools._get_new_article(core.pages)
    if not page:
        return
    assert 'scp' in page.tags or 'tale' in page.tags
    if 'scp' in page.tags:
        assert page.rating >= 40
    if 'tale' in page.tags:
        assert page.rating >= 20


def test_twitter_get_old_article():
    page = tools._get_old_article(core.pages)
    if not page:
        return
    assert 'scp' in page.tags or 'tale' in page.tags
    if 'scp' in page.tags:
        assert page.rating >= 120
    if 'tale' in page.tags:
        assert page.rating >= 60


def test_twitter_post_tweet():
    uuid_text = str(uuid.uuid4())
    api = tools._get_twitter_api()

    api.update_status(uuid_text)
    tweet = api.user_timeline(count=5)[0]
    assert tweet.text == uuid_text


def test_post_on_twitter():
    tools.post_on_twitter()


def test_updatehelp():
    result = run('.updatehelp')
    assert result == lex.updatehelp.finished
    assert str(result)
