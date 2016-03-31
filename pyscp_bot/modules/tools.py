#!/usr/bin/env python3

###############################################################################
# Module Imports
###############################################################################

import random
import sopel
import pyscp_bot.jarvis as vocab

###############################################################################


@sopel.module.commands('[^ ]+')
def autocomplete(bot, trigger):
    funcs = [f for group in bot._callables.values() for f in group.values()]
    funcs = [f for l in funcs for f in l if hasattr(f, 'commands')]
    partial = trigger.group(1)
    if any(partial in f.commands for f in funcs):
        return
    funcs = [
        f for f in funcs if any(c.startswith(partial) for c in f.commands)]
    if not funcs:
        return
    if len(funcs) > 1:
        names = [f.commands[0] for f in funcs]
        bot.say('{}: did you mean {} or {}?'.format(
            trigger.nick, ', '.join(names[:-1]), names[-1]))
    else:
        wrapper = bot.SopelWrapper(bot, trigger)
        bot.call(funcs[0], wrapper, trigger)


@sopel.module.commands('choose')
def choose(bot, trigger):
    """
    Randomly pick one of the options.

    The options must be comma-separated.
    """
    options = [i.strip() for i in trigger.group(2).split(',')]
    bot.say('{}: {}'.format(trigger.nick, random.choice(options)))
