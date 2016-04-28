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
    r = jarvis.scp.find_author('anq', 'test-channel')
    assert r == jarvis.scp.author_summary(pages, 'anqxyr')
    r = jarvis.scp.find_author('gears', 'test-channel')
    assert inlex(
        r, 'input', 'options',
        head='\x02Dr Gears\x02', tail='\x02TwistedGears\x02')
    r = jarvis.tools.recall(2, 'test-channel')
    assert r == jarvis.scp.author_summary('TwistedGears')
    r = jarvis.scp.find_author('!!!', 'test-channel')
    assert inlex(r, 'not_found', 'author')
    r = jarvis.scp.find_author(None, 'test-channel')
    assert inlex(r, 'input', 'missing')


def test_update_author_details():
    r = jarvis.scp.update_author_details('anqxyr', 'test-channel')
    assert r == 'http://scp-stats.wikidot.com/user:anqxyr'
    r = jarvis.scp.update_author_details('VOCT', 'test-channel')
    assert r == 'http://scp-stats.wikidot.com/user:voct'
    r = jarvis.scp.update_author_details('gears', 'test-channel')
    inlex(
        r, 'input', 'options',
        head='\x02Dr Gears\x02', tail='\x02TwistedGears\x02')
    r = jarvis.tools.recall(1, 'test-channel')
    assert r == 'http://scp-stats.wikidot.com/user:dr-gears'
    r = jarvis.scp.update_author_details('!!!', 'test-channel')
    assert inlex(r, 'not_found', 'author')
    r = jarvis.scp.update_author_details(None, 'test-channel')
    assert inlex(r, 'input', 'missing')


def test_find_page_by_title():
    jarvis.scp.find_page_by_title('routine', 'test-channel')
    jarvis.scp.find_page_by_title('scp-', 'test-channel')
    jarvis.scp.find_page_by_title('белки', 'test-channel')
    jarvis.scp.find_page_by_title('paradise mobile', 'test-channel')
    jarvis.scp.find_page_by_title('', 'test-channel')
    jarvis.scp.find_page_by_title(None, 'test-channel')


def test_find_tale():
    jarvis.scp.find_tale_by_title('173', 'test-channel')
    jarvis.scp.find_tale_by_title('scp-', 'test-channel')
    jarvis.scp.find_tale_by_title('Kitten Flu', 'test-channel')


def test_find_page_by_tags():
    jarvis.scp.find_page_by_tags('keter temporal', 'test-channel')
    jarvis.scp.find_page_by_tags('safe keter', 'test-channel')
    jarvis.scp.find_page_by_tags('blahblahblah', 'test-channel')
    jarvis.scp.find_page_by_tags('', 'test-channel')
    jarvis.scp.find_page_by_tags(None, 'test-channel')


def test_error_report():
    jarvis.scp.get_error_report()
