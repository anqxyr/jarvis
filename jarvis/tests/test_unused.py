#!/usr/bin/env python3

###############################################################################
# Module Imports
###############################################################################


from jarvis import lex
from jarvis.tests.utils import run

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
