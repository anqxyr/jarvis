#!/usr/bin/env python3

###############################################################################
# Module Imports
###############################################################################

import sopel
import jarvis

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
        bot.send(jarvis.tools.choose_input([f.commands[0] for f in funcs]))
    else:
        wrapper = bot.SopelWrapper(bot, tr)
        bot.call(funcs[0], wrapper, tr)


@sopel.module.commands('choose')
def choose(bot, tr):
    """
    Randomly pick one of the options.

    The options must be comma-separated.
    """
    bot.send(jarvis.tools.choose(tr.group(2)))


@sopel.module.rule(r'(?i)(^(?:[+-]?[0-9]*d(?:[0-9]+|f))+(?:[+-][0-9]+)?$)')
@sopel.module.commands('roll', 'dice')
def dice(bot, tr):
    inp = tr.groups()[0] if len(tr.groups()) == 1 else tr.groups()[1]
    bot.send(jarvis.tools.roll_dice(inp))
