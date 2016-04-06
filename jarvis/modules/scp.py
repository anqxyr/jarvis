#!/usr/bin/env python3
"""All bot actions related to the scp-wiki."""


###############################################################################
# Module Imports
###############################################################################

import jarvis
import pyscp
import sopel

###############################################################################


def setup(bot):
    #pyscp.utils.default_logging(True)
    if bot.config.scp.debug:
        bot._wiki = pyscp.snapshot.Wiki('www.scp-wiki.net', 'test.db')
    else:
        bot._wiki = pyscp.wikidot.Wiki('scp-wiki')
    bot._stwiki = pyscp.wikidot.Wiki('scp-stats')
    bot._stwiki.auth(bot.config.scp.wikiname, bot.config.scp.wikipass)

    refresh_page_cache(bot)


###############################################################################
# Search And Lookup Commands
###############################################################################


@sopel.module.commands('author')
def author(bot, tr):
    """Output basic information about the author."""
    name = tr.group(2) if tr.group(2) else tr.nick
    bot.send(jarvis.scp.find_author(bot.memory['pages'], name, tr.sender))


@sopel.module.commands('search', 's')
def search(bot, tr):
    """
    Search for a wiki page.

    Attempts to match the search terms to one or more of the existing wiki
    pages. Search by the series titles of SCP articles is supported. When
    searching for multiple words, the order of the search terms is unimportant.

    Also searches among hubs, guides, and system pages.

    When multiple results are found, the extended information about each result
    can be accessed via the !showmore command.
    """
    bot.send(jarvis.scp.find_page(bot.memory['pages'], tr.group(2), tr.sender))


@sopel.module.rule(r'(?i)^(scp-[^ ]+)$')
@sopel.module.rule(r'(?i).*!(scp-[^ ]+)')
def scp(bot, tr):
    """Display page summary for the matching scp article."""
    bot.send(jarvis.scp.find_scp(bot.memory['pages'], tr.group(1), tr.sender))


@sopel.module.commands('tale')
def tale(bot, tr):
    """
    Search for a tale.

    Identical to the !search command, but returns only tales.

    When multiple results are found, the extended information about each result
    can be accessed via the !showmore command.
    """
    bot.send(jarvis.scp.find_tale(bot.memory['pages'], tr.group(2), tr.sender))


@sopel.module.commands('tags')
def tags(bot, tr):
    """
    Find pages by tag.

    Returns all pages that have **all** of the specified tags.

    When multiple results are found, the extended information about each result
    can be accessed via the !showmore command.
    """
    bot.send(jarvis.scp.find_tags(bot.memory['pages'], tr.group(2), tr.sender))


@sopel.module.commands('showmore', 'sm')
def showmore(bot, tr):
    """
    Access additional results.

    Must be used after a !search, !tale, or !tags command. Displays sumary of
    the specified result. Must be issued in the same channel as the search
    command.
    """
    bot.send(jarvis.tools.recall(tr.group(2), tr.sender))


@sopel.module.rule(r'(?i).*(http://www\.scp-wiki\.net/[^ ]+)')
def url(bot, tr):
    """Display page summary for the matching wiki page."""
    output = jarvis.scp.lookup_url(bot.memory['pages'], tr.group(1))
    if output:
        bot.send(output)


@sopel.module.commands('lastcreated', 'lc')
def lastcreated(bot, tr):
    """Display recently created pages."""
    pages = list(bot._wiki.list_pages(
        order='created_at desc', limit=3, body='created_by rating'))
    bot.send(' || '.join(map(jarvis.scp.get_page_summary, pages)))

###############################################################################
# Extended Stats
###############################################################################


@sopel.module.commands('ad')
def authordetails(bot, tr):
    name = tr.group(2) if tr.group(2) else tr.nick
    bot.send(jarvis.scp.update_author_details(
        bot.memory['pages'], name, bot._stwiki, tr.sender))


###############################################################################
# Misc Tools
###############################################################################


@sopel.module.commands('unused')
def unused(bot, tr):
    """Link to the first empty scp slot."""
    skips = ['scp-{:03}'.format(i) for i in range(2, 3000)]
    names = {p._body.name for p in bot.memory['pages']}
    unused = next(i for i in skips if i not in names)
    bot.send('http://www.scp-wiki.net/{}'.format(unused))


@sopel.module.commands('user')
def user(bot, tr):
    """Link to the user's profile page."""
    name = tr.group(2).lower().replace(' ', '-')
    bot.send('http://www.wikidot.com/user:info/{}'.format(name))


@sopel.module.commands('errors')
def errors(bot, tr):
    """Display pages with errors."""
    bot.send(jarvis.scp.get_error_report(bot.memory['pages']))


@sopel.module.interval(3600)
def refresh_page_cache(bot):
    bot.memory['pages'] = jarvis.ext.PageView(
        bot._wiki.list_pages(
            body='title created_by created_at rating tags',
            category='*'))

###############################################################################
