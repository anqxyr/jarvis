#!/usr/bin/env python3

###############################################################################
# Module Imports
###############################################################################

import configparser
import pathlib
import pyscp

from . import ext

###############################################################################

config = configparser.ConfigParser()
config.read('jarvis.cfg')

wiki = pyscp.wikidot.Wiki('www.scp-wiki.net')
pages = None


def refresh():
    kwargs = dict(body='title created_by created_at rating tags', category='*')
    if config['wiki'].getboolean('debug'):
        pyscp.utils.default_logging(True)
        data = wiki._list_pages_parsed(author='anqxyr', **kwargs)
    else:
        data = wiki.list_pages(**kwargs)
    global pages
    pages = ext.PageView(data)
    wiki.titles.cache_clear()
    wiki.metadata.cache_clear()


refresh()
