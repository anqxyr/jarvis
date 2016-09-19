#!/usr/bin/env python3

###############################################################################
# Module Imports
###############################################################################

from jarvis import core, scp, lex, tools
from jarvis.tests.utils import run, page

###############################################################################


def test_dispatcher_simple():
    assert run('.seen', core.config.irc.nick) == lex.seen.self


def test_dispatcher_ambigious():
    assert run('.se') == tools.choose_input(['search', 'seen'])


def test_dispatcher_override():
    assert run('.s белки') == scp.show_page(page('scp-2797'))


def test_dispatcher_not_a_command():
    assert not run('.whatever')


def test_dispatcher_elipsis():
    assert not run('...')


def test_dispatcher_whitespace():
    assert not run(' ')


def test_dispatcher_plain_text():
    assert not run('text')


def test_dispatcher_case_sensitivity():
    assert run('.SEEN', core.config.irc.nick) == lex.seen.self
