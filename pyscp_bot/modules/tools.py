#!/usr/bin/env python3

###############################################################################
# Module Imports
###############################################################################

import random
import sopel
import pyscp_bot.jarvis as vocab

###############################################################################


@sopel.module.commands('[^ ]*')
def autocomplete(bot, trigger):
    commands = {command: module
                for module, group in bot._command_groups.items()
                for command in group}
    partial = trigger.group(1)
    if partial in commands:
        return
    matches = {k: v for k, v in commands.items() if k.startswith(partial)}
    if not matches:
        return
    if len(matches) == 1:
        name, module = list(matches.items())[0]
        items = [i for pr, gr in bot._callables.items() for i in gr.items()]
        funcs = [f[0] for regexp, f in items]
        funcs = [
            f for f in funcs if f.__module__ == module and f.__name__ == name]
        wrapper = bot.SopelWrapper(bot, trigger)
        bot.call(funcs[0], wrapper, trigger)
        return
    commands = ['\x02{}\x02'.format(k) for k in matches]
    bot.say('{}: did you mean {} or {}?'.format(
        trigger.nick, ', '.join(commands[:-1]), commands[-1]))


@sopel.module.commands('choose')
def choose(bot, trigger):
    """
    Randomly pick one of the options.

    The options must be comma-separated.
    """
    options = [i.strip() for i in trigger.group(2).split(',')]
    bot.say('{}: {}'.format(trigger.nick, random.choice(options)))
