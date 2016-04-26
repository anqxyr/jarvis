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
    r = jarvis.scp.find_author(pages, 'anq', 'test-channel')
    assert r == jarvis.scp.author_summary(pages, 'anqxyr')
    r = jarvis.scp.find_author(pages, 'gears', 'test-channel')
    assert inlex(
        r, 'input', 'options',
        head='\x02Dr Gears\x02', tail='\x02TwistedGears\x02')
    r = jarvis.tools.recall(2, 'test-channel')
    assert r == jarvis.scp.author_summary(
        pages, 'TwistedGears')
    r = jarvis.scp.find_author(pages, '!!!', 'test-channel')
    assert inlex(r, 'not_found', 'author')
    r = jarvis.scp.find_author(pages, None, 'test-channel')
    assert inlex(r, 'input', 'missing')


def test_update_author_details():
    stwiki = pyscp.wikidot.Wiki('scp-stats')
    stwiki.auth(config['wikiname'], config['wikipass'])
    r = jarvis.scp.update_author_details(
        pages, 'anqxyr', 'test-channel', stwiki)
    assert r == 'http://scp-stats.wikidot.com/user:anqxyr'
    r = jarvis.scp.update_author_details(
        pages, 'VOCT', 'test-channel', stwiki)
    assert r == 'http://scp-stats.wikidot.com/user:voct'
    r = jarvis.scp.update_author_details(
        pages, 'gears', 'test-channel', stwiki)
    inlex(
        r, 'input', 'options',
        head='\x02Dr Gears\x02', tail='\x02TwistedGears\x02')
    r = jarvis.tools.recall(1, 'test-channel')
    assert r == 'http://scp-stats.wikidot.com/user:dr-gears'
    r = jarvis.scp.update_author_details(pages, '!!!', 'test-channel', stwiki)
    assert inlex(r, 'not_found', 'author')
    r = jarvis.scp.update_author_details(pages, None, 'test-channel', stwiki)
    assert inlex(r, 'input', 'missing')


def test_find_page_by_title():
    jarvis.scp.find_page_by_title(pages, 'routine', 'test-channel')
    jarvis.scp.find_page_by_title(pages, 'scp-', 'test-channel')
    jarvis.scp.find_page_by_title(pages, 'белки', 'test-channel')
    jarvis.scp.find_page_by_title(pages, 'paradise mobile', 'test-channel')
    jarvis.scp.find_page_by_title(pages, '', 'test-channel')
    jarvis.scp.find_page_by_title(pages, None, 'test-channel')


def test_find_tale():
    jarvis.scp.find_tale_by_title(pages, '173', 'test-channel')
    jarvis.scp.find_tale_by_title(pages, 'scp-', 'test-channel')
    jarvis.scp.find_tale_by_title(pages, 'Kitten Flu', 'test-channel')


def test_find_page_by_tags():
    jarvis.scp.find_page_by_tags(pages, 'keter temporal', 'test-channel')
    jarvis.scp.find_page_by_tags(pages, 'safe keter', 'test-channel')
    jarvis.scp.find_page_by_tags(pages, 'blahblahblah', 'test-channel')
    jarvis.scp.find_page_by_tags(pages, '', 'test-channel')
    jarvis.scp.find_page_by_tags(pages, None, 'test-channel')


def test_error_report():
    jarvis.scp.get_error_report(pages)
