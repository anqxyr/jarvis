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
        new = self.__class__(self.path)
        new.kwargs = kwargs
        return new

    @property
    def _raw(self):
        out = DATA
        for i in self.path:
            out = out[i]
        try:
            out = out.split('\n')
        except AttributeError:
            pass
        return out

    def compose(self, inp):
        text = random.choice(self._raw)
        return text.replace('*', '\x02').format(**self.kwargs)


sys.modules[__name__] = Lexicon()
