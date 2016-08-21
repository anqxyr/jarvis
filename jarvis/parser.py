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


class PositionalArgument:

    def __init__(self, *args, **kwargs):
        self.name = args[0].lstrip('-')

        self.is_optional = False

        self.nargs = kwargs.get('nargs', 1)

        self.action = kwargs.get('action')

        self.re = kwargs.get('re')
        self.type = kwargs.get('type')
        self.choices = kwargs.get('choices')

    def __repr__(self):
        return '<{} name={}>'.format(self.__class__.__name__, repr(self.name))

    @property
    def _min(self):
        """Minimum number of required values."""
        if self.nargs in ['?', '*']:
            return 0
        if self.nargs == '+':
            return 1
        return self.nargs

    @property
    def _max(self):
        """Maximum number of allowed values."""
        if self.nargs in ['*', '+']:
            return 999
        if self.nargs == '?':
            return 1
        return self.nargs

    def _apply_constraints(self, bit):
        if self.re:
            assert re.match(self.re, bit)

        if self.type:
            bit = self.type(bit)

        if self.choices:
            assert bit in self.choices

        return bit

    def _finalize(self, values):
        if self.nargs in [1, '?']:
            return values[0] if values else None

        if not self.action:
            return values

        if self.action == 'join':
            return ' '.join(values)

        return self.action(values)

    def parse(self, unparsed, values):
        parsed = []
        counter = 0
        for bit in unparsed:
            if self.name != 'mode':
                assert bit != '--usage'
            if len(parsed) >= self._max:
                break
            try:
                bit = self._apply_constraints(bit)
            except:
                break
            parsed.append(bit)
            counter += 1
        assert self._min <= len(parsed) <= self._max
        values[self.name] = self._finalize(parsed)
        unparsed[:] = unparsed[counter:]

    def usage(self, brackets=True):
        if self.choices:
            usage = '{{{}}}'.format(','.join([i for i in self.choices if i]))
        elif self.nargs in [1, '?'] or self.action == 'join':
            usage = self.name
        elif self.nargs in ['*', '+']:
            usage = self.name
        else:
            usage = [self.name + str(i) for i in range(1, self.nargs + 1)]
            usage = ' '.join(usage)

        if self.nargs in ['?', '*'] and brackets:
            usage = '[{}]'.format(usage)

        return usage


class OptionalArgument(PositionalArgument):

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('nargs', 0)
        super().__init__(*args, **kwargs)
        self.is_optional = True
        self.flags = args

    def _finalize(self, values):
        if not values:
            return True
        return super()._finalize(values)

    def parse(self, unparsed, values):
        for i in self.flags:
            if i in unparsed:
                idx = unparsed.index(i)
                break
        else:
            values[self.name] = False
            return

        unparsed2 = unparsed[idx + 1:]
        super().parse(unparsed2, values)

        unparsed[:] = unparsed[:idx] + unparsed2

    def usage(self, brackets=True):
        usage = super().usage()
        usage = '--{} {}'.format(self.name, usage).strip()

        if brackets:
            usage = '[{}]'.format(usage)

        return usage


class ExclusiveGroup:

    def __init__(self, args, required):
        self.args = args
        self.required = required

    def parse(self, arg, values):
        if arg.name not in self.args:
            return
        if any(values.get(i) for i in self.args):
            values[arg.name] = None

    def validate(self, values):
        if not self.required:
            return
        if not any(values.get(i) for i in self.args):
            assert False

    def usage(self, args):
        args = [i for i in args if i.name in self.args]
        args = [i.usage(brackets=False) for i in args]
        args = '|'.join(args)
        return ('({})' if self.required else '[{}]').format(args)


class ArgumentParser:

    def __init__(self, subparser=None):
        self._spname = subparser
        self._args = []
        self._egroups = []
        self._subparsers = {}

    def add_argument(self, *args, **kwargs):
        if args[0].startswith('-'):
            cls = OptionalArgument
        else:
            cls = PositionalArgument
        self._args.append(cls(*args, **kwargs))

    def exclusive(self, *args, required=False):
        self._egroups.append(ExclusiveGroup(args, required))

    def subparser(self, mode=None):
        if not any(i.name == 'mode' for i in self._args):
            self.add_argument(
                'mode',
                nargs='?' if mode is None else 1,
                choices=[mode], type=str.lower)
        else:
            mode_arg = next(i for i in self._args if i.name == 'mode')
            mode_arg.choices.append(mode)
            if mode is None:
                mode_arg.nargs = '?'
        pr = ArgumentParser(mode)
        self._subparsers[mode] = pr
        return pr

    def _next_arg(self, args, values):
        for arg in args:
            for e in self._egroups:
                e.parse(arg, values)
            if arg.name in values:
                continue
            yield arg

    def _next_positional(self, values):
        args = [i for i in self._args if not i.is_optional]
        yield from self._next_arg(args, values)

    def _next_optional(self, values):
        args = [i for i in self._args if i.is_optional]
        yield from self._next_arg(args, values)

    def _parse(self, unparsed):
        values = {}
        for arg in self._next_optional(values):
            arg.parse(unparsed, values)
        for arg in self._next_positional(values):
            arg.parse(unparsed, values)
        if 'mode' in values:
            subparser = self._subparsers[values['mode']]
            values.update(subparser.parse_args(unparsed))
        assert not unparsed
        for e in self._egroups:
            e.validate(values)
        return values

    def parse_args(self, unparsed):
        """
        Parse arguments.

        Takes a list of strings, and returns a dict of parsed args.
        """
        try:
            return self._parse(unparsed)
        except ArgumentError as e:
            raise e
        except Exception:
            raise ArgumentError(self.usage)

    def usage(self, command):
        usage = []
        for arg in self._args:
            egroups = [e for e in self._egroups if arg.name in e.args]
            if not egroups:
                usage.append(arg.usage())
                continue
            for e in egroups:
                eusage = e.usage(self._args)
                if eusage not in usage:
                    usage.append(eusage)
        usage = ' '.join(usage)

        if self._spname:
            return 'usage: !{} {} {}'.format(command, self._spname, usage)
        return 'usage: !{} {}'.format(command, usage)


class ArgumentError(Exception):

    def __init__(self, usage=None):
        self.usage = usage


###############################################################################
# Notes
###############################################################################


@parser
def tell(pr):
    pr.add_argument('topic', re='@.+', type=lambda x: x.lstrip('@'), nargs='?')
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
    pr.add_argument('date', type=arrow.get, nargs='?')
    pr.add_argument('span', re='(\d+[dhm])+')
    pr.exclusive('date', 'span', required=True)
    pr.add_argument('message', nargs='+', action='join')


###############################################################################
# SCP
###############################################################################


@parser
def random(pr):
    pr.add_argument('title', nargs='*', type=str.lower)
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


@parser
def help(pr):
    pr.add_argument('command', nargs='?')
    pr.add_argument('--elemental', '-e')

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

    claim = pr.subparser('claim')
    claim.add_argument('category')
    claim.add_argument('--purge', '-p')
