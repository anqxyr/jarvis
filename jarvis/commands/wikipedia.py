#!/usr/bin/env python3

###############################################################################
# Module Imports
###############################################################################

import wikipedia as wiki

from jarvis import core, parser, lex, tools


###############################################################################
# Parser
###############################################################################

@parser.parser
def prwiki(pr):
    pr.add_argument(
        'query',
        nargs='+',
        action='join',
        help="""Terms for which you wish to search.""")


###############################################################################
# Command
###############################################################################


@core.command
@core.alias('w')
@prwiki
def wikipedia(inp, *, query):
    """Get wikipedia page about the topic."""
    try:
        page = wiki.page(query)
    except wiki.exceptions.PageError:
        return lex.wikipedia.not_found
    except wiki.exceptions.DisambiguationError as e:
        tools.save_results(inp, e.options, lambda x: wikipedia(inp, query=x))
        return lex.unclear(options=e.options)

    return lex.wikipedia.result(
        title=page.title, url=page.url, text=page.content)
