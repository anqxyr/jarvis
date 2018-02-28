#!/usr/bin/env python3
"""Test jarvis.websearch module."""

###############################################################################
# Module Imports
###############################################################################


from jarvis import lex
from jarvis.tests.utils import run


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


def test_duckduckgo_simpe():
    assert run('.ddg scp wiki') == lex.duckduckgo.result(index=1)


def test_duckduckgo_index():
    assert run('.ddg scp-wiki -i 5') == lex.duckduckgo.result(index=5)


def test_duckduckgo_index_error():
    assert run('.ddg scp-wiki -i 100') == lex.generics.index_error


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

###############################################################################
#
###############################################################################


def test_kaktuskast_default():
    assert run('.kk') == [
        lex.kaktuskast.short, lex.kaktuskast.short, lex.kaktuskast.short]


def test_kaktuskast_index():
    assert run('.kk 25') == [
        lex.kaktuskast.short(title='The KaktusKast Ep. 25 - 3000Kast'),
        lex.kaktuskast.text]


def test_kaktuskast_index_error():
    assert run('.kk 4002') == lex.kaktuskast.index_error


def test_kaktuskast_podcast_not_found():
    assert run('.kk blahblah') == lex.kaktuskast.podcast_not_found


def test_kaktuskast_podcast():
    assert run('.kk crit 1') == [
        lex.kaktuskast.short(date='2017-07-25'), lex.kaktuskast.text]


def test_kaktuskast_foundation():
    assert run('.kk foundation 1')


def test_kaktuskast_ttrimmd():
    assert run('.kk trim 10') == [
        lex.kaktuskast.short(date='2017-07-22'), lex.kaktuskast.text]


def test_kaktuskast_title():
    assert run('.kk thing 5') == [lex.kaktuskast.short, lex.kaktuskast.text]


def test_kaktuskast_sm():
    run('.kk')
    assert run('.sm 1') == lex.kaktuskast.long
