#!/usr/bin/env python3
"""All bot actions related to the scp-wiki."""


###############################################################################
# Module Imports
###############################################################################

import pyscp
import sopel
import difflib
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
    bot._pages = list(bot._wiki.list_pages(
        body='title created_by rating tags'))
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
        partname = trigger.user
    authors = {p.author for p in bot._pages if p.author}
    candidates = difflib.get_close_matches(partname, authors)
    if not candidates:
        _say(bot, trigger, NOAUTHOR)
        return
    author = candidates[0]
    pages = [
        p for p in bot._pages if p.author == author and
        ('scp' in p.tags or 'tale' in p.tags)]
    msg = (
        '{} has written {} SCPs, {} tales, and {} GOI-format pages. '
        'They have {} net upvotes with an average of {}.')
    msg = msg.format(
        author,
        len([p for p in pages if 'scp' in p.tags]),
        len([p for p in pages if 'tale' in p.tags]),
        len([p for p in pages if 'goi-format' in p.tags]),
        sum([p.rating for p in pages]),
        sum([p.rating for p in pages]) // len(pages))
    bot.say(msg)


@sopel.module.rule('^(scp-[0-9]+)$')
@sopel.module.rule('.*!(scp-[0-9]+)')
def skip(bot, trigger):
    """Display SCP article details."""
    name = trigger.group(1)
    page_matches = [p for p in bot._pages if p._body.name == name]
    if not page_matches:
        _say(bot, trigger, NOPAGE)
    else:
        bot.say(_page_info(page_matches[0]))


@sopel.module.commands('s', 'sea', 'search')
def search(bot, trigger):
    partname = trigger.group(2)
    titles = [p.title for p in bot._pages]
    candidates = difflib.get_close_matches(partname, titles, 10, 0.2)
    if not candidates:
        _say(bot, trigger, NOPAGE)
        return
    elif len(candidates) == 1:
        bot.say(_page_info(
            next(p for p in bot._pages if p.title == candidates[0])))
        return
    elif len(candidates) <= 3:
        msg = '; '.join(candidates)
    else:
        msg = '{} plus {} more.'.format(
            '; '.join(candidates[:3]), len(candidates) - 3)
    bot._found = candidates
    bot.say(msg)


@sopel.module.commands('sm', 'showmore')
def showmore(bot, trigger):
    index = int(trigger.group(2)) - 1
    if index >= len(bot._found):
        _say(bot, trigger, OUTOFRANGE)
    bot.say(_page_info(
        next(p for p in bot._pages if p.title == bot._found[index])))


@sopel.module.commands('lc', 'lastcreated')
def lastcreated(bot, trigger):
    """Display recently created pages."""
    pages = bot._wiki.list_pages(
        order='created_at desc', limit=3, body='rating')
    for p in pages:
        bot.say(_page_info(p))


@sopel.module.interval(3600)
def refresh_page_cache(bot):
    bot._pages = list(
        bot._wiki.list_pages(body='title created_by rating tags'))

###############################################################################


def _page_info(page):
    msg = '{} (written by {}; rating: {:+d}) - {}'
    return msg.format(page.title, page.author, page.rating, page.url)


def _say(bot, trigger, messages):
    bot.say('{}: {}'.format(trigger.user.lstrip('~'), random.choice(messages)))
