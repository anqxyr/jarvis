#!/usr/bin/env python3

###############################################################################
# Module Imports
###############################################################################

import random as rand
import itertools

from jarvis import core, parser, lex


###############################################################################
# Parser
###############################################################################


@parser.parser
def prunused(pr):
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
        '--series', '-s',
        nargs='+',
        type=int,
        re='[1-4]',
        help="""Only check slots within the given series.""")

    pr.exclusive('random', 'last', 'count')


###############################################################################
# Command
###############################################################################


@core.command
@prunused
def unused(inp, *, random, last, count, prime, palindrome, divisible, series):
    """Get the first unused scp slot."""
    series = [0, 1, 2, 3] if not series else [i - 1 for i in set(series)]
    series = [i * 1000 for i in series]
    numbers = itertools.chain.from_iterable(
        range(i or 2, i + 1000) for i in series)

    if prime:
        numbers = [i for i in numbers if all(i % k for k in range(2, i))]
    if palindrome:
        numbers = [
            i for i in numbers if str(i).zfill(3) == str(i).zfill(3)[::-1]]
    if divisible:
        numbers = [i for i in numbers if i % divisible == 0]

    slots = ['scp-{:03d}'.format(i) for i in numbers]
    used_slots = {p.name for p in core.pages}
    unused_slots = [i for i in slots if i not in used_slots]

    if not unused_slots:
        return lex.unused.not_found

    if count:
        return lex.unused.count(count=len(unused_slots))

    if random:
        result = rand.choice(unused_slots)
    elif last:
        result = unused_slots[-1]
    else:
        result = unused_slots[0]

    return lex.unused.found(slot=result)
