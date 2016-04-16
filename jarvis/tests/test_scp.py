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


def inlex(res, *args, **kwargs):
    data = jarvis.lexicon.data
    for i in args:
        data = data[i]
    if kwargs:
        data = [i.format(**kwargs) for i in data]
    return res in data


def test_find_author():
    r = jarvis.scp.find_author(pages, 'anq')
    assert r == jarvis.scp.get_author_summary(pages, 'anqxyr')
    r = jarvis.scp.find_author(pages, 'gears')
    assert inlex(r, 'input', 'options', head='Dr Gears', tail='TwistedGears')
    r = jarvis.tools.recall(2, 'global')
    assert r == jarvis.scp.get_author_summary(pages, 'TwistedGears')
    r = jarvis.scp.find_author(pages, '!!!')
    assert inlex(r, 'not_found', 'author')
    r = jarvis.scp.find_author(pages, None)
    assert inlex(r, 'input', 'incorrect')


def test_update_author_details():
    stwiki = pyscp.wikidot.Wiki('scp-stats')
    stwiki.auth(config['wikiname'], config['wikipass'])
    r = jarvis.scp.update_author_details(pages, 'anqxyr', stwiki)
    assert r == 'http://scp-stats.wikidot.com/user:anqxyr'
    r = jarvis.scp.update_author_details(pages, 'VOCT', stwiki)
    assert r == 'http://scp-stats.wikidot.com/user:voct'
    r = jarvis.scp.update_author_details(pages, 'gears', stwiki)
    inlex(r, 'input', 'options', head='Dr Gears', tail='TwistedGears')
    r = jarvis.tools.recall(1, 'global')
    assert r == 'http://scp-stats.wikidot.com/user:dr-gears'
    r = jarvis.scp.update_author_details(pages, '!!!', stwiki)
    assert inlex(r, 'not_found', 'author')
    r = jarvis.scp.update_author_details(pages, None, stwiki)
    assert inlex(r, 'input', 'incorrect')


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
