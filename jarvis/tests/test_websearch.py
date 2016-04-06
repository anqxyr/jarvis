#!/usr/bin/env python3

###############################################################################
# Module Imports
###############################################################################

import pytest
import jarvis

###############################################################################

config = {}
with open('/home/anqxyr/.sopel/default.cfg') as file:
    for line in file:
        if '=' not in line:
            continue
        key, value = apikey = line.split('=')
        config[key.strip()] = value.strip()


def test_google_search():
    jarvis.websearch.google_search(
        config['apikey'], config['cseid'], 'test search string')
    jarvis.websearch.google_search(config['apikey'], config['cseid'], None)


def test_google_image_search():
    jarvis.websearch.google_image_search(
        config['apikey'], config['cseid'], 'Kittens on Drugs')


def test_youtube_search():
    jarvis.websearch.youtube_search(config['apikey'], 'I like trains')


def test_youtube_video_info():
    jarvis.websearch.youtube_video_info(config['apikey'], 'llIAae61QHk')
    jarvis.websearch.youtube_video_info(config['apikey'], 'j46utX3dJlM')


def test_wikipedia_search():
    jarvis.websearch.wikipedia_search('Ants')
    jarvis.websearch.wikipedia_search('Mercury')
    jarvis.websearch.wikipedia_search('glabberbock')
    jarvis.websearch.wikipedia_search('')
    jarvis.websearch.wikipedia_search(None)


def test_dictionary_search():
    jarvis.websearch.dictionary_search('door')
    jarvis.websearch.dictionary_search('find')
    jarvis.websearch.dictionary_search('BuggyMcBugword')
    jarvis.websearch.dictionary_search('')
    jarvis.websearch.dictionary_search(None)
