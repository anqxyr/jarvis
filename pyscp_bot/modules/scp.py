#!/usr/bin/env python3
"""All bot actions related to the scp-wiki."""


###############################################################################
# Module Imports
###############################################################################

import pyscp
import re
import sopel
import pyscp_bot.jarvis as vocab

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
def author(bot, trigger):
    """
    Output basic information about the author.

    Only pages tagged with any of {'scp', 'tale', 'goi-format'} are counted.
    Ratings are calculated as displayed on the page, and may include votes
    from deleted accounts.

    Calling the command without arguments will use the username
    of the caller as the name of the author.
    """
    partname = trigger.group(2)
    if not partname:
        partname = trigger.nick
    authors = list({
        p.author for p in bot.memory['pages']
        if p.author and partname.lower() in p.author.lower()})
    if not authors:
        bot.say(vocab.author_not_found(trigger.nick))
        return
    if len(authors) > 1:
        authors = authors[:min(5, len(authors))]
        bot.say('{}: did you mean {} or {}?'.format(
            trigger.nick.lstrip('~'),
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
    bot.say(msg)


@sopel.module.rule(r'(?i)^(scp-[^ ]+)$')
@sopel.module.rule(r'(?i).*!(scp-[^ ]+)')
def scp_lookup(bot, trigger):
    """Display page summary for the matching scp article."""
    name = trigger.group(1).lower()
    pages = [p for p in bot.memory['pages'] if p._body.name == name]
    show_search_results(bot, trigger, pages)


@sopel.module.rule(r'(?i).*(http://www\.scp-wiki\.net/[^ ]+)')
def url_lookup(bot, trigger):
    """Display page summary for the matching wiki page."""
    url = trigger.group(1)
    if '/forum/' in url:
        return
    name = url.split('/')[-1]
    show_search_results(
        bot, trigger, [p for p in bot.memory['pages'] if p._body.name == name])


@sopel.module.commands('unused')
def unused(bot, trigger):
    """Link to the first empty scp slot."""
    skips = ['scp-{:03}'.format(i) for i in range(2, 3000)]
    names = {p._body.name for p in bot.memory['pages']}
    unused = next(i for i in skips if i not in names)
    bot.say('{}: http://www.scp-wiki.net/{}'.format(trigger.nick, unused))


@sopel.module.commands('user')
def user(bot, trigger):
    """Link to the user's profile page."""
    name = trigger.group(2).lower().replace(' ', '-')
    bot.say(
        '{}: http://www.wikidot.com/user:info/{}'.format(trigger.nick, name))


@sopel.module.commands('search', 's')
def search(bot, trigger):
    """
    Search for a wiki page.

    Attempts to match the search terms to one or more of the existing wiki
    pages. Search by the series titles of SCP articles is supported. When
    searching for multiple words, the order of the search terms is unimportant.

    Also searches among hubs, guides, and system pages.

    When multiple results are found, the extended information about each result
    can be accessed via the !showmore command.
    """
    words = trigger.group(2).lower().split()
    pages = [
        p for p in bot.memory['pages']
        if all(w in p.title.lower() for w in words)]
    bot.memory['search'][trigger.sender] = pages
    show_search_results(bot, trigger, pages)


@sopel.module.commands('tale')
def tale(bot, trigger):
    """
    Search for a tale.

    Identical to the !search command, but returns only tales.

    When multiple results are found, the extended information about each result
    can be accessed via the !showmore command.
    """
    partname = trigger.group(2).lower()
    pages = [
        p for p in bot.memory['pages'] if partname in p.title.lower() and
        'tale' in p.tags]
    bot.memory['search'][trigger.sender] = pages
    show_search_results(bot, trigger, pages)


@sopel.module.commands('tags')
def tags(bot, trigger):
    """
    Find pages by tag.

    Returns all pages that have **all** of the specified tags.

    When multiple results are found, the extended information about each result
    can be accessed via the !showmore command.
    """
    tags = set(trigger.group(2).lower().split())
    pages = [p for p in bot.memory['pages'] if p.tags.issuperset(tags)]
    bot.memory['search'][trigger.sender] = pages
    show_search_results(bot, trigger, pages)


@sopel.module.commands('showmore', 'sm')
def showmore(bot, trigger):
    """
    Access additional results.

    Must be used after a !search, !tale, or !tags command. Displays sumary of
    the specified result. Must be issued in the same channel as the search
    command.
    """
    if not trigger.group(2):
        index = 0
    else:
        index = int(trigger.group(2)) - 1

    if index >= len(bot.memory['search'][trigger.sender]):
        bot.say(vocab.out_of_range(trigger.nick))
    else:
        bot.say(page_summary(bot.memory['search'][trigger.sender][index]))


@sopel.module.commands('lastcreated', 'lc')
def lastcreated(bot, trigger):
    """Display recently created pages."""
    pages = list(bot._wiki.list_pages(
        order='created_at desc', limit=3, body='rating'))
    bot.say(' || '.join(map(page_summary, pages)))


@sopel.module.commands('errors')
def errors(bot, trigger):
    """Display pages with errors."""
    msg = ''
    no_tags = [p.title for p in bot.memory['pages'] if not p.tags]
    no_tags = ['\x02{}\x02'.format(t) for t in no_tags]
    if no_tags:
        msg += 'Pages with no tags: {}. '.format(', '.join(no_tags))
    no_title = [
        p.title for p in bot.memory['pages']
        if re.search(r'scp-[0-9]+$', p.url) and
        p._raw_title == p.title]
    no_title = ['\x02{}\x02'.format(t) for t in no_title]
    if no_title:
        msg += 'Pages without titles: {}.'.format(', '.join(no_title))
    if msg:
        bot.say('{}: {}'.format(trigger.nick, msg))
    else:
        bot.say('{}: no errors.'.format(trigger.nick))


@sopel.module.interval(3600)
def refresh_page_cache(bot):
    pages = bot._wiki.list_pages(
        body='title created_by rating tags',
        limit=10,
        order='created_at desc')
    bot.memory['pages'] = list(pages)

###############################################################################


def page_summary(page):
    msg = '\x02{}\x02 (written by {}; rating: {:+d}) - {}'
    return msg.format(
        page.title, page.author, page.rating,
        page.url.replace('scp-wiki.wikidot.com', 'www.scp-wiki.net'))


def show_search_results(bot, trigger, pages):
    if not pages:
        msg = vocab.page_not_found(trigger.nick)
    elif len(pages) == 1:
        msg = page_summary(pages[0])
    elif len(pages) <= 3:
        msg = vocab.few_pages_found(trigger.nick, pages)
    else:
        msg = vocab.many_pages_found(trigger.nick, pages)
    bot.say(msg)
