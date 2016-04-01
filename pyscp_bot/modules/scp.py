#!/usr/bin/env python3
"""All bot actions related to the scp-wiki."""


###############################################################################
# Module Imports
###############################################################################

import pyscp
import re
import sopel
import pyscp_bot.jarvis as lexicon

###############################################################################


def setup(bot):
    #pyscp.utils.default_logging(True)
    bot._wiki = pyscp.wikidot.Wiki('scp-wiki')
    bot._wiki.auth('pyscp_bot', bot.config.scp.wikipass)
    refresh_page_cache(bot)
    bot.memory['search'] = {}


def configure(config):
    config.define_section('scp')

###############################################################################


@sopel.module.commands('author')
def author(bot, tr):
    """
    Output basic information about the author.

    Only pages tagged with any of {'scp', 'tale', 'goi-format'} are counted.
    Ratings are calculated as displayed on the page, and may include votes
    from deleted accounts.

    Calling the command without arguments will use the username
    of the caller as the name of the author.
    """
    partname = tr.group(2)
    if not partname:
        partname = tr.nick
    authors = list({
        p.author for p in bot.memory['pages']
        if p.author and partname.lower() in p.author.lower()})
    if not authors:
        bot.send(lexicon.author_not_found())
        return
    if len(authors) > 1:
        authors = authors[:min(5, len(authors))]
        bot.send('Did you mean {} or {}?'.format(
            ', '.join(authors[:-1]),
            authors[-1]))
        return
    author = authors[0]
    pages = [
        p for p in bot.memory['pages']
        if p.author == author and '_sys' not in p.tags]
    skips = {p for p in pages if 'scp' in p.tags}
    tales = {p for p in pages if 'tale' in p.tags}
    goifs = {p for p in pages if 'goi-format' in p.tags}
    pages = (skips | tales | goifs)
    rating = sum(p.rating for p in pages)
    msg = (
        '{} has written {} SCPs, {} tales, and {} GOI-format pages. '
        'They have {} net upvotes with an average of {}.'
    ).format(
        author, len(skips), len(tales), len(goifs),
        rating, rating // len(pages))
    bot.send(msg)


@sopel.module.rule(r'(?i)^(scp-[^ ]+)$')
@sopel.module.rule(r'(?i).*!(scp-[^ ]+)')
def scp_lookup(bot, tr):
    """Display page summary for the matching scp article."""
    name = tr.group(1).lower()
    pages = [p for p in bot.memory['pages'] if p._body.name == name]
    if not pages:
        bot.send(lexicon.page_not_found())
    else:
        bot.send(page_summary(pages[0]))


@sopel.module.rule(r'(?i).*(http://www\.scp-wiki\.net/[^ ]+)')
def url_lookup(bot, tr):
    """Display page summary for the matching wiki page."""
    url = tr.group(1)
    if '/forum/' in url:
        return
    name = url.split('/')[-1]
    pages = [p for p in bot.memory['pages'] if p._body.name == name]
    if not pages:
        bot.send(lexicon.page_not_found())
    else:
        bot.send(page_summary(pages[0]))


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
    words = tr.group(2).lower().split()
    pages = [
        p for p in bot.memory['pages']
        if all(w in p.title.lower() for w in words)]
    bot.memory['search'][tr.sender] = pages
    show_search_results(bot, tr, pages)


@sopel.module.commands('tale')
def tale(bot, tr):
    """
    Search for a tale.

    Identical to the !search command, but returns only tales.

    When multiple results are found, the extended information about each result
    can be accessed via the !showmore command.
    """
    partname = tr.group(2).lower()
    pages = [
        p for p in bot.memory['pages'] if partname in p.title.lower() and
        'tale' in p.tags]
    bot.memory['search'][tr.sender] = pages
    show_search_results(bot, tr, pages)


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
    if not tr.group(2):
        index = 0
    else:
        index = int(tr.group(2)) - 1

    if index >= len(bot.memory['search'][tr.sender]):
        bot.send(lexicon.out_of_range())
    else:
        bot.send(page_summary(bot.memory['search'][tr.sender][index]))


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
    pages = bot._wiki.list_pages(
        body='title created_by rating tags',
        #limit=10,
        order='created_at desc')
    bot.memory['pages'] = list(pages)

###############################################################################


def page_summary(page):
    msg = '\x02{}\x02 (written by {}; rating: {:+d}) - {}'
    return msg.format(
        page.title, page.author, page.rating,
        page.url.replace('scp-wiki.wikidot.com', 'www.scp-wiki.net'))


def show_search_results(bot, tr, pages):
    if not pages:
        msg = lexicon.page_not_found()
    elif len(pages) == 1:
        msg = page_summary(pages[0])
    else:
        pages = [p.title for p in pages]
        head, tail = pages[:3], pages[3:]
        msg = ' || '.join(map('\x02{}\x02'.format, head))
        if tail:
            msg += ' and \x02{}\x02 more.'.format(len(tail))
    bot.send(msg)
