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

    def __repr__(self):
        return '<{} {}>'.format(
            self.__class__.__qualname__, '.'.join(self.path))

    def __eq__(self, other):
        if not hasattr(other, 'path'):
            return False
        if self.path != other.path:
            return False
        print(self.kwargs)
        print(other.kwargs)
        return self.kwargs == other.kwargs

    def __getattr__(self, value):
        return self.__class__(self.path + [value])

    def __call__(self, **kwargs):
        new = self.__class__(self.path)
        new.kwargs = kwargs
        return new

    def __str__(self):
        text = random.choice(self._raw.split('\n')).replace('*', '\x02')
        return text.format(**self.kwargs)

    @property
    def _raw(self):
        out = DATA
        for i in self.path:
            out = out[i]
        return out

    def compose(self, inp):
        return str(self)


sys.modules[__name__] = Lexicon()
