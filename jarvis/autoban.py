#!/usr/bin/env python3

###############################################################################
# Module Imports
###############################################################################

import arrow
import collections
import pyscp
import time

from . import core, lexicon

###############################################################################

Ban = collections.namedtuple('Ban', 'names hosts status reason thread')


def get_ban_list():
    wiki = pyscp.wikidot.Wiki('05command')
    soup = wiki('alexandra-s-ban-page')._soup
    rows = soup('tr')[1:]
    return [b for b in map(parse_ban, rows) if b]


def parse_ban(row):
    names, hosts, status, reason, thread = [i.text for i in row('td')]
    names = [i for i in names.strip().lower().split() if 'generic' not in i]
    try:
        if arrow.get(status, ['M/D/YYYY', 'YYYY-MM-DD']) < arrow.now():
            return
    except arrow.parser.ParserError:
        pass
    return Ban(names, hosts.strip().split(), status, reason, thread)


BANS = get_ban_list()

###############################################################################


@core.command
def update_bans(inp):
    global BANS
    if inp.channel != core.config['irc']['sssc']:
        return
    try:
        BANS = get_ban_list()
        return lexicon.bans.updated
    except:
        return lexicon.bans.failed


def offensive_username(name, host, kick, ban, send):
    banned_words = [
        'bitch', 'fuck', 'asshole', 'penis', 'vagina', 'nigger', 'retard',
        'faggot', 'chink', 'shit', 'hitler', 'douche']
    if any(word in name.lower() for word in banned_words):
        kick(lexicon.bans.kick.profanity)
        ban(host, True)
        ban(name, True)
        send(lexicon.bans.profanity.format(user=name))
        time.sleep(10)
        ban(host, False)
        time.sleep(890)
        ban(name, False)
        return True


def ban_evasion(name, host, kick, ban, send):
    for b in BANS:
        if name.lower() in b.names or host in b.hosts:
            kick(lexicon.bans.kick.evasion.format(b.reason))
            ban(host, True)
            send(lexicon.bans.evasion.format(user=name, name=b.names[0]))
            time.sleep(900)
            ban(host, False)
            return True
