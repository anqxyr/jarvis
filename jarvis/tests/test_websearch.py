#!/usr/bin/env python3
"""Test jarvis.websearch module."""

###############################################################################
# Module Imports
###############################################################################


from jarvis import lex
from jarvis.tests.utils import run


###############################################################################


def test_wikipedia_simple():
    assert run('.w music') == lex.wikipedia.result(title='Music')


def test_wikipedia_ambiguous():
    assert run('.w mercury') == lex.unclear


def test_wikipedia_not_found():
    assert run('.w sdfgdhfghe') == lex.wikipedia.not_found


def test_wikipedia_bracket_escaping():
    assert str(run('.w probability field'))

###############################################################################


def test_youtube_search_simple():
    assert run('.y I like trains') == lex.youtube.result(
        video_id='hHkKJfcBXcw')


def test_youtube_mssing_likes():
    assert (
        run('https://www.youtube.com/watch?v=llIAae61QHk') ==
        lex.youtube.result(title='Защитники - Официальный тизер!'))


def test_youtube_curly_braces():
    assert str(run('https://www.youtube.com/watch?v=DNNOeEDB19E'))


def test_youtube_whatever():
    assert str(run('https://www.youtube.com/watch?v=T1Hklvc-vx0'))

###############################################################################


def test_translate_simple():
    assert (
        run('.trans en-ru teapot') == lex.translate.result(text=['чайничек']))


def test_translate_detect_language():
    assert run('.trans en белочки') == lex.translate.result(text=['squirrels'])


def test_translate_garbage_text():
    assert run('.trans en-ru gsjdhfgsjld') == lex.translate.result


def test_translate_garbage_lang():
    assert run('.trans 1011-en text in robot language') == lex.translate.error


###############################################################################


def test_imdb_simple():
    assert run('.imdb watchmen') == lex.imdb.result(imdbid='tt0409459')


def test_imdb_year():
    assert (
        run('.imdb avengers -y 2015') ==
        lex.imdb.result(title='Avengers: Age of Ultron'))


def test_imdb_search():
    assert run('.imdb -s avengers') == lex.unclear


def test_imdb_not_found():
    assert run('.imdb whatever -y 2100') == lex.imdb.not_found


def test_imdb_showmore():
    run('.imdb -s star wars')
    assert run('.sm 1') == lex.imdb.result(year='1977')

###############################################################################


def test_duckduckgo_simpe():
    assert run('.ddg scp wiki') == lex.duckduckgo.result(index=1)


def test_duckduckgo_index():
    assert run('.ddg scp-wiki -i 5') == lex.duckduckgo.result(index=5)


def test_duckduckgo_bad_index():
    assert run('.ddg scp-wiki -i 100') == lex.index_out_of_range


def test_duckduckgo_showmore():
    run('.ddg scp-wiki')
    assert run('.sm 8') == lex.duckduckgo.result(index=8)


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


###############################################################################


def test_twitter_lookup_simple():
    assert (
        run('https://twitter.com/MeetAnimals/status/778453962970107904') ==
        lex.twitter_lookup(name='Animal Life'))


def test_twitter_lookup_linebreaks():
    assert (
        run('https://twitter.com/TwitterForNews/status/311909802462822400') ==
        lex.twitter_lookup(text='L I N E  B R E A K S  #newattwitter'))
