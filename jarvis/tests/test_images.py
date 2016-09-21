#!/usr/bin/env python3
"""Test jarvis.images module."""

###############################################################################
# Module Imports
###############################################################################


from jarvis import lex, images
from jarvis.tests.utils import run


###############################################################################


def test_images_list_simple():
    assert run('.im list scp-003') == lex.images.list.verbose(
        url='http://scp-wiki.wdfiles.com/local--files/scp-003/SCP-003a.jpg',
        status='BY-NC-SA CC')
