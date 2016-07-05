#!/usr/bin/env python3

###############################################################################
# Module Imports
###############################################################################

import pathlib
import yaml
import random
import sys

###############################################################################

with (pathlib.Path(__file__).parent / 'lexicon.yaml').open() as file:
    DATA = yaml.load(file)

###############################################################################


class Lexicon:

    def __init__(self, path=None):
        self.path = path or []
        self.kwargs = {}

    def __getattr__(self, value):
        return self.__class__(self.path + [value])

    def __call__(self, **kwargs):
        self.kwargs = kwargs
        return self

    def format(self, inp):
        out = DATA
        for i in self.path:
            out = out[i]
        try:
            out = out.split('\n')
        except AttributeError:
            pass
        return random.choice(out).replace('*', '\x02').format(**self.kwargs)


sys.modules[__name__] = Lexicon()
