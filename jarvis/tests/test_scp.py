#!/usr/bin/env python3

###############################################################################
# Module Imports
###############################################################################

from jarvis import scp, lex, tools
from jarvis.tests.utils import run

###############################################################################


def test_author_simple():
    # the call to scp here is a code smell
    # run results should be always compared to lex objects directly
    # if they can't be, it means the output is too complicated
    assert run('.au anq') == scp.author_summary('anqxyr')


def test_author_ambiguous():
    assert run('.au gears') == tools.choose_input(['Dr Gears', 'TwistedGears'])


def test_author_not_found():
    assert run('.au fakeauthorname') == lex.not_found.author



#def test_update_author_details():
#    r = jarvis.scp.update_author_details('anqxyr', 'test-channel')
#    assert r == 'http://scp-stats.wikidot.com/user:anqxyr'
#    r = jarvis.scp.update_author_details('VOCT', 'test-channel')
#    assert r == 'http://scp-stats.wikidot.com/user:voct'
#    r = jarvis.scp.update_author_details('gears', 'test-channel')
#    inlex(
#        r, 'input', 'options',
#        head='\x02Dr Gears\x02', tail='\x02TwistedGears\x02')
#    r = jarvis.tools.recall(1, 'test-channel')
#    assert r == 'http://scp-stats.wikidot.com/user:dr-gears'
#    r = jarvis.scp.update_author_details('!!!', 'test-channel')
#    assert inlex(r, 'not_found', 'author')
#    r = jarvis.scp.update_author_details(None, 'test-channel')
#    assert inlex(r, 'input', 'missing')


#def test_find_page_by_title():
#    jarvis.scp.find_page_by_title('routine', 'test-channel')
#    jarvis.scp.find_page_by_title('scp-', 'test-channel')
#    jarvis.scp.find_page_by_title('белки', 'test-channel')
#    jarvis.scp.find_page_by_title('paradise mobile', 'test-channel')
#    jarvis.scp.find_page_by_title('', 'test-channel')
#    jarvis.scp.find_page_by_title(None, 'test-channel')


#def test_find_tale():
#    jarvis.scp.find_tale_by_title('173', 'test-channel')
#    jarvis.scp.find_tale_by_title('scp-', 'test-channel')
#    jarvis.scp.find_tale_by_title('Kitten Flu', 'test-channel')


#def test_find_page_by_tags():
#    jarvis.scp.find_page_by_tags('keter temporal', 'test-channel')
#    jarvis.scp.find_page_by_tags('safe keter', 'test-channel')
#    jarvis.scp.find_page_by_tags('blahblahblah', 'test-channel')
#    jarvis.scp.find_page_by_tags('', 'test-channel')
#    jarvis.scp.find_page_by_tags(None, 'test-channel')


#def test_error_report():
#    jarvis.scp.get_error_report()
