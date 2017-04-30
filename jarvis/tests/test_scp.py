#!/usr/bin/env python3

###############################################################################
# Module Imports
###############################################################################

from jarvis import scp, lex
from jarvis.tests.utils import run, page

###############################################################################
# Author
###############################################################################


def test_author_simple():
    # the call to scp here is a code smell
    # run results should be always compared to lex objects directly
    # if they can't be, it means the output is too complicated
    assert run('.au anq') == lex.author.summary(name='anqxyr')


def test_author_ambiguous():
    assert run('.au gears') == lex.unclear(
        options=['Dr Gears', 'TwistedGears'])


def test_author_not_found():
    assert run('.au fakeauthorname') == lex.author.not_found


def test_author_default():
    assert run('.au', _user='anqxyr') == lex.author.summary(name='anqxyr')


def test_author_showmore():
    run('.au Jack')
    assert run('.sm 3') == lex.author.summary


###############################################################################


def test_authordetails_showmore():
    run('.ad Jack')
    assert run('.sm 3')


###############################################################################
# Misc
###############################################################################


def test_scp_lookup_simple():
    assert run('scp-1200') == lex.page_lookup.summary


def test_scp_lookup_not_found():
    assert run('scp-7548') == lex.page_lookup.not_found


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
    assert run('.unused') == lex.unused.found(slot='scp-2258')


def test_unused_last():
    assert run('.unused -l') == lex.unused.found(slot='scp-3999')


def test_unused_prime():
    assert run('.unused -p') == lex.unused.found(slot='scp-2287')


def test_unused_divisible():
    assert run('.unused -d 10 -s 3') == lex.unused.not_found


def test_unused_count():
    assert run('.unused -c') == lex.unused.count(count=1217)


def test_unused_series():
    assert run('.unused -c -s 1 2 3') == lex.unused.count(count=217)
