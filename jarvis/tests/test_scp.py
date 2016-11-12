#!/usr/bin/env python3

###############################################################################
# Module Imports
###############################################################################

from jarvis import core, scp, lex, tools
from jarvis.tests.utils import run, samples, page

###############################################################################
# Author
###############################################################################


def test_author_simple():
    # the call to scp here is a code smell
    # run results should be always compared to lex objects directly
    # if they can't be, it means the output is too complicated
    assert run('.au anq') == lex.summary.author(name='anqxyr')


def test_author_ambiguous():
    assert run('.au gears') == tools.choose_input(['Dr Gears', 'TwistedGears'])


def test_author_not_found():
    assert run('.au fakeauthorname') == lex.not_found.author


def test_author_default():
    assert run('.au', _user='anqxyr') == lex.summary.author(name='anqxyr')


def test_author_showmore():
    run('.au Jack')
    assert run('.sm 3') == lex.summary.author


###############################################################################


def test_authordetails_showmore():
    run('.ad Jack')
    assert run('.sm 3')


###############################################################################
# Misc
###############################################################################


def test_scp_lookup_simple():
    assert run('scp-1200') == lex.show_page.summary


def test_scp_lookup_not_found():
    assert run('scp-7548') == lex.not_found.page


###############################################################################
# Search
###############################################################################


def test_search_simple():
    assert run('.s белки') == scp.show_page(page('scp-2797'))


def test_search_case_insensitive():
    assert run('.s БЕЛКИ') == scp.show_page(page('scp-2797'))


def test_search_rating_simple():
    assert run('.s -r >250') == lex.search.default(count=260)


def test_search_rating_range():
    assert run('.s -r 80..120') == lex.search.default(count=915)


def test_search_tags_simple():
    assert run('.s -t keter') == lex.search.default(count=374)


def test_search_author():
    assert run('.s -a anqxyr') == lex.search.default(count=25)


def test_search_created_exact_date():
    assert run('.s -c 2015-10-01') == scp.show_page(page('scp-2523'))


def test_seach_created_year_and_month():
    assert run('.s -c 2015-10') == lex.search.default(count=33)


def test_search_fullname():
    assert run('.s -f 1') == scp.show_page(page('1'))

###############################################################################
# Unused
###############################################################################


def test_unused_simple():
    assert run('.unused') == 'http://www.scp-wiki.net/scp-739'


def test_unused_last():
    assert run('.unused -l') == 'http://www.scp-wiki.net/scp-2973'


def test_unused_prime():
    assert run('.unused -p') == 'http://www.scp-wiki.net/scp-739'


def test_unused_divisible():
    assert run('.unused -d 10') == lex.not_found.unused


def test_unused_count():
    assert run('.unused -c') == lex.unused.count(count=225)
