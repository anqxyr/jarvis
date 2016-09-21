#!/usr/bin/env python3

###############################################################################
# Module Imports
###############################################################################

import pathlib
import yaml
import random
import sys
import jinja2

###############################################################################

with (pathlib.Path(__file__).parent / 'lexicon.yaml').open() as file:
    DATA = yaml.safe_load(file)

###############################################################################


class Lexicon:

    def __init__(self, path=None):
        self.path = path or []
        self.kwargs = {}

    def __repr__(self):
        return '<{} {} {}>'.format(
            self.__class__.__qualname__,
            '.'.join(self.path),
            repr(self.kwargs))

    def __eq__(self, other):
        """
        Compare lex objects to each other.

        This comparison is unintuitive in the interests of practicality.
        Saved arguments are compared, but only if they're present in
        both objects. This means that all of the following is true:

        lex.example(a=3) != lex.example(a=4)
        lex.example(a=3, b=4) == lex.example(a=3)
        lex.example == lex.example(a=3)
        lex.example == lex.example(a=4)
        """
        if not hasattr(other, 'path'):
            return False
        if self.path != other.path:
            return False
        for k, v in self.kwargs.items():
            if other.kwargs.get(k, v) != v:
                return False
        return True

    def __getattr__(self, value):
        return self.__class__(self.path + [value])

    def __call__(self, **kwargs):
        new = self.__class__(self.path)
        new.kwargs = kwargs
        return new

    def __str__(self):
        text = env.from_string(self._raw).render(**self.kwargs).strip()
        text = random.choice(text.split('\n'))
        return text.strip().format(**self.kwargs)

    @property
    def _raw(self):
        out = DATA
        for i in self.path:
            out = out[i]
        return out

    @property
    def jinja2(self):
        return env

    def compose(self, inp):
        return str(self)


###############################################################################


lex = Lexicon()
env = jinja2.Environment()
env.globals['lex'] = lex
env.filters['bold'] = lambda x: '\x02{}\x02'.format(x)

sys.modules[__name__] = lex
