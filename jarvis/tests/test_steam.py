#!/usr/bin/env python3

###############################################################################
# Module Imports
###############################################################################


from jarvis import lex
from jarvis.tests.utils import run

###############################################################################


def test_steam_lookup_simple():
    assert (
        run('http://store.steampowered.com/app/418150') ==
        lex.steam.result(name='The Madness of Little Emma'))


def test_steam_lookup_not_found():
    assert (
        run('http://store.steampowered.com/app/999999999999') ==
        lex.steam.not_found)


def test_steam_simple():
    assert run('.steam terraria') == lex.steam.result(name='Terraria')


def test_steam_no_price():
    assert str(run('.steam little emma demo'))


def test_steam_no_genre():
    assert str(run('.steam magic the gathering'))


def test_steam_superhot():
    # this weird bug happens in cycles, every 3rd or so result is correct
    # so we'll check the output 3 times to make sure
    url = 'http://store.steampowered.com/app/322500'
    for _ in range(3):
        assert url in str(run('.steam superhot'))
