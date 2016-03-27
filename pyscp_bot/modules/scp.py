#!/usr/bin/env python3
"""All bot actions related to the scp-wiki."""


###############################################################################
# Module Imports
###############################################################################

import pyscp
import sopel
import random

###############################################################################

NOAUTHOR = [
    'Your author is in another castle.',
    'There is nobody here by that name. Now go away.',
    "I'm sorry Dave, I'm afraid I can't do that.",
    "That person has been retconned from existence. Try again later.",
    'No dice.',
    'Author Not Found.',
    'Could not find a matching author.',
    'Author does not exist.']

NOPAGE = [
    "I couldn't find anything like that. Sorry.",
    'Page Not Found.'
    "The future author of that page haven't wrote it yet. Try later.",
    "You're better off reading something else.",
    "Yesterday, in wiki cache, I saw a page that wasn't there. "
    "It didn't rhyme again today.",
    "Your search query does not match any existing pages.",
    'No such luck.',
    'Maybe another time.']

OUTOFRANGE = [
    "That's a big number you have there. I don't even have that many results."]

###############################################################################


def setup(bot):
    #pyscp.utils.default_logging(True)
    bot._wiki = pyscp.wikidot.Wiki('scp-wiki')
    bot._wiki.auth('pyscp_bot', bot.config.scp.wikipass)
    refresh_page_cache(bot)
    bot._found = []


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
        p.author for p in bot._pages
        if p.author and partname.lower() in p.author.lower()})
    if not authors:
        _say(bot, trigger, NOAUTHOR)
        return
    if len(authors) > 1:
        bot.say('{}: did you mean {} or {}?'.format(
            trigger.nick.lstrip('~'),
            ', '.join(authors[:-1]),
            authors[-1]))
    author = authors[0]
    pages = [
        p for p in bot._pages if p.author == author if '_sys' not in p.tags]
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
    page_matches = [p for p in bot._pages if p._body.name == name]
    if not page_matches:
        _say(bot, trigger, NOPAGE)
    else:
        bot.say(_page_info(page_matches[0]))


@sopel.module.commands('s', 'sea', 'search')
def search(bot, trigger):
    partname = trigger.group(2).lower()
    pages = [p for p in bot._pages if partname in p.title.lower()]
    _display_pages(bot, trigger, pages)


@sopel.module.commands('tag', 'tags')
def tags(bot, trigger):
    tags = set(trigger.group(2).lower().split())
    pages = [p for p in bot._pages if p.tags.issuperset(tags)]
    _display_pages(bot, trigger, pages)


@sopel.module.commands('sm', 'showmore')
def showmore(bot, trigger):
    index = int(trigger.group(2)) - 1
    if index >= len(bot._found):
        _say(bot, trigger, OUTOFRANGE)
    bot.say(_page_info(bot._found[index]))


@sopel.module.commands('lc', 'lastcreated')
def lastcreated(bot, trigger):
    """Display recently created pages."""
    pages = list(bot._wiki.list_pages(
        order='created_at desc', limit=3, body='rating'))
    bot.say(' || '.join([_page_info(p) for p in pages]))


@sopel.module.interval(3600)
def refresh_page_cache(bot):
    bot._pages = list(
        bot._wiki.list_pages(body='title created_by rating tags'))

###############################################################################


def _page_info(page):
    msg = '{} (written by {}; rating: {:+d}) - {}'
    return msg.format(
        page.title, page.author, page.rating,
        page.url.replace('scp-wiki.wikidot.com', 'scp-wiki.net'))


def _display_pages(bot, trigger, pages):
    if not pages:
        _say(bot, trigger, NOPAGE)
        return
    if len(pages) == 1:
        bot.say(_page_info(pages[0]))
        return
    msg = ' || '.join([p.title for p in pages][:3])
    if len(pages) > 3:
        msg += ' plus {} more.'.format(len(pages) - 3)
    bot._found = pages
    bot.say(msg)


def _say(bot, trigger, messages):
    bot.say('{}: {}'.format(trigger.nick.lstrip('~'), random.choice(messages)))
