#!/usr/bin/env python3

###############################################################################
# Module Imports
###############################################################################

import pytest
import jarvis
import pathlib
import random

###############################################################################


random.seed(200)


###############################################################################


@pytest.fixture(scope='session', autouse=True)
def prepare_databases():
    db_path = pathlib.Path('jarvis/tests/resources/jarvis.db')
    if db_path.exists():
        db_path.unlink()
    jarvis.db.init(str(db_path))
