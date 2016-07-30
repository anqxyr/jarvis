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

from . import lex

###############################################################################
# Generic Functionality
###############################################################################


def parser(func):
    parser = ArgumentParser()
    func(parser)

    @functools.wraps(func)
    def deco(command):
        inner = CommandWrapper(command, parser)
        return functools.wraps(command)(inner)
    return deco


class CommandWrapper:

    def __init__(self, func, parser):
        self._func = func
        self._parser = parser
        self._subcommands = {}

    def __call__(self, inp, *args, **kwargs):
        try:
            parsed = self._parser.parse_args(inp.text.split())
        except ArgumentError:
            inp.multiline = False
            return lex.input.incorrect
        parsed.update(kwargs)
        return self._func(inp, *args, **parsed)

    def subcommand(self, mode=None):

        def inner(func):
            self._subcommands[mode] = func
            return func

        return inner

    def dispatch(self, inp, mode, *args, **kwargs):
        return self._subcommands[mode](inp, *args, **kwargs)

###############################################################################
# ArgumentParser
###############################################################################


class Argument:

    def __init__(self, *args, **kwargs):
        self.name = args[0].lstrip('-')
        self.is_optional = args[0].startswith('-')
        self.flags = args if self.is_optional else []

        self.nargs = kwargs.get('nargs', None)
        if not self.nargs and self.is_optional:
            self.nargs = 0
        elif not self.nargs and not self.is_optional:
            self.nargs = 1

        self.action = kwargs.get('action', None)

        self.re = kwargs.get('re', None)
        self.type = kwargs.get('type', None)
        self.choices = kwargs.get('choices', None)

        self.values = []
        self.open = True
        self.marked = False

    def __repr__(self):
        return '<{} name={} values={}>'.format(
            self.__class__.__name__, repr(self.name), repr(self.values))

    def consume(self, value):
        """
        Attempt to consume the value.

        Checks if the argument can consume the value based on its
        restrictions. If so, adds the value to the argument's value list
        and returns True. Otherwise returns False.
        """
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
        """Show if minimal requirements for the argument have been met."""
        if self.is_optional:
            return True  # optional args don't have minimal requirements
        if self.nargs in ['?', '*']:
            return True
        if self.nargs == '+':
            return len(self.values) > 0
        return len(self.values) >= self.nargs

    @property
    def max_consumed(self):
        """Show if the argument has consumed all the values it can."""
        if self.nargs == '?':
            return len(self.values) > 0
        if self.nargs in ['*', '+']:
            return False
        return len(self.values) >= self.nargs

    def get_values(self):
        if self.action == 'join':
            return {self.name: ' '.join(self.values)}

        if self.action:
            return self.action(self.name, self.values)

        if self.nargs == 0 and self.is_optional:
            return {self.name: self.marked}

        if self.nargs in [1, '?']:
            return {self.name: self.values[0] if self.values else None}

        return {self.name: self.values}


class ArgumentParser:

    def __init__(self):
        self._args = []
        self._exclusive_args = []
        self._subparsers = {}

    def add_argument(self, *args, **kwargs):
        self._args.append(Argument(*args, **kwargs))

    def exclusive(self, *args, required=False):
        self._exclusive_args.append({'args': args, 'required': required})

    def subparser(self, mode=None):
        if not any(i.name == 'mode' for i in self._args):
            self.add_argument('mode', nargs='?')
        pr = ArgumentParser()
        self._subparsers[mode] = pr
        return pr

    def parse_args(self, unparsed):
        """
        Parse arguments.

        Takes a list of strings, and returns a dict of parsed args.
        """
        # Argument objects are mutable
        # at the beginning of each parsing we make a copy of them
        # and work with that copy only from then on
        self.args = copy.deepcopy(self._args)
        values = {}
        last = None
        while unparsed:
            # go through each segment and try to match it either to the
            # current positional argument  or to any optional one
            if not unparsed:
                break
            value = unparsed[0]
            unparsed = unparsed[1:]
            known_flag = self._get_known_flag(value)
            if known_flag:
                # if an optional argument is found, then the last argument
                # has just ended, so lets close it
                self._close(last)
                last = known_flag
            elif last:
                # otherwise continue feeding the last known argument
                consumed = last.consume(value)
                if not consumed:
                    self._close(last)
                    last = self._next_positional(value)
            else:
                # and if we don't know any, get the next positional
                last = self._next_positional(value)
            # if the name of the argument is 'mode'
            # then hand off the rest of the parsing to a subparser
            if last.name == 'mode':
                self._close(last)
                break
        self._check_constraints()
        for arg in self.args:
            values.update(arg.get_values())
        if 'mode' in values:
            subparser = self._subparsers[values['mode']]
            values.update(subparser.parse_args(unparsed))
        return values

    def _get_known_flag(self, value):
        """
        Get the flag corresponding to the value.

        Checks if the value indicates any of the known flags.
        If it does, returns it. Otherwise, returns None.
        """
        for arg in [i for i in self.args if i.is_optional]:
            if value in arg.flags and arg.open:
                arg.marked = True
                return arg

    def _next_positional(self, value):
        for arg in [i for i in self.args if not i.is_optional]:
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
        if (arg.is_optional and not arg.marked) or not arg.values:
            return
        for exc in self._exclusive_args:
            if arg.name not in exc['args']:
                continue
            for name in exc['args']:
                next(i for i in self.args if i.name == name).open = False

    def _arg_present(self, name):
        arg = next(i for i in self.args if i.name == name)
        return bool(arg.marked if arg.is_optional else arg.values)

    def _check_constraints(self):
        if not all(i.min_consumed for i in self.args):
            raise ArgumentError
        for exc in self._exclusive_args:
            if sum(1 for arg in exc['args'] if self._arg_present(arg)) > 1:
                raise ArgumentError
            if not exc['required']:
                continue
            if not any(self._arg_present(arg) for arg in exc['args']):
                raise ArgumentError(
                    'Required mutually exclusive arguments missing: {}'
                    .format(self.args))


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
    pr.add_argument('channel', re='#', nargs='?')
    pr.add_argument('user', type=str.lower)


@parser
def quote(pr):
    pr.add_argument('channel', re='#', nargs='?')

    get = pr.subparser()
    get.add_argument('user', re=r'.*[^\d].*', type=str.lower, nargs='?')
    get.add_argument('index', type=int, nargs='?')

    add = pr.subparser('add')
    add.add_argument(
        'date', nargs='?', type=arrow.get, re=r'\d{4}-\d{2}-\d{2}')
    add.add_argument('user', type=str.lower)
    add.add_argument('message', nargs='+', action='join')

    delete = pr.subparser('del')
    delete.add_argument('user', type=str.lower)
    delete.add_argument('message', nargs='+', action='join')


@parser
def save_memo(pr):
    pr.add_argument('user', type=str.lower)
    pr.add_argument('message', nargs='*', action='join')
    pr.add_argument('--purge', '-p', '--forget', '-f')
    pr.exclusive('message', 'purge', required=True)


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
    pr.add_argument('partial', nargs='*', type=str.lower)
    pr.add_argument('--exclude', '-e', nargs='+', type=str.lower)
    pr.add_argument('--strict', '-s', nargs='+', type=str.lower)
    pr.add_argument('--tags', '-t', nargs='+', action='join', type=str.lower)
    pr.add_argument('--author', '-a', nargs='+', action='join', type=str.lower)
    pr.add_argument('--rating', '-r', re=r'([><=]?\d+)|(\d+\.\.\d+)', nargs=1)
    pr.add_argument('--created', '-c', nargs=1)
    pr.add_argument(
        '--fullname', '-f', nargs='+', action='join', type=str.lower)
    pr.add_argument('--summary', '-u')


@parser
def unused(pr):
    pr.add_argument('--random', '-r')
    pr.add_argument('--last', '-l')
    pr.add_argument('--count', '-c')
    pr.add_argument('--prime', '-p')
    pr.add_argument('--palindrome', '-i')
    pr.add_argument('--divisible', '-d', nargs=1, type=int)
    pr.exclusive('random', 'last', 'count')


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


###############################################################################
# Images
###############################################################################


@parser
def images(pr):

    pr.subparser('scan').add_argument('page')

    update = pr.subparser('update')
    update.add_argument('target')
    update.add_argument('index', nargs='?', type=int)
    update.add_argument('--url', '-u', nargs=1)
    update.add_argument('--page', '-p', nargs=1)
    update.add_argument('--source', '--origin', '-o', nargs=1)
    update.add_argument(
        '--status', '-s', nargs='+', type=str.upper, action='join')

    list_ = pr.subparser('list')
    list_.add_argument('target')
    list_.add_argument('index', nargs='?', type=int)
    list_.add_argument('--terse', '-t')

    notes = pr.subparser('notes')
    notes.add_argument('target')
    notes.add_argument('index', nargs='?', type=int)
    notes.add_argument('--append', '-a', nargs='+', action='join')
    notes.add_argument('--purge', '-p')
    notes.add_argument('--list', '-l')
    notes.exclusive('append', 'purge', 'list')

    purge = pr.subparser('purge')
    purge.add_argument('target')
    purge.add_argument('index', nargs='?', type=int)

    search = pr.subparser('search')
    search.add_argument('target')
    search.add_argument('index', nargs='?', type=int)

    pr.subparser('stats').add_argument('category')

    add = pr.subparser('add')
    add.add_argument('url')
    add.add_argument('page', nargs='?')
