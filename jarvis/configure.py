#!/usr/bin/env python3
"""The .conf command and its subcommands."""

###############################################################################
# Module Imports
###############################################################################


from . import core, parser, lex


###############################################################################


@core.command
@parser.configure
def configure(inp, mode, **kwargs):
    """TODO: docstring."""
    return configure.dispatch(inp, mode, **kwargs)


def _configurable(inp, name, states, value):
    states = states.split()
    if not value:
        current = getattr(inp.config, name)
        value = states[states.index(current) - 1]
    setattr(inp.config, name, value)
    return getattr(lex.configure, name)(state=value)


@configure.subcommand('memos')
@core.require(level=4)
def memos(inp, *, value):
    """
    Toggle memo settings for this channel.

    Possible values is 'off', 'alphanumeric', and 'all'.

    'off' will disable memos and quotes in the channel.

    'alphanumeric' limits possible usernames in memos and quotes to
    alphanumeric characters, preventing lines such as '???' from being
    interpreted as memo pull up requests.

    'all' allows unrestricted memo use.

    Defaults to 'all'. Can only be changed by channel operators.
    """
    return _configurable(inp, 'memos', 'off all alphanumeric', value)


@configure.subcommand('lcratings')
@core.require(level=4)
def lcratings(inp, *, value):
    """
    Toggle lcratings setting for this channel.

    Determines whether article ratings will be displayed by the .lc command.

    Defaults to 'on'.
    """
    return _configurable(inp, 'lcratings', 'on off', value)
