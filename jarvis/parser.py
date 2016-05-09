#!/usr/bin/env python3
"""
Jarvis Parser Module.

Contains argument parsers for other commands.
"""
###############################################################################
# Module Imports
###############################################################################

import functools

###############################################################################
# Generic Functionality
###############################################################################


def parser(usage):
    """Create Parser Decorator."""
    def outer_decorator(par):
        @functools.wraps(par)
        def inner_decorator(command):
            @functools.wraps(command)
            def wrapped(inp, *args, **kwargs):
                usage = '!{} {}'.format(command.__name__, usage)
                if not inp.text or inp.text == '--help':
                    return usage
                try:
                    parsed_args = par(inp.text)
                except:
                    return usage
                kwargs.update(parsed_args)
                return command(inp, *args, **kwargs)
            return wrapped
        return inner_decorator
    return outer_decorator


def get_flags(inp, *flags):
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


@parser('(<user> | @<topic>) <message>')
def tell(inp):
    """Argument parser for the notes.send_tell command."""
    uort, message = inp.split(maxsplit=1)
    user, topic = uort.lstrip('@').rstrip(':,'), None
    if uort[0] == '@':
        user, topic = topic, user
    return dict(user=user, topic=topic, message=message)


@parser('[--count | --purge]')
def outbound(inp):
    """Argument parser for the notes.outbound command."""
    inp, args = get_flags(inp, 'count', 'purge')
    if inp or (args['count'] and args['purge']):
        raise ValueError
    return args


@parser('<user> [--first]')
def seen(inp):
    """Argument parser for the notes.seen command."""
    inp, args = get_flags(inp, 'first')
    args.update(user=inp)
    return args
