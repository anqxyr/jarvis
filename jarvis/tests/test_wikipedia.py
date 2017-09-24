#!/usr/bin/env python3

###############################################################################
# Module Imports
###############################################################################


from jarvis import lex
from jarvis.tests.utils import run

###############################################################################


def test_wikipedia_simple():
    assert run('.w music') == lex.wikipedia.result(title='Music')


def test_wikipedia_ambiguous():
    assert run('.w mercury') == lex.unclear


def test_wikipedia_not_found():
    assert run('.w sdfgdhfghe') == lex.wikipedia.not_found


def test_wikipedia_bracket_escaping():
    assert str(run('.w probability field'))
