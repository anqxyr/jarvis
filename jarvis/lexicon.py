#!/usr/bin/env python3

###############################################################################
# Module Imports
###############################################################################

import json
import pathlib
import random
import sys

###############################################################################

class Lexicon:

    def __init__(self):
        path = pathlib.Path(__file__).parent / 'lexicon.json')
        with open(str(path)) as file:
            self.data = json.load(file)

    def __getattr__(self, value):
        keys = [k for k in self.data if value.startswith(k)]
        if not key:
            return 'ERROR: missing lexicon entry.'
        return random.choice(sum([self.data[k] for k in keys], []))


sys.modules[__name__] = Lexicon()

