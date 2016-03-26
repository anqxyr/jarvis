#!/usr/bin/env python3

###############################################################################
# Module Imports
###############################################################################

import arrow
import collections
import pyscp
import re
import sopel
import time
import random

###############################################################################

BANUPDATE = [
    'Banlist updated, boss.']
UPDATEFAILED = [
    "I tried, but it doesn't look like it's working."]
OPALERTNICK = [
    'The user was kicked out and told wash their mouth with soap.',
    "This guy is just untasteful, and I don't want their ilk here.",
    'Was this a troll? It was probably a troll.']
OPALERTBAN = [
    '{} (better known as {}) was exiled from this fine and pure kingdom.',
    ('{} was kicked and banned because they look like {} and their face '
        'is ugly and they smell :| .'),
    "Another old troll - {} (they're actually {})",
    'This guys is banned - {} (aka {})']

###############################################################################

Ban = collections.namedtuple('Ban', 'names hosts status reason thread')

###############################################################################


def setup(bot):
    bot._bans = get_ban_list()


###############################################################################

@sopel.module.commands('updatebans')
def update_bans(bot, trigger):
    try:
        bot._bans = get_ban_list()
        bot.say(random.choice(BANUPDATE))
    except:
        bot.say(random.choice(UPDATEFAILED))


@sopel.module.event('JOIN')
@sopel.module.rule('.*')
def join_event(bot, trigger):
    bad_words = [
        'bitch', 'fuck', 'asshole', 'penis', 'vagina', 'nigger', 'retard',
        'faggot', 'chink', 'shit', 'hitler', 'douche']
    for word in bad_words:
        if word in trigger.nick.lower():
            ban_user(bot, trigger)
    for ban in bot._bans:
        if trigger.nick.lower() in ban.names:
            ban_user(bot, trigger, ban)
        if trigger.host in ban.hosts:
            ban_user(bot, trigger, ban)


###############################################################################


def ban_user(bot, trigger, ban=None):
    channel = trigger.sender
    if channel == '#site17':
        return
    nick = trigger.nick
    if nick == bot.config.core.nick:
        return
    hostmask = trigger.hostmask
    if not ban:
        msg = (
            'Your username is inappropriate. Please use '
            '"/nick newnick" to change it. You may rejoin with a '
            'different username in 10 seconds.')
        bot.write(['MODE', channel, '+b', hostmask])
        bot.write(['MODE', channel, '+b', nick])
        bot.write(['KICK', channel, nick], msg)
        time.sleep(10)
        bot.write(['MODE', channel, '-b', hostmask])
        time.sleep(890)
        bot.write(['MODE', channel, '-b', nick])
        bot.say('OP Alert: ' + random.choice(OPALERTNICK))
    else:
        msg = (
            "Your nick/ip was found in the bot's banlist. "
            "Reason for ban: {}. If you wish to appeal please join #site17.")
        msg = msg.format(ban.reason)
        bot.write(['MODE', channel, '+b', hostmask])
        bot.write(['KICK', channel, nick], msg)
        time.sleep(900)
        bot.write(['MODE', channel, '-b', hostmask])
        bot.say('OP Alert: ' +
                random.choice(OPALERTBAN).format(nick, ban.names[0]))


def get_ban_list():
    wiki = pyscp.wikidot.Wiki('05command')
    soup = wiki('alexandra-s-ban-page')._soup
    rows = soup('tr')[1:]
    return [b for b in map(parse_ban, rows) if b]


def parse_ban(row):
    names, hosts, status, reason, thread = [i.text for i in row('td')]
    names = [i for i in names.strip().lower().split() if 'generic' not in i]
    if re.match('[0-9]+/[0-9]+/[0-9]+', status):
        status = arrow.get(status, 'M/D/YYYY')
        if status < arrow.now():
            return
    elif re.match('[0-9]+-[0-9]+-[0-9]+', status):
        status = arrow.get(status, 'YYYY-MM-DD')
        if status < arrow.now():
            return
    return Ban(names, hosts.strip().split(), status, reason, thread)
