#!/usr/bin/env python3
"""All bot actions related to the scp-wiki."""


###############################################################################
# Module Imports
###############################################################################

import jarvis
import sopel

###############################################################################
# Search And Lookup Commands
###############################################################################


@sopel.module.commands('author')
def find_author(bot, tr):
    name = tr.group(2) if tr.group(2) else tr.nick
    bot.send(jarvis.scp.find_author(name, tr.sender))


@sopel.module.commands('search', 's')
def find_page_by_title(bot, tr):
    bot.send(jarvis.scp.find_page_by_title(tr.group(2), tr.sender))


@sopel.module.rule(r'(?i)^(scp-[\d]+(?:-[\w]+)?)$')
@sopel.module.rule(r'(?i).*!(scp-[\d]+(?:-[\w]+)?)')
def scp_lookup(bot, tr):
    url = 'http://www.scp-wiki.net/' + tr.group(1)
    bot.send(jarvis.scp.find_page_by_url(url))


@sopel.module.commands('tale')
def find_tale_by_title(bot, tr):
    bot.send(jarvis.scp.find_tale_by_title(tr.group(2), tr.sender))


@sopel.module.commands('tags')
def find_page_by_tags(bot, tr):
    bot.send(jarvis.scp.find_page_by_tags(tr.group(2), tr.sender))


@sopel.module.commands('showmore', 'sm')
def showmore(bot, tr):
    bot.send(jarvis.tools.recall(tr.group(2), tr.sender))


@sopel.module.rule(r'(?i).*(http://www\.scp-wiki\.net/[^ ]+)')
def find_page_by_url(bot, tr):
    bot.send(jarvis.scp.find_page_by_url(tr.group(1)))


@sopel.module.commands('lastcreated', 'lc')
def get_last_created(bot, tr):
    for line in jarvis.scp.get_last_created(tr.sender):
        bot.send(line, force=True)

###############################################################################
# Extended Stats
###############################################################################


@sopel.module.commands('ad')
def authordetails(bot, tr):
    name = tr.group(2) if tr.group(2) else tr.nick
    bot.send(jarvis.scp.update_author_details(name, tr.sender))


###############################################################################
# Misc Tools
###############################################################################


@sopel.module.commands('unused')
def unused(bot, tr):
    """Link to the first empty scp slot."""
    skips = ['scp-{:03}'.format(i) for i in range(2, 3000)]
    names = {p._body.fullname for p in bot.memory['pages']}
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
    bot.send(jarvis.scp.get_error_report())


@sopel.module.commands('random')
def get_random_page(bot, tr):
    bot.send(jarvis.scp.get_random_page(tr.group(2)))


@sopel.module.interval(3600)
def refresh_page_cache(bot):
    jarvis.core.refresh()


###############################################################################
