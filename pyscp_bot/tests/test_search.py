#!/usr/bin/env python3

###############################################################################
# Module Imports
###############################################################################

import pytest
import pyscp_bot as pbot

###############################################################################

config = {}
with open('/home/anqxyr/.sopel/default.cfg') as file:
    for line in file:
        if '=' not in line:
            continue
        key, value = apikey = line.split('=')
        config[key.strip()] = value.strip()


def test_youtube_search():
    r = pbot.search.youtube_search(config['apikey'], 'I like trains')
    assert r.startswith('\x02I LIKE TRAINS (asdfmovie song)\x02')
    assert r.endswith('youtube.com/watch?v=hHkKJfcBXcw')


def test_youtube_video_info():
    assert pbot.search.youtube_video_info(config['apikey'], 'llIAae61QHk')
    assert pbot.search.youtube_video_info(config['apikey'], 'j46utX3dJlM')


def test_wikipedia_search():
    r = pbot.search.wikipedia_search('Ants')
    assert r.startswith('Ants are eusocial insects of the family Formicidae')
    assert r.endswith('wikipedia.org/wiki/Ant\x02')

    assert pbot.search.wikipedia_search('Mercury')
    assert pbot.search.wikipedia_search('glabberbock')


def test_dictionary_search():
    r = pbot.search.dictionary_search('door')
    assert '\n' not in r

    r = pbot.search.dictionary_search('find')
    assert '\n' not in r
    assert r.endswith('.')
