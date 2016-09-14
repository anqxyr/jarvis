#!/usr/bin/env python3

###############################################################################
# Module Imports
###############################################################################


import pyscp
import pytest
import jarvis
import pathlib


###############################################################################


@pytest.fixture(scope='session', autouse=True)
def prepare_databases():
    snapshot_path = pathlib.Path('jarvis/tests/resources/snapshot.db')
    jarvis.core.wiki = pyscp.snapshot.Wiki(
        'www.scp-wiki.net', str(snapshot_path))
    jarvis.core.pages = jarvis.ext.PageView(
        jarvis.core.wiki.list_pages(limit=1))

    db_path = pathlib.Path('jarvis/tests/resources/jarvis.db')
    if db_path.exists():
        db_path.unlink()
    jarvis.notes.init(str(db_path))

    yield

    db_path.unlink()
