#!/usr/bin/env python3
"""All bot actions related to the scp-wiki."""


###############################################################################
# Module Imports
###############################################################################

import pyscp
import sopel
import pyscp_bot.jarvis as vocab

###############################################################################


def setup(bot):
    #pyscp.utils.default_logging(True)
    bot._wiki = pyscp.wikidot.Wiki('scp-wiki')
    bot._wiki.auth('pyscp_bot', bot.config.scp.wikipass)
    refresh_page_cache(bot)
    bot.memory['search'] = []


class SCPSection(sopel.config.types.StaticSection):

    wikipass = sopel.config.types.BaseValidated('wikipass')


def configure(config):
    config.define_section('scp')

###############################################################################


@sopel.module.commands('au', 'author')
def author(bot, trigger):
    """Display basic author statistics."""
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
        bot.say('{}: did you mean {} or {}?'.format(
            trigger.nick.lstrip('~'),
            ', '.join(authors[:-1]),
            authors[-1]))
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


@sopel.module.rule(r'(?i)^(scp-[0-9]+)$')
@sopel.module.rule(r'(?i).*!(scp-[0-9]+)')
def skip(bot, trigger):
    """Display SCP article details."""
    name = trigger.group(1).lower()
    page_matches = [p for p in bot.memory['pages'] if p._body.name == name]
    if not page_matches:
        bot.say(vocab.page_not_found(trigger.nick))
    else:
        bot.say(page_details(page_matches[0]))


@sopel.module.commands('search', 'sea', 's')
def search(bot, trigger):
    partname = trigger.group(2).lower()
    pages = [p for p in bot.memory['pages'] if partname in p.title.lower()]
    display_pages(bot, trigger, pages)


@sopel.module.commands('tags', 'tag')
def tags(bot, trigger):
    tags = set(trigger.group(2).lower().split())
    pages = [p for p in bot.memory['pages'] if p.tags.issuperset(tags)]
    display_pages(bot, trigger, pages)


@sopel.module.commands('showmore', 'sm')
def showmore(bot, trigger):
    index = int(trigger.group(2)) - 1
    if index >= len(bot._found):
        bot.say(vocab.out_of_range(trigger.nick))
    bot.say(page_details(bot.memory['search'][index]))


@sopel.module.commands('lastcreated', 'lc')
def lastcreated(bot, trigger):
    """Display recently created pages."""
    pages = list(bot._wiki.list_pages(
        order='created_at desc', limit=3, body='rating'))
    bot.say(' || '.join([page_details(p) for p in pages]))


@sopel.module.interval(3600)
def refresh_page_cache(bot):
    bot.memory['pages'] = list(
        bot._wiki.list_pages(body='title created_by rating tags', limit=10))

###############################################################################


def page_details(page):
    msg = '{} (written by {}; rating: {:+d}) - {}'
    return msg.format(
        page.title, page.author, page.rating,
        page.url.replace('scp-wiki.wikidot.com', 'scp-wiki.net'))


def display_pages(bot, trigger, pages):
    if not pages:
        bot.say(vocab.page_not_found(trigger.nick))
        return
    if len(pages) == 1:
        bot.say(page_details(pages[0]))
        return
    msg = ' || '.join([p.title for p in pages][:3])
    if len(pages) > 3:
        msg += ' plus {} more.'.format(len(pages) - 3)
    bot.memory['search'] = pages
    bot.say(msg)
