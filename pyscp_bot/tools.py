#!/usr/bin/env python3
"""Misc. bot commands."""

###############################################################################
# Module Imports
###############################################################################

import random
import re

from . import lexicon


def choose(inp):
    """Return one random comma-separated option."""
    options = [i.strip() for i in inp.split(',')]
    return random.choice(options)


def roll_dice(inp):
    """Return the result of rolling multiple dice."""
    rolls = re.findall(r'([+-]?)([0-9]*)d([0-9]+|f)', inp)
    total = 0

    def roll_die(sign, count, sides):
        nonlocal total
        results = [random.randint(1, int(sides)) for _ in range(count)]
        if sign == '-':
            results = [-i for i in results]
        total += sum(results)
        return results

    def roll_fudge_die(count):
        nonlocal total
        results = [random.choice(['+1', '0', '-1']) for _ in range(count)]
        total += sum(map(int, results))
        return [i[0] for i in results]

    results = []
    for sign, count, sides in rolls:
        count = int(count) if count else 1
        if count > 5000:
            return lexicon.too_many_dice()
        if sides == 'f':
            results.extend(roll_fudge_die(count))
        elif int(sides) < 2:
            return lexicon.bad_die()
        else:
            results.extend(roll_die(sign, count, sides))
    results = ', '.join(map(str, results))
    results = results.replace('+', '\x033+\x0F').replace('-', '\x034-\x0F')

    bonus = re.search(r'[+-][0-9]+$', inp)
    if bonus:
        total += int(bonus.group(0))

    return '{} ({}={})'.format(total, inp, results)
