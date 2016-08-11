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
        except ArgumentError as e:
            inp.multiline = False
            if e.usage:
                return e.usage(self._func.__name__)
            return self._parser.usage(self._func.__name__)
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

        self.nargs = kwargs.get('nargs')
        if not self.nargs:
            self.nargs = 0 if self.is_optional else 1

        self.action = kwargs.get('action')

        self.re = kwargs.get('re')
        self.type = kwargs.get('type')
        self.choices = kwargs.get('choices')

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

    @property
    def usage(self):
        if self.is_optional:
            return self._usage_optional
        else:
            return self._usage_positional

    @property
    def _usage_optional(self):
        flag = max(self.flags, key=len)
        if self.nargs == 0:
            return flag
        if self.nargs == 1:
            return '{} {}'.format(flag, self.name)
        if self.nargs == '+':
            return '{0} {1}1 [{1}2 ...]'.format(flag, self.name)
        args = [self.name + str(i) for i in range(1, self.nargs + 1)]
        return '{} {}'.format(flag, ' '.join(args))

    @property
    def _usage_positional(self):
        if self.choices:
            choices = ','.join([i for i in self.choices if i])
            if self.nargs == 1:
                return '{{{}}}'.format(choices)
            if self.nargs == '?':
                return '[{{{}}}]'.format(choices)
        if self.nargs == 1:
            return self.name
        if self.nargs == '?':
            return '[{}]'.format(self.name)
        if self.nargs == '*':
            if self.action == 'join':
                return '[{}]'.format(self.name)
            return '[{}1 ...]'.format(self.name)
        if self.nargs == '+':
            if self.action == 'join':
                return self.name
            return '{0}1 [{0}2 ...]'.format(self.name)
        return ' '.join([self.name + str(i) for i in range(1, self.nargs + 1)])


class ArgumentParser:

    def __init__(self, usage_subparser=None):
        self._uspr = usage_subparser
        self._args = []
        self._exclusive_args = []
        self._subparsers = {}

    def add_argument(self, *args, **kwargs):
        self._args.append(Argument(*args, **kwargs))

    def exclusive(self, *args, required=False):
        self._exclusive_args.append({'args': args, 'required': required})

    def subparser(self, mode=None):
        if not any(i.name == 'mode' for i in self._args):
            self.add_argument('mode', nargs='?', choices=[mode])
        else:
            mode_arg = next(i for i in self._args if i.name == 'mode')
            mode_arg.choices.append(mode)
        pr = ArgumentParser(mode)
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
            # a hook to force usage output
            if unparsed == ['--usage']:
                raise ArgumentError(self.usage)
            # go through each segment and try to match it either to the
            # current positional argument  or to any optional one
            if not unparsed:
                break
            known_flag = self._get_known_flag(unparsed[0])
            if known_flag:
                # if an optional argument is found, then the last argument
                # has just ended, so lets close it
                unparsed = unparsed[1:]
                self._close(last)
                last = known_flag
            elif last:
                # otherwise continue feeding the last known argument
                if not last.consume(unparsed[0]):
                    self._close(last)
                    last = self._next_positional()
                else:
                    unparsed = unparsed[1:]
            else:
                # and if we don't know any, get the next positional
                last = self._next_positional()
            # if the name of the argument is 'mode'
            # then hand off the rest of the parsing to a subparser
            if last.name == 'mode':
                if last.consume(unparsed[0]):
                    unparsed = unparsed[1:]
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

    def _next_positional(self):
        for arg in [i for i in self.args if not i.is_optional]:
            if not arg.open:
                continue
            return arg
        raise ArgumentError

    def _close(self, arg):
        if arg is None:
            return
        arg.open = False
        for exc in self._exclusive_args:
            args = exc['args']
            if arg.name not in args:
                continue
            if not self._arg_present(arg.name):
                return
            args = [i for i in self.args if i.name in args]
            for i in args:
                i.open = False
            return
        if not arg.min_consumed:
            raise ArgumentError
        if (arg.is_optional and not arg.marked) or not arg.values:
            return

    def _arg_present(self, name):
        arg = next(i for i in self.args if i.name == name)
        return bool(arg.marked if arg.is_optional else arg.values)

    def _check_constraints(self):
        exclusive = [i for e in self._exclusive_args for i in e['args']]
        for arg in self.args:
            if arg.name in exclusive:
                continue
            if not arg.min_consumed:
                raise ArgumentError

        for exc in self._exclusive_args:
            count = len([i for i in exc['args'] if self._arg_present(i)])
            if count > 1:
                raise ArgumentError
            if exc['required'] and count == 0:
                raise ArgumentError

    def _usage_exclusive(self, group):
        args = [i.usage for i in self._args if i.name in group['args']]
        args = ' | '.join(args)
        if group['required']:
            return '( {} )'.format(args)
        else:
            return '[ {} ]'.format(args)

    def usage(self, command_name):
        args = []
        exclusive_matched = []
        for arg in self._args:
            if arg.name in exclusive_matched:
                continue
            for excgroup in self._exclusive_args:
                if arg.name in excgroup['args']:
                    args.append(self._usage_exclusive(excgroup))
                    exclusive_matched.extend(excgroup['args'])
                    break
            else:
                usage = '[{}]' if arg.is_optional else '{}'
                usage = usage.format(arg.usage)
                args.append(usage)
        if self._uspr:
            return 'usage: !{} {} {}'.format(
                command_name, self._uspr, ' '.join(args))
        return 'usage: !{} {}'.format(command_name, ' '.join(args))


class ArgumentError(Exception):

    def __init__(self, usage=None):
        self.usage = usage


###############################################################################
# Notes
###############################################################################


@parser
def tell(pr):
    pr.add_argument('topic', re='@.+', type=lambda x: x.lstrip('@'))
    pr.add_argument('user', type=lambda x: x.lower().rstrip(':,'))
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
def memo(pr):
    pr.add_argument('channel', re='#', nargs='?')

    pr.subparser().add_argument('user', type=str.lower)

    add = pr.subparser('add')
    append = pr.subparser('append')
    delete = pr.subparser('del')

    for subpr in (add, append, delete):
        subpr.add_argument('user', type=str.lower)
        subpr.add_argument('message', nargs='+', action='join')

    pr.subparser('count')


@parser
def rem(pr):
    pr.add_argument('user', type=str.lower)
    pr.add_argument('message', nargs='+', action='join')


@parser
def topic(pr):
    pr.add_argument('action', choices=[
        'list', 'subscribe', 'unsubscribe', 'sub', 'unsub',
        'restrict', 'unrestrict', 'res', 'unres'])
    pr.add_argument('topic', nargs='?')


@parser
def alert(pr):
    pr.add_argument('date', type=arrow.get)
    pr.add_argument('span', re='(\d+[dhm])+')
    pr.exclusive('date', 'span', required=True)
    pr.add_argument('message', nargs='+', action='join')


###############################################################################
# SCP
###############################################################################


@parser
def random(pr):
    pr.add_argument('partial', nargs='*', type=str.lower)
    pr.add_argument('--exclude', '-e', nargs='+', type=str.lower)
    pr.add_argument('--strict', '-s', nargs='+', type=str.lower)
    pr.add_argument('--tags', '-t', nargs='+', action='join', type=str.lower)
    pr.add_argument('--author', '-a', nargs='+', action='join', type=str.lower)
    pr.add_argument('--rating', '-r', re=r'([><=]?\d+)|(\d+\.\.\d+)', nargs=1)
    pr.add_argument('--created', '-c', nargs=1)
    pr.add_argument(
        '--fullname', '-f', nargs='+', action='join', type=str.lower)


@parser
def search(pr):
    # search and random are almost the same
    # except search has one more argument
    random.__wrapped__(pr)
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

    pr.subparser('scan').add_argument('pages', nargs='+')

    update = pr.subparser('update')
    update.add_argument('target')
    update.add_argument('index', nargs='?', type=int)
    update.add_argument('--url', '-u', nargs=1)
    update.add_argument('--page', '-p', nargs=1)
    update.add_argument('--source', '--origin', '-o', nargs=1)
    update.add_argument(
        '--status', '-s', nargs='+', type=str.upper, action='join')
    update.add_argument('--notes', '-n', nargs='+', action='join')

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

    pr.subparser('sync')

    add = pr.subparser('add')
    add.add_argument('url')
    add.add_argument('page', nargs='?')

    remove = pr.subparser('remove')
    remove.add_argument('page')
    remove.add_argument('images', nargs='+')

    pr.subparser('attribute').add_argument('page')
