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
            func._parser = self._parser._subparsers[mode]
            return func

        return inner

    def dispatch(self, inp, mode, *args, **kwargs):
        return self._subcommands[mode](inp, *args, **kwargs)

###############################################################################
# ArgumentParser
###############################################################################


class PositionalArgument:

    def __init__(self, parser, *args, **kwargs):
        self.parser = parser
        self.name = args[0].lstrip('-').replace('-', '_')
        self.flags = []

        self.is_optional = False

        self.nargs = kwargs.get('nargs', 1)

        self.action = kwargs.get('action')

        self.re = kwargs.get('re')
        self.type = kwargs.get('type')
        self.choices = kwargs.get('choices')

        self.help = kwargs.get('help')
        if self.help:
            self.help = ' '.join([i.strip() for i in self.help.split('\n')])

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
            # do not consume other optional args
            if bit in [f for i in self.parser._args for f in i.flags]:
                break
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

    def __init__(self, parser, *args, **kwargs):
        kwargs.setdefault('nargs', 0)
        super().__init__(parser, *args, **kwargs)
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
        self._args.append(cls(self, *args, **kwargs))

    def exclusive(self, *args, required=False):
        self._egroups.append(ExclusiveGroup(args, required))

    def subparser(self, mode=None):
        if not any(i.name == 'mode' for i in self._args):
            self.add_argument(
                'mode',
                nargs='?' if mode is None else 1,
                choices=[mode], type=str.lower,
                help="""Name of the subcommand to execute.""")
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
    pr.add_argument(
        'user',
        type=lambda x: x.lower().rstrip(':,'),
        #re=r'(?i)\A[a-z_\-\[\]\\^{}|`][a-z0-9_\-\[\]\\^{}|`]*\z',
        help="""IRC username of the user to whom the message is intended.""")

    pr.add_argument(
        'message',
        nargs='+',
        action='join',
        help="""Text of the message.""")


@parser
def masstell(pr):
    pr.add_argument(
        'names',
        type=lambda x: x.lower().rstrip(':,'),
        nargs='*',
        re='(?!^\|$)',
        help="""IRC usernames of the users to whom the message is intended.
                Space-separated. Commas are automatically stripped off.""")

    pr.add_argument(
        'separator',
        re='\|',
        nargs='?',
        help="""The '|' character, used to separate the list of names from
                the text of the tell.""")

    pr.add_argument(
        'text',
        nargs='*',
        action='join',
        help="""Text of the tell, to be sent to all the specified users.""")

    pr.add_argument(
        '--users', '--cc',
        type=lambda x: x.lower().rstrip(':,'),
        nargs='+',
        help="""IRC usernames of the users to whom the message is intended.
                Space-separated. Commas are automatically stripped off.

                This is the depricated version of the argument. You should
                use the 'names' positional argument instead.""")

    pr.add_argument(
        '--message', '--text',
        nargs='+',
        action='join',
        help="""Text of the message.

                This is the depricated version of the argument. You should
                use the 'text' positional argument instead.""")


@parser
def outbound(pr):
    pr.add_argument(
        '--purge', '-p',
        nargs='?',
        type=str.lower,
        help="""Purge outbound tells. If a username is specified, the command
                will delete the tells sent to that user. Otherwise, all
                outbound tells will be deleted.""")

    pr.add_argument(
        '--echo', '-e',
        help="""Print all outbound tells. Full text and send time of each tell
                will be displayed.""")

    pr.exclusive('purge', 'echo')


@parser
def seen(pr):
    pr.add_argument(
        '--first', '-f',
        help="""Display the first recorded message said by the user.""")

    pr.add_argument(
        '--total', '-t',
        help="""Display the total number of messages said by the user.""")

    pr.add_argument(
        '--date', '-d',
        help="""Display exact date.""")

    pr.exclusive('first', 'total')

    pr.add_argument(
        'channel',
        re='#',
        nargs='?',
        help="""Switch to another channel.""")

    pr.add_argument(
        'user',
        type=str.lower,
        help='Username to look for.')


@parser
def quote(pr):
    pr.add_argument(
        'channel',
        re='#',
        nargs='?',
        help="""Switch to another channel.""")

    ###########################################################################

    get = pr.subparser()

    get.add_argument(
        'user',
        re=r'.*[^\d].*',
        type=str.lower,
        nargs='?',
        help="""Find a quote by the given user.""")

    get.add_argument(
        'index',
        type=int,
        nargs='?',
        help="""Get the quote at the given index.""")

    ###########################################################################

    add = pr.subparser('add')

    add.add_argument(
        'date',
        nargs='?',
        type=arrow.get,
        re=r'\d{4}-\d{2}-\d{2}',
        help="""Override the quote creation time with the given date
                in the YYYY-MM-DD format.""")

    add.add_argument(
        'user',
        type=str.lower,
        help="""Name of the user being quoted.""")

    add.add_argument(
        'message',
        nargs='+',
        action='join',
        help="""Text of the quote.""")

    ###########################################################################

    delete = pr.subparser('del')

    delete.add_argument(
        'user',
        type=lambda x: x.lower().rstrip(',:'),
        help="""Name of the user whose quote is being deleted.""")

    delete.add_argument(
        'index',
        type=int,
        help="""Index of the quote to be deleted.""")


@parser
def memo(pr):
    pr.add_argument(
        'channel',
        re='#',
        nargs='?',
        help="""Switch to another channel.""")

    pr.subparser().add_argument(
        'user',
        type=str.lower,
        help="""Name of the user whose memo is being retrieved.""")

    ###########################################################################

    add = pr.subparser('add')

    add.add_argument(
        'user',
        type=str.lower,
        help="""Name of the user whose memo is being added.""")

    add.add_argument(
        'message',
        nargs='+',
        action='join',
        help="""Text of the memo.""")

    ###########################################################################

    append = pr.subparser('append')

    append.add_argument(
        'user',
        type=str.lower,
        help="""Name of the user whose memo is being appended.""")

    append.add_argument(
        'message',
        nargs='+',
        action='join',
        help="""Text to be appended to the memo.""")

    ###########################################################################

    delete = pr.subparser('del')

    delete.add_argument(
        'user',
        type=lambda x: x.lower().rstrip(',:'),
        help="""Name of the user whose memeo is being deleted.""")

    ###########################################################################

    pr.subparser('count')


@parser
def rem(pr):
    pr.add_argument(
        'user',
        type=str.lower,
        help="""Name of the user whose memo is being added.""")

    pr.add_argument(
        'message',
        nargs='+',
        action='join',
        help="""Text of the memo.""")


@parser
def alert(pr):
    aset = pr.subparser('set')

    aset.add_argument(
        'date',
        type=arrow.get,
        nargs='?',
        help="""Date in YYYY-MM-DD format.""")

    aset.add_argument(
        'span',
        re='(\d+[dhm])+',
        help="""Time to wait before the alert, for example 2d3h4m.""")

    aset.exclusive('date', 'span', required=True)

    aset.add_argument(
        'message',
        nargs='+',
        action='join',
        help="""Alert text.""")

    ###########################################################################

    pr.subparser('echo')


@parser
def gibber(pr):
    pr.add_argument(
        'channel',
        re='#',
        nargs='?',
        help="""Switch to another channel.""")

    pr.add_argument(
        'user',
        type=str.lower,
        nargs='?',
        help="""What would <user> say?""")

    pr.add_argument(
        '--quotes', '-q',
        help="""Use quotes instead of history as source of the gib.""")


###############################################################################
# SCP
###############################################################################


@parser
def random(pr):
    pr.add_argument(
        'title',
        nargs='*',
        type=str.lower,
        help="""Search for pages whose title contains the given words.""")

    pr.add_argument(
        '--exclude', '-e',
        nargs='+',
        type=str.lower,
        help="""Exclude pages whose title contains the given words.""")

    pr.add_argument(
        '--strict', '-s',
        nargs='+',
        type=str.lower,
        help="""An analogue of the [title] argument with strict
                word matching. Unlike the former, specifying '--strict part'
                will *not* return matches whose title contains 'particle'.""")

    pr.add_argument(
        '--tags', '-t',
        nargs='+',
        action='join',
        type=str.lower,
        help="""Limit results to pages with specified tags.
                Follows the normal +/- wikidot tag notation.""")

    pr.add_argument(
        '--author', '-a',
        nargs='+',
        action='join',
        type=str.lower,
        help="""Limit results to pages written by the specified user.
                Rewrites are supported. Unlike .au, this argument does not
                attempt to divine the name of the user based on a partial
                input. Full exact case-insensitive wikidot username must
                be provided.""")

    pr.add_argument(
        '--rating', '-r',
        re=r'([><=]?\d+)|(\d+\.\.\d+)',
        nargs=1,
        help="""Limit results to pages with the specified rating. Supports
                exact ratings (20, =20); ratings above or below a given value
                (>100, <-10); or a range of ratings (20..50).""")

    pr.add_argument(
        '--created', '-c',
        nargs=1,
        help="""Limit results to pages created on the given date. Dates must
                follow the YYYY-MM-DD format. Partial dates are supported:
                specifying -c 2014-01 will return only pages created in
                January of 2014. Dates before or after (>2012 or <2015-10-05);
                as well as date ranges (2013-02-10..2013-02-20) are
                likewise supported.""")

    pr.add_argument(
        '--fullname', '-f',
        nargs='+',
        action='join',
        type=str.lower,
        help="""Find a page by exact full name.""")


@parser
def search(pr):
    # search and random are almost the same
    # except search has one more argument
    random.__wrapped__(pr)
    pr.add_argument(
        '--summary', '-u',
        help="""Instead of showing the results of the search, output summary
                information about the found pages.""")


@parser
def unused(pr):
    pr.add_argument(
        '--random', '-r',
        help="""Return a random slot.""")

    pr.add_argument(
        '--last', '-l',
        help='Return the last slot.')

    pr.add_argument(
        '--count', '-c',
        help="""Return the number of matching slots.""")

    pr.add_argument(
        '--prime', '-p',
        help="""Limit matches to prime-numbered slots.""")

    pr.add_argument(
        '--palindrome', '-i',
        help="""Limit matches to slots whose number is a palindrome.""")

    pr.add_argument(
        '--divisible', '-d',
        nargs=1,
        type=int,
        help="""Limit matches to slots divisible by a given number.
                For example, '.unused -d 100' will return slots that
                end wtih 00.""")
    
    pr.add_argument(
        '--pattern', '-x',
        nargs=1,
        type=str.lower,
        re='[A-Za-z]{3,4}',
        help="""Limit matches to slots that match the given pattern.""")

    pr.add_argument(
        '--series', '-s',
        nargs='+',
        type=int,
        re='[1-5]',
        help="""Only check slots within the given series.""")

    pr.exclusive('random', 'last', 'count')


@parser
def contest(pr):
    pr.add_argument(
        'name',
        nargs='*',
        action='join',
        type=str.lower,
        re='^[a-z].*',
        help="""Find contests by partial or full name.""")

    pr.add_argument(
        'year',
        nargs='?',
        type=int,
        help="""Find contests run in the given year.""")


###############################################################################
# Tools
###############################################################################


@parser
def showmore(pr):
    pr.add_argument(
        'index',
        nargs='?',
        type=int,
        help="""Index of the stored result you wish to see,
                starting with 1.""")


@parser
def dice(pr):
    pr.add_argument(
        'throws',
        nargs='+',
        re=r'(?i)[+-]?[0-9]*d([0-9]+|f)$',
        type=str.lower,
        help="""One or more dice throws to be calculated.""")

    pr.add_argument(
        'bonus',
        nargs='?',
        type=int,
        help="""Bonus value to be added to or substracted from
                the final result.""")

    pr.add_argument(
        'text',
        nargs='*',
        action='join',
        help="""Description of the throw.""")

    pr.add_argument(
        '--expand', '-e',
        help="""Display detailed information about each thrown die.""")


@parser
def help(pr):
    pr.add_argument('command', nargs='*', action='join')
    pr.add_argument('--elemental', '-e', nargs='*')


@parser
def onpage(pr):
    pr.add_argument(
        'user',
        nargs='+',
        type=str.lower,
        action='join',
        help="""Wikidot username of the user in question.""")

    pr.add_argument(
        '--oldest-first', '-o',
        help="""Start the search with oldest users.""")


@parser
def convert(pr):
    pr.add_argument(
        'expression',
        nargs='+',
        action='join',
        help="""Conversion expression. Must follow the form of
                "<number> <unit> to <unit>".""")

    pr.add_argument(
        '--precision', '-p',
        nargs='?',
        type=int,
        help="""Specify conversion precision. By default .convert will attempt
                to preserve the significant figures of the input value.
                This parameter overrides the default behaviour. Positive
                precision values correspond to the number of digits displayed
                after the decimal point. Negative precision values will
                round the result value to the nearest ten, hundred, thousand,
                etc.""")


@parser
def name(pr):
    person = pr.subparser()

    person.add_argument(
        '--male', '-m',
        help="""Generate male name.""")

    person.add_argument(
        '--female', '-f',
        help="""Generate female name.""")

    person.add_argument(
        '--first', '--given', '-g',
        help="""Only generate the first name.""")

    person.add_argument(
        '--last', '-l',
        help="""Only generate the family name.""")

    person.add_argument(
        '--prefix', '-p',
        help="""Add a prefix to the name.""")

    person.add_argument(
        '--suffix', '-s',
        help="""Add a suffix to the name.""")

    person.exclusive('male', 'female')
    person.exclusive('first', 'last')


@parser
def say(pr):
    pr.add_argument(
        'channel',
        type=str.lower,
        re='#.+')

    pr.add_argument(
        'text',
        nargs='+',
        action='join')

###############################################################################
# Websearch
###############################################################################


@parser
def websearch(pr):
    pr.add_argument(
        'query',
        nargs='+',
        action='join',
        help="""Terms for which you wish to search.""")


@parser
def dictionary(pr):
    pr.add_argument(
        'query',
        nargs='+',
        action='join',
        help="""A word or a phrase.""")


@parser
def google(pr):
    pr.add_argument(
        'query',
        nargs='+',
        action='join',
        help="""Your search query.""")

    pr.add_argument(
        '--index', '-i',
        nargs=1,
        type=int,
        help="""Number of the result to show, between 1 and 10.""")


@parser
def youtube(pr):
    pr.add_argument(
        'query',
        nargs='+',
        action='join',
        help="""Your search query.""")

    pr.add_argument(
        '--index', '-i',
        nargs=1,
        type=int,
        help="""Number of the result to show, between 1 and 10.""")


@parser
def translate(pr):
    pr.add_argument(
        'lang',
        help="""Langauge codes for source and target language. For example,
                specifying ru-fr will translate your text from Russian into
                French. The source language can be optionally omitted.""")

    pr.add_argument(
        'query',
        nargs='+',
        action='join',
        help="""Text you wish to translate.""")


@parser
def imdb(pr):
    pr.add_argument(
        'title',
        nargs='+',
        action='join',
        help="""Exact title of a movie or tv show.""")
    pr.add_argument(
        '--search', '-s',
        nargs='+',
        action='join',
        help="""Search for movies whose title contains the specified words.""")
    pr.add_argument(
        '--imdbid', '-i',
        nargs=1,
        help="""Show the movie with the given imdb id.""")
    pr.exclusive('title', 'search', 'imdbid')
    pr.add_argument(
        '--year', '-y',
        nargs=1,
        type=int,
        help="""Limit results to those released in the specified year.""")


@parser
def duckduckgo(pr):
    pr.add_argument(
        'query',
        nargs='+',
        action='join',
        help="""Your search query.""")

    pr.add_argument(
        '--index', '-i',
        nargs=1,
        type=int,
        help="""Number of the result to show, between 1 and 30.""")


@parser
def steam(pr):
    pr.add_argument(
        'title',
        nargs='+',
        action='join',
        type=str.lower,
        help="""Title of the game to search for.""")


@parser
def kaktuskast(pr):
    pr.add_argument(
        'podcast',
        nargs='*',
        re='^[a-z].*',
        type=str.lower,
        action='join',
        help="""Partial name of the podcast to look for.
                Defaults to Kaktuskast.""")

    pr.add_argument(
        'index',
        nargs='?',
        type=int,
        help="""Index of the episode to look up.""")

###############################################################################
# Images
###############################################################################


@parser
def images(pr):

    pr.subparser('scan').add_argument(
        'pages',
        nargs='+',
        help="""Names of pages to be scanned for unindexed images.""")

    ###########################################################################

    update = pr.subparser('update')

    update.add_argument(
        'target',
        help="""Page name or image url indicating which image to target.""")

    update.add_argument(
        'index',
        nargs='?',
        type=int,
        help="""For pages with multiple images,
                index specifies which image to use.""")

    update.add_argument(
        '--url', '-u',
        nargs=1,
        help="""Update the url of the image. Useful when the image was
                rehosted or reuploaded.""")

    update.add_argument(
        '--page', '-p',
        nargs=1,
        help="""Update the page on which the image resides.""")

    update.add_argument(
        '--source', '--origin', '-o',
        nargs=1,
        help="""Update the origin of the image. Should be a full valid url.""")

    update.add_argument(
        '--status', '-s',
        nargs='+',
        type=str.upper,
        action='join',
        help="""Update the image status.""")

    update.add_argument(
        '--notes', '-n',
        nargs='+',
        action='join',
        help="""Add a note. Only addes one note, and only if no notes are
                present already. If more notes needs to be added,
                use .im notes instead.""")

    ###########################################################################

    list_ = pr.subparser('list')

    list_.add_argument(
        'target',
        help="""Page name or image url indicating which image to target.""")

    list_.add_argument(
        'index',
        nargs='?',
        type=int,
        help="""For pages with multiple images,
                index specifies which image to use.""")

    list_.add_argument(
        '--terse', '-t',
        help="""Do not show full urls.""")

    ###########################################################################

    notes = pr.subparser('notes')

    notes.add_argument(
        'target',
        help="""Page name or image url indicating which image to target.""")

    notes.add_argument(
        'index',
        nargs='?',
        type=int,
        help="""For pages with multiple images,
                index specifies which image to use.""")

    notes.add_argument(
        '--append', '-a',
        nargs='+',
        action='join',
        help="""Add a new note to the image.""")

    notes.add_argument(
        '--purge', '-p',
        help="""Delete all notes from the record.""")

    notes.add_argument(
        '--list', '-l',
        help="""Display all notes.""")

    notes.exclusive('append', 'purge', 'list')

    ###########################################################################

    purge = pr.subparser('purge')

    purge.add_argument(
        'target',
        help="""Page name or image url indicating which image to target.""")

    purge.add_argument(
        'index',
        nargs='?',
        type=int,
        help="""For pages with multiple images,
                index specifies which image to use.""")

    ###########################################################################

    search = pr.subparser('search')

    search.add_argument(
        'target',
        help="""Page name or image url indicating which image to target.""")

    search.add_argument(
        'index',
        nargs='?',
        type=int,
        help="""For pages with multiple images,
                index specifies which image to use.""")

    ###########################################################################

    pr.subparser('stats').add_argument(
        'category',
        help="""Name of the category for which to display the stats.""")

    ###########################################################################

    pr.subparser('sync')

    add = pr.subparser('add')

    add.add_argument(
        'url',
        help="""Full url of the image.""")

    add.add_argument(
        'page',
        nargs='?',
        help="""Name of the parent page.""")

    ###########################################################################

    remove = pr.subparser('remove')

    remove.add_argument(
        'page',
        help="""Name of the page.""")

    remove.add_argument(
        'images',
        nargs='+',
        help="""Full urls of all the images that must be removed.""")

    ###########################################################################

    pr.subparser('attribute').add_argument(
        'page',
        help="""Name of the page to be attributed.""")

    ###########################################################################

    claim = pr.subparser('claim')

    claim.add_argument(
        'category',
        help="""Name of the category.""")

    claim.add_argument(
        '--purge', '-p',
        help="""Delete claim.""")

    ###########################################################################

    pr.subparser('tagcc')


###############################################################################
# Configure
###############################################################################


@parser
def configure(pr):

    memos = pr.subparser('memos')

    memos.add_argument(
        'value',
        nargs='?',
        choice=['off', 'all', 'alphanumeric'],
        help="""New value of the configured parameter.""")

    ###########################################################################

    # this is a narrowly targeted type to be used in .conf values
    def bool_string(value):
        if value.lower() in ['yes', 'on', 'true', 'enable']:
            return True
        elif value.lower() in ['no', 'off', 'false', 'disable']:
            return False
        else:
            raise ValueError

    toggleables = ['lcratings', 'keeplogs', 'urbandict', 'gibber']

    for name in toggleables:
        subpr = pr.subparser(name)

        subpr.add_argument(
            'value',
            nargs='?',
            type=bool_string,
            help="""New value of the configured parameter.""")

    ###########################################################################
