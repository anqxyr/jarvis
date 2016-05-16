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


def parser(usage):
    """Create Parser Decorator."""
    def outer_decorator(par):
        @functools.wraps(par)
        def inner_decorator(command):
            command._usage = usage

            @functools.wraps(command)
            def wrapped(inp, *args, **kwargs):
                if inp.text.endswith('--help'):
                    return usage
                try:
                    parsed_args = par(inp.text)
                except:
                    traceback.print_exc()
                    if not inp.text:
                        return usage
                    return lexicon.input.incorrect
                kwargs.update(parsed_args)
                return command(inp, *args, **kwargs)
            return wrapped
        return inner_decorator
    return outer_decorator


def get_flags(inp, *flags):
    """Retrieve flags from input string."""
    args = {f: False for f in flags}
    inp = inp.split()
    for i in inp:
        if i[0] != '-':
            continue
        for f in flags:
            if i == ('--' + f) or i == ('-' + f[0]):
                args[f] = True
                inp.remove(i)
    return ' '.join(inp), args


###############################################################################
# Notes
###############################################################################


@parser('!tell (<user> | @<topic>) <message>')
def tell(inp):
    """Argument parser for the notes.send_tell command."""
    uort, message = inp.split(maxsplit=1)
    user, topic = uort.lstrip('@').rstrip(':,'), None
    if uort[0] == '@':
        user, topic = topic, user
    if not user and not topic:
        raise ValueError
    return dict(user=user, topic=topic, message=message)


@parser('!outbound [--count | --purge]')
def outbound(inp):
    """Argument parser for the notes.outbound command."""
    if not inp:
        raise ValueError
    inp, args = get_flags(inp, 'count', 'purge')
    if inp or (args['count'] and args['purge']):
        raise ValueError
    return args


@parser('!seen <user> [--first]')
def seen(inp):
    """Argument parser for the notes.seen command."""
    inp, args = get_flags(inp, 'first')
    args.update(user=inp.lower())
    return args


@parser('!quote [add|del] [<user>] [<index>]')
def quote(inp):
    """Argument parser for the notes.quote command."""
    if not inp or inp.split()[0].lower() not in ('add', 'del'):
        mode = None
    else:
        mode = inp.split()[0].lower()
    return dict(mode=mode)


@parser('!quote add [<date>] <user> <message>')
def quote_add(inp):
    """Argument parser for the notes.quote_add command."""
    _, user, message = inp.split(maxsplit=2)
    try:
        date = arrow.get(user, 'YYYY-MM-DD').format('YYYY-MM-DD')
        user, message = message.split(maxsplit=1)
    except arrow.parser.ParserError:
        date = None
    return dict(date=date, user=user.lower(), message=message)


@parser('!quote del <user> <message>')
def quote_del(inp):
    """Argument parser for the notes.quote_del command."""
    _, user, message = inp.split(maxsplit=2)
    return dict(user=user, message=message)


@parser('!quote [<user>] [<index>]')
def quote_get(inp):
    """Argument parser for the notes.quote_add command."""
    inp = inp.lower().split()
    user = index = None
    if len(inp) == 1:
        try:
            index = int(inp[0])
        except ValueError:
            user = inp[0]
    elif len(inp) == 2:
        user = inp[0]
        index = int(inp[1])
    elif len(inp) > 2:
        raise ValueError
    if index is not None and index <= 0:
        raise ValueError
    return dict(user=user, index=index)


@parser('!rem <user> <message>')
def save_memo(inp):
    user, message = inp.split(maxsplit=1)
    return dict(user=user, message=message)


@parser('!topic <topic> [-r][-f][-s][-u][-l]')
def topic(inp):
    inp, args = get_flags(
        inp, 'restrict', 'free', 'subscribe', 'unsubscribe', 'list')
    if len(inp.split()) != 1 or list(args.values()).count(True) != 1:
        raise ValueError
    action = [k for k, v in args.items() if v][0]
    return dict(topic=inp.lstrip('@'), action=action)


@parser('!alert [<date>|<delay>] <message>')
def alert(inp):
    date, message = inp.split(maxsplit=1)
    try:
        arrow.get(date, 'YYYY-MM-DD')
        delay = None
    except arrow.parser.ParserError:
        delay = date
        date = None
    if not re.match(r'((\d+)([dhm]))+$', delay):
        raise ValueError
    return dict(date=date, delay=delay, message=message)

###############################################################################
# SCP
###############################################################################


@parser('!s <title> [-e][-s][-t][-a][-r]')
def search(inp):
    pass