#!/usr/bin/env python3

###############################################################################
# Module Imports
###############################################################################

import pyscp
import jarvis

###############################################################################


wiki = pyscp.wikidot.Wiki('scp-wiki')

pages = jarvis.ext.PageView(list(wiki.list_pages(
    body='title created_by created_at rating tags')))

config = {}
with open('/home/anqxyr/.sopel/default.cfg') as file:
    for line in file:
        if '=' not in line:
            continue
        key, value = apikey = line.split('=')
        config[key.strip()] = value.strip()


def test_find_author():
    # trying to validate the output is too hard, it's better done by hand
    # so this and other tests here will just call the functions with various
    # arguments and make sure they don't throw exceptions anywhere
    jarvis.scp.find_author(pages, 'anqxyr')
    jarvis.scp.find_author(pages, 'voct')
    jarvis.scp.find_author(pages, 'roget')
    jarvis.scp.find_author(pages, 'gears')  # ambiguous
    jarvis.tools.recall(1, 'global')
    jarvis.scp.find_author(pages, 'dr')
    jarvis.scp.find_author(pages, 'author does not exist')
    jarvis.scp.find_author(pages, '')
    jarvis.scp.find_author(pages, None)


def test_update_author_details():
    stwiki = pyscp.wikidot.Wiki('scp-stats')
    stwiki.auth(config['wikiname'], config['wikipass'])
    jarvis.scp.update_author_details(pages, 'anqxyr', stwiki)
    jarvis.scp.update_author_details(pages, 'voct', stwiki)
    jarvis.scp.update_author_details(pages, 'gears', stwiki)
    jarvis.tools.recall(1, 'global')
    jarvis.scp.update_author_details(pages, 'author does not exist', stwiki)
    jarvis.scp.update_author_details(pages, None, stwiki)


def test_find_page():
    jarvis.scp.find_page(pages, 'routine')
    jarvis.scp.find_page(pages, 'scp-')
    jarvis.scp.find_page(pages, 'белки')
    jarvis.scp.find_page(pages, 'paradise mobile')
    jarvis.scp.find_page(pages, '')
    jarvis.scp.find_page(pages, None)


def test_find_scp():
    jarvis.scp.find_scp(pages, 'clown')
    jarvis.scp.find_scp(pages, 'quiet days')
    jarvis.scp.find_scp(pages, '0')


def test_find_tale():
    jarvis.scp.find_tale(pages, '173')
    jarvis.scp.find_tale(pages, 'scp-')
    jarvis.scp.find_tale(pages, 'Kitten Flu')


def test_find_tags():
    jarvis.scp.find_tags(pages, 'keter temporal')
    jarvis.scp.find_tags(pages, 'safe keter')
    jarvis.scp.find_tags(pages, 'blahblahblah')
    jarvis.scp.find_tags(pages, '')
    jarvis.scp.find_tags(pages, None)


def test_error_report():
    jarvis.scp.get_error_report(pages)
