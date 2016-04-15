#!/usr/bin/env python3

###############################################################################
# Module Imports
###############################################################################

import json
import pathlib
import random
import sys

###############################################################################


class NestedDictWrapper:

    def __init__(self, data):
        self.data = data

    def __getattr__(self, value):
        result = self.data.get(value)
        if not result:
            return 'ERROR: missing lexicon entry.'
        if isinstance(result, list):
            return random.choice(result)
        if isinstance(result, dict):
            return NestedDictWrapper(result)
        raise ValueError


path = pathlib.Path(__file__).parent / 'lexicon.json'
with open(str(path)) as file:
    data = json.load(file)

sys.modules[__name__] = NestedDictWrapper(data)
