#!/usr/bin/env python3

###############################################################################
# Module Imports
###############################################################################

import random
import sopel
import pyscp_bot as jarvis

###############################################################################


@sopel.module.commands('[^ ]+')
def autocomplete(bot, tr):
    funcs = [f for group in bot._callables.values() for f in group.values()]
    funcs = {f for l in funcs for f in l if hasattr(f, 'commands')}
    partial = tr.group(1)
    if any(partial in f.commands for f in funcs):
        return
    funcs = [
        f for f in funcs if any(c.startswith(partial) for c in f.commands)]
    if not funcs:
        return
    if len(funcs) > 1:
        names = [f.commands[0] for f in funcs]
        bot.send('Did you mean {} or {}?'.format(
            ', '.join(names[:-1]), names[-1]))
    else:
        wrapper = bot.SopelWrapper(bot, tr)
        bot.call(funcs[0], wrapper, tr)


@sopel.module.commands('choose')
def choose(bot, tr):
    """
    Randomly pick one of the options.

    The options must be comma-separated.
    """
    options = [i.strip() for i in tr.group(2).split(',')]
    bot.send(random.choice(options))


@sopel.module.rule(r'(?i)(^(?:[+-]?[0-9]*d(?:[0-9]+|f))+(?:[+-][0-9]+)?$)')
@sopel.module.commands('roll', 'dice')
def dice(bot, tr):
    inp = tr.groups()[0] if len(tr.groups()) == 1 else tr.groups()[1]
    bot.send(jarvis.tools.roll_dice(inp))
