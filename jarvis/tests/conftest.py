#!/usr/bin/env python3

###############################################################################
# Module Imports
###############################################################################

import arrow
import pyscp
import pytest
import jarvis
import pathlib
import random

from playhouse import dataset

###############################################################################


random.seed(200)


###############################################################################


@pytest.fixture(scope='session', autouse=True)
def prepare_databases():
    db = dataset.DataSet('sqlite:///jarvis/tests/resources/snapshot.db')
    pages = []
    for p in db['page'].all():
        page = jarvis.core.wiki(p['url'])
        for k, v in p.items():
            page._body[k] = v
        pages.append(page)
    jarvis.core.pages = jarvis.ext.PageView(pages)
    jarvis.core.wiki.titles = lambda: {}

    db_path = pathlib.Path('jarvis/tests/resources/jarvis.db')
    if db_path.exists():
        db_path.unlink()
    jarvis.notes.init(str(db_path))
