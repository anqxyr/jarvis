#!/usr/bin/env python3
"""
Jarvis Parser Module.

Contains argument parsers for other commands.
"""
###############################################################################
# Module Imports
###############################################################################

import arrow
import functools
import re
import traceback

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
                traceback.print_exc()
                return lexicon.input.incorrect
            print(parsed_args)
            return
            kwargs.update(parsed_args)
            return command(inp, *args, **kwargs)
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
        if not self.action and not self.is_opt:
            self.action = 'join'

        self.re = kwargs.get('re', None)
        self.type = kwargs.get('type', None)

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
            except:
                return False

        self.values.append(value)
        return True

    @property
    def min_consumed(self):
        if self.is_opt and not self.required:
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
        if not self.nargs == 0 and self.is_opt:
            return self.marked

        if not self.values:
            return None

        if self.action == 'join':
            return ' '.join(self.values)

        return self.values


class ArgumentParser:

    def __init__(self):
        self.pos = []
        self.opt = []
        self.exc = []

    def add_argument(self, *args, **kwargs):
        arg = Argument(*args, **kwargs)
        (self.opt if arg.is_opt else self.pos).append(arg)

    def exclusive(self, *args, required=False):
        self.exc.append({'args': args, 'required': required})

    def parse_args(self, input_string):
        last = None
        for value in input_string.split(' '):
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
        values = {i.name: i.get_values() for i in self.pos + self.opt}
        self._reset()
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

    def _check_constraints(self):
        if not all(i.min_consumed for i in self.pos + self.opt):
            raise ArgumentError
        for exc in self.exc:
            if not exc['required']:
                continue
            args = [i for i in self.pos + self.opt if i.name in exc['args']]
            if not any(i.marked if i.is_opt else i.values for i in args):
                raise ArgumentError(
                    'Required mutually exclusive arguments missing: {}'
                    .format(self.pos + self.opt))

    def _reset(self):
        for arg in self.pos + self.opt:
            arg.values = []
            arg.open = True
            arg.marked = False


class ArgumentError(Exception):
    pass


###############################################################################
# Notes
###############################################################################


@parser
def tell(pr):
    pr.add_argument('topic', re='@.*', type=lambda x: x.lstrip('@'), nargs='?')
    pr.add_argument('user', type=lambda x: x.rstrip(':,'), nargs='?')
    pr.exclusive('user', 'topic', required=True)
    pr.add_argument('message', nargs='+')


@parser
def outbound(pr):
    pr.add_argument('action', choices=['count', 'purge'])


@parser
def seen(pr):
    pr.add_argument('--first', '-f')
    pr.add_argument('user')


@parser
def quote(pr):
    pr.add_argument('mode', nargs='?', choices=['add', 'del'])
    pr.add_argument('_', nargs='*')


@parser
def quote_add(pr):
    pr.add_argument('mode', choices=['add'])
    pr.add_argument('date', nargs='?', type=arrow.get)
    pr.add_argument('user')
    pr.add_argument('message', nargs='+')


@parser
def quote_del(pr):
    pr.add_argument('mode', choices=['del'])
    pr.add_argument('user')
    pr.add_argument('message', nargs='+')


@parser
def quote_get(pr):
    pr.add_argument('user', nargs='?')
    pr.add_argument('index', type=int, nargs='?')


@parser
def save_memo(pr):
    pr.add_argument('user')
    pr.add_argument('message', nargs='+')


@parser
def topic(pr):
    pr.add_argument('--list', '-l')
    pr.add_argument('topic')
    pr.add_argument('--subscribe', '-s')
    pr.add_argument('--unsubscribe', '-u')
    pr.add_argument('--restrict', '-r')
    pr.add_argument('--free', '-f')


@parser
def alert(pr):
    pr.add_argument('date', type=arrow.get)
    pr.add_argument('delay')
    #pr.exclusive('date', 'delay', required=True)
    pr.add_argument('message', nargs='+')


###############################################################################
# SCP
###############################################################################


@parser
def search(pr):
    pass
