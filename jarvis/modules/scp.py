#!/usr/bin/env python3
"""All bot actions related to the scp-wiki."""


###############################################################################
# Module Imports
###############################################################################

import pyscp
import re
import sopel

import jarvis

###############################################################################


def setup(bot):
    #pyscp.utils.default_logging(True)
    if bot.config.scp.debug:
        bot._wiki = pyscp.snapshot.Wiki('www.scp-wiki.net', 'test.db')
    else:
        bot._wiki = pyscp.wikidot.Wiki('scp-wiki')
        #bot._wiki.auth('pyscp_bot', bot.config.scp.wikipass)
    refresh_page_cache(bot)
    bot.memory['search'] = {}


def configure(config):
    config.define_section('scp')

###############################################################################
# Search And Lookup Commands
###############################################################################


@sopel.module.commands('author')
def find_author(bot, tr):
    """Output basic information about the author."""
    name = tr.group(2) if tr.group(2) else tr.nick
    bot.send(jarvis.scp.find_author(bot.memory['pages'], name, tr.sender))


@sopel.module.commands('search', 's')
def find_page(bot, tr):
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
def find_scp(bot, tr):
    """Display page summary for the matching scp article."""
    bot.send(jarvis.scp.find_scp(bot.memory['pages'], tr.group(2), tr.sender))


@sopel.module.commands('tale')
def find_tale(bot, tr):
    """
    Search for a tale.

    Identical to the !search command, but returns only tales.

    When multiple results are found, the extended information about each result
    can be accessed via the !showmore command.
    """
    bot.send(jarvis.scp.find_tale(bot.memory['pages'], tr.group(2), tr.sender))


@sopel.module.rule(r'(?i).*(http://www\.scp-wiki\.net/[^ ]+)')
def url_lookup(bot, tr):
    """Display page summary for the matching wiki page."""
    url = tr.group(1)
    if '/forum/' in url:
        return
    name = url.split('/')[-1]
    pages = [p for p in bot.memory['pages'] if p._body.name == name]
    if not pages:
        bot.send(jarvis.lexicon.page_not_found())
    else:
        bot.send(page_summary(pages[0]))

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


@sopel.module.commands('tags')
def tags(bot, tr):
    """
    Find pages by tag.

    Returns all pages that have **all** of the specified tags.

    When multiple results are found, the extended information about each result
    can be accessed via the !showmore command.
    """
    tags = set(tr.group(2).lower().split())
    pages = [p for p in bot.memory['pages'] if p.tags.issuperset(tags)]
    bot.memory['search'][tr.sender] = pages
    show_search_results(bot, tr, pages)


@sopel.module.commands('showmore', 'sm')
def showmore(bot, tr):
    """
    Access additional results.

    Must be used after a !search, !tale, or !tags command. Displays sumary of
    the specified result. Must be issued in the same channel as the search
    command.
    """
    bot.send(jarvis.tools.showmore(tr.group(2), tr.sender))


@sopel.module.commands('lastcreated', 'lc')
def lastcreated(bot, tr):
    """Display recently created pages."""
    pages = list(bot._wiki.list_pages(
        order='created_at desc', limit=3, body='rating'))
    bot.send(' || '.join(map(page_summary, pages)))


@sopel.module.commands('errors')
def errors(bot, tr):
    """Display pages with errors."""
    msg = ''
    no_tags = [p.title for p in bot.memory['pages'] if not p.tags]
    no_tags = ['\x02{}\x02'.format(t) for t in no_tags]
    if no_tags:
        msg += 'Pages with no tags: {}. '.format(', '.join(no_tags))
    no_title = [
        p.title for p in bot.memory['pages']
        if re.search(r'/scp-[0-9]+$', p.url) and
        p._raw_title == p.title]
    no_title = ['\x02{}\x02'.format(t) for t in no_title]
    if no_title:
        msg += 'Pages without titles: {}.'.format(', '.join(no_title))
    if msg:
        bot.send(msg)
    else:
        bot.send('No Errors.')


@sopel.module.interval(3600)
def refresh_page_cache(bot):
    bot.memory['pages'] = jarvis.ext.PageView(
        bot._wiki.list_pages(
            body='title created_by created_at rating tags',
            category='*'))

###############################################################################


def page_summary(page):
    msg = '\x02{}\x02 (written by {}; rating: {:+d}) - {}'
    return msg.format(
        page.title, page.author, page.rating,
        page.url.replace('scp-wiki.wikidot.com', 'www.scp-wiki.net'))


def show_search_results(bot, tr, pages):
    if not pages:
        msg = jarvis.lexicon.page_not_found()
    elif len(pages) == 1:
        msg = page_summary(pages[0])
    else:
        pages = [p.title for p in pages]
        head, tail = pages[:3], pages[3:]
        msg = ' || '.join(map('\x02{}\x02'.format, head))
        if tail:
            msg += ' and \x02{}\x02 more.'.format(len(tail))
    bot.send(msg)
