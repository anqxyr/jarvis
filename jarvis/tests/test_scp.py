#!/usr/bin/env python3

###############################################################################
# Module Imports
###############################################################################

import pytest
import pyscp
import pyscp_bot as pbot

###############################################################################


wiki = pyscp.snapshot.Wiki(
    'www.scp-wiki.net',
    '/home/anqxyr/heap/_scp/scp-wiki.2016-04-01.db')

pages = pbot.ext.PageView(list(wiki.list_pages()))


def test_get_author_summary():
    out = pbot.scp.get_author_summary(pages, 'anqxyr')
    assert 'http://www.scp-wiki.net/anqxyr' in out
    assert 'SCPs' in out
    assert 'tales' in out
    assert 'GOI-format' not in out
    assert 'rewrites' not in out

    assert ', )' not in out
    assert '( ,' not in out
    assert ',)' not in out
    assert '(,' not in out
    assert '()' not in out

    out = pbot.scp.get_author_summary(pages, 'Voct')
    assert 'rewrites' in out
    assert 'artwork galleries' not in out

    assert ', )' not in out
    assert '( ,' not in out
    assert ',)' not in out
    assert '(,' not in out
    assert '()' not in out

    out = pbot.scp.get_author_summary(pages, 'SunnyClockwork')
    assert 'SCPs' not in out
    assert 'artwork galleries' in out

    assert ', )' not in out
    assert '( ,' not in out
    assert ',)' not in out
    assert '(,' not in out
    assert '()' not in out

    out = pbot.scp.get_author_summary(pages, 'Moto42')

    assert ', )' not in out
    assert '( ,' not in out
    assert ',)' not in out
    assert '(,' not in out
    assert '()' not in out

    out = pbot.scp.get_author_summary(pages, 'Crayne')
    assert 'artwork' not in out

    out = pbot.scp.get_author_summary(pages, 'Roget')
    assert 'rewrites' in out
