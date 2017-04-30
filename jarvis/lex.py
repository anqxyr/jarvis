#!/usr/bin/env python3

###############################################################################
# Module Imports
###############################################################################

import jinja2
import pathlib
import random
import sys
import textwrap
import yaml

###############################################################################

DATA = {}
LEXPATH = pathlib.Path(__file__).parent / 'resources/lexicon'
for file in LEXPATH.glob('*.yaml'):
    with file.open() as filestream:
        DATA[file.stem] = yaml.safe_load(filestream)

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
        return self.compose('static')

    @property
    def jinja2(self):
        return env

    def compose(self, lexicon):
        if self.path[0] in DATA:
            lexicon, self.path = self.path[0], self.path[1:]
        template = DATA[lexicon]
        for i in self.path:
            template = template[i]
        text = env.from_string(template).render(**self.kwargs).strip()
        text = random.choice(text.split('\n'))
        text = text.strip()
        return text


###############################################################################


lex = Lexicon()
env = jinja2.Environment()
env.globals['lex'] = lex
env.filters['bold'] = lambda x: '\x02{}\x02'.format(x)
env.filters['shorten'] = textwrap.shorten
env.filters['escape_newline'] = lambda x: x.replace('\n', ' ')

sys.modules[__name__] = lex
