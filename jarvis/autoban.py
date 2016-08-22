#!/usr/bin/env python3

###############################################################################
# Module Imports
###############################################################################

import arrow
import collections
import pyscp
import threading
import fnmatch

from . import core, lex

###############################################################################

PROFANITY = [
    'bitch', 'fuck', 'asshole', 'penis', 'vagina', 'nigger', 'retard',
    'faggot', 'chink', 'shit', 'hitler', 'douche', 'bantest']

###############################################################################
# Helper Functions
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
    return Ban(names, hosts.strip().split(), status, reason, thread)


BANS = get_ban_list()


def kick_user(inp, name, message):
    message = message.compose(inp)
    inp.raw(['KICK', inp.channel, name], message)


def ban_user(inp, target, length):
    inp.raw(['MODE', inp.channel, '+b', target])
    t = threading.Timer(
        length,
        lambda: inp.raw(['MODE', inp.channel, '-b', target]))
    t.start()

###############################################################################
# Commands
###############################################################################


@core.require(channel=core.config.irc.sssc)
@core.command
def updatebans(inp):
    global BANS
    try:
        BANS = get_ban_list()
        return lex.updatebans.updated
    except:
        return lex.updatebans.failed


def autoban(inp, name, host):
    if not core.config.debug and inp.channel != '#site19':
        return
    if any(word in name.lower() for word in PROFANITY):
        kick_user(inp, name, lex.autoban.kick.name)
        ban_user(inp, host, 10)
        ban_user(inp, name, 900)
        return lex.autoban.name(user=name)
    # find if the user is in the banlist
    bans = [b for b in BANS if name.lower() in b.names or
            any(fnmatch.fnmatch(host, pat) for pat in b.hosts)]
    for ban in bans:
        try:
            # check if the ban has expired
            if arrow.get(ban.status, ['M/D/YYYY', 'YYYY-MM-DD']) < arrow.now():
                continue
        except arrow.parser.ParserError:
            # if we can't parse the time, it's perma
            pass
        kick_user(inp, name, lex.autoban.kick.banlist(reason=ban.reason))
        ban_user(inp, host, 900)
        return lex.autoban.banlist(user=name, truename=ban.names[0])
