#!/usr/bin/env python3
"""
Jarvis Parser Module.

Contains argument parsers for other commands.
"""
###############################################################################
# Module Imports
###############################################################################

import arrow
import copy
import functools
import re

from . import lexicon

###############################################################################
# Generic Functionality
###############################################################################


def parser(fn):
    parser = ArgumentParser()
    fn(parser)

    @functools.wraps(fn)
    def deco(command):
        @functools.wraps(command)
        def wrapped(inp, *args, **kwargs):
            try:
                parsed_args = parser.parse_args(inp.text)
            except ArgumentError:
                inp.multiline = False
                return lexicon.input.incorrect
            parsed_args.update(kwargs)
            return command(inp, *args, **parsed_args)
        return wrapped
    return deco


###############################################################################
# ArgumentParser
###############################################################################


class Argument:

    def __init__(self, *args, **kwargs):
        self.name = args[0].lstrip('-')
        self.is_opt = args[0].startswith('-')
        self.flags = args if self.is_opt else []

        self.nargs = kwargs.get('nargs', None)
        if not self.nargs and self.is_opt:
            self.nargs = 0
        elif not self.nargs and not self.is_opt:
            self.nargs = 1

        self.action = kwargs.get('action', None)

        self.re = kwargs.get('re', None)
        self.type = kwargs.get('type', None)
        self.choices = kwargs.get('choices', None)
        self.ignore = kwargs.get('ignore', None)

        self.values = []
        self.open = True
        self.marked = False

    def __repr__(self):
        return '<{} name={} values={}>'.format(
            self.__class__.__name__, repr(self.name), repr(self.values))

    def consume(self, value):
        if self.max_consumed or not self.open:
            return False

        if self.re and not re.match(self.re, value):
            return False

        if self.type:
            try:
                value = self.type(value)
                assert value is not None
            except:
                return False

        if self.choices and value not in self.choices:
            return False

        self.values.append(value)
        return True

    @property
    def min_consumed(self):
        if self.is_opt:
            return True
        if self.nargs in ['?', '*']:
            return True
        if self.nargs == '+':
            return len(self.values) > 0
        return len(self.values) >= self.nargs

    @property
    def max_consumed(self):
        if self.nargs == '?':
            return len(self.values) > 0
        if self.nargs in ['*', '+']:
            return False
        return len(self.values) >= self.nargs

    def get_values(self):
        if self.ignore:
            return {}

        if self.action == 'join':
            return {self.name: ' '.join(self.values)}

        if self.action:
            return self.action(self.name, self.values)

        if self.nargs == 0 and self.is_opt:
            return {self.name: self.marked}

        if self.nargs in [1, '?']:
            return {self.name: self.values[0] if self.values else None}

        return {self.name: self.values}


class ArgumentParser:

    def __init__(self):
        self._pos = []
        self._opt = []
        self.exc = []

    def add_argument(self, *args, **kwargs):
        arg = Argument(*args, **kwargs)
        (self._opt if arg.is_opt else self._pos).append(arg)

    def exclusive(self, *args, required=False):
        self.exc.append({'args': args, 'required': required})

    def parse_args(self, input_string):
        self.pos = copy.deepcopy(self._pos)
        self.opt = copy.deepcopy(self._opt)
        last = None
        for value in input_string.split(' '):
            if not input_string:
                break
            known_flag = self._get_known_flag(value)
            if known_flag:
                self._close(last)
                last = known_flag
            elif last:
                consumed = last.consume(value)
                if not consumed:
                    self._close(last)
                    last = self._next_positional(value)
            else:
                last = self._next_positional(value)
        self._check_constraints()
        values = {}
        for arg in self.pos + self.opt:
            values.update(arg.get_values())
        return values

    def _get_known_flag(self, value):
        for arg in self.opt:
            if value in arg.flags and arg.open:
                arg.marked = True
                return arg

    def _next_positional(self, value):
        for arg in self.pos:
            if not arg.open:
                continue
            consumed = arg.consume(value)
            if not consumed and not arg.min_consumed:
                raise ArgumentError
            elif not consumed:
                self._close(arg)
            else:
                return arg
        raise ArgumentError

    def _close(self, arg):
        if arg is None:
            return
        if not arg.min_consumed:
            raise ArgumentError
        arg.open = False
        if (arg.is_opt and not arg.marked) or not arg.values:
            return
        for exc in self.exc:
            if arg.name not in exc['args']:
                continue
            for name in exc['args']:
                arg = next(i for i in self.pos + self.opt if i.name == name)
                arg.open = False

    def _arg_present(self, name):
        arg = next(i for i in self.opt + self.pos if i.name == name)
        return bool(arg.marked if arg.is_opt else arg.values)

    def _check_constraints(self):
        if not all(i.min_consumed for i in self.pos + self.opt):
            raise ArgumentError
        for exc in self.exc:
            if sum(1 for arg in exc['args'] if self._arg_present(arg)) > 1:
                raise ArgumentError
            if not exc['required']:
                continue
            if not any(self._arg_present(arg) for arg in exc['args']):
                raise ArgumentError(
                    'Required mutually exclusive arguments missing: {}'
                    .format(self.pos + self.opt))


class ArgumentError(Exception):
    pass


###############################################################################
# Notes
###############################################################################


@parser
def tell(pr):
    pr.add_argument('topic', re='@.+', type=lambda x: x.lstrip('@'), nargs='?')
    pr.add_argument('user', type=lambda x: x.lower().rstrip(':,'), nargs='?')
    pr.exclusive('user', 'topic', required=True)
    pr.add_argument('message', nargs='+', action='join')


@parser
def outbound(pr):
    pr.add_argument('action', choices=['count', 'purge', 'echo'])


@parser
def seen(pr):
    pr.add_argument('--first', '-f')
    pr.add_argument('--total', '-t')
    pr.exclusive('first', 'total')
    pr.add_argument('user', type=str.lower)


@parser
def quote(pr):
    pr.add_argument('mode', nargs='?', choices=['add', 'del'])
    pr.add_argument('_', nargs='*', ignore=True)


@parser
def quote_add(pr):
    pr.add_argument('mode', choices=['add'], ignore=True)
    pr.add_argument('date', nargs='?', type=arrow.get)
    pr.add_argument('user', type=str.lower)
    pr.add_argument('message', nargs='+', action='join')


@parser
def quote_del(pr):
    pr.add_argument('mode', choices=['del'], ignore=True)
    pr.add_argument('user', type=str.lower)
    pr.add_argument('message', nargs='+', action='join')


@parser
def quote_get(pr):
    pr.add_argument('user', re='[^\d-].*', type=str.lower, nargs='?')
    pr.add_argument('index', type=int, nargs='?')


@parser
def save_memo(pr):
    pr.add_argument('user')
    pr.add_argument('message', nargs='+', action='join')


@parser
def topic(pr):
    pr.add_argument('action', choices=[
        'list', 'subscribe', 'unsubscribe', 'sub', 'unsub',
        'restrict', 'unrestrict', 'res', 'unres'])
    pr.add_argument('topic', nargs='?')


@parser
def alert(pr):
    pr.add_argument('date', type=arrow.get, nargs='?')
    pr.add_argument('span', re='(\d+[dhm])+', nargs='?')
    pr.exclusive('date', 'span', required=True)
    pr.add_argument('message', nargs='+', action='join')


###############################################################################
# SCP
###############################################################################


@parser
def search(pr):
    pr.add_argument('partial', nargs='*')
    pr.add_argument('--exclude', '-e', nargs='+')
    pr.add_argument('--strict', '-s', nargs='+')
    pr.add_argument('--tags', '-t', nargs='+', action='join')
    pr.add_argument('--author', '-a', nargs='+', action='join')
    pr.add_argument('--rating', '-r', nargs=1)
    pr.add_argument('--created', '-c', nargs=1)


@parser
def last_created(pr):
    pr.add_argument('limit', nargs='?', type=int, choices=range(1, 11))


###############################################################################
# Tools
###############################################################################


@parser
def showmore(pr):
    pr.add_argument('index', nargs='?', type=int)


###############################################################################
# Websearch
###############################################################################


@parser
def websearch(pr):
    pr.add_argument('query', nargs='+', action='join')
