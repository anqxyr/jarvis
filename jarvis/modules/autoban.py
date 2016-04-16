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

import jarvis

###############################################################################

Ban = collections.namedtuple('Ban', 'names hosts status reason thread')


def setup(bot):
    bot.memory['bans'] = get_ban_list()

###############################################################################


@sopel.module.commands('updatebans')
def update_bans(bot, tr):
    if tr.sender != '#site67':
        return
    try:
        bot.memory['bans'] = get_ban_list()
        bot.send(jarvis.lexicon.bans.updated)
    except:
        bot.send(jarvis.lexicon.bans.failed


@sopel.module.event('JOIN')
@sopel.module.rule('.*')
def join_event(bot, tr):
    bad_words = [
        'bitch', 'fuck', 'asshole', 'penis', 'vagina', 'nigger', 'retard',
        'faggot', 'chink', 'shit', 'hitler', 'douche']
    for word in bad_words:
        if word in tr.nick.lower():
            ban_user(bot, tr)
    for ban in bot.memory['bans']:
        if tr.nick.lower() in ban.names:
            ban_user(bot, tr, ban)
        if tr.host in ban.hosts:
            ban_user(bot, tr, ban)

###############################################################################


def ban_user(bot, tr, ban=None):
    channel = tr.sender
    if channel == '#site17':
        return
    nick = tr.nick
    if nick == bot.config.core.nick:
        return
    hostmask = tr.hostmask
    if not ban:
        msg = (
            'Your username is inappropriate. Please use '
            '"/nick newnick" to change it. You may rejoin with a '
            'different username in 10 seconds.')
        bot.write(['MODE', channel, '+b', hostmask])
        bot.write(['MODE', channel, '+b', nick])
        bot.write(['KICK', channel, nick], msg)
        bot.send(
            'OP Alert: ' + jarvis.lexicon.bans.profanity.format(user=nick))
        time.sleep(10)
        bot.write(['MODE', channel, '-b', hostmask])
        time.sleep(890)
        bot.write(['MODE', channel, '-b', nick])
    else:
        msg = (
            "Your nick/ip was found in the bot's banlist. "
            "Reason for ban: {}. If you wish to appeal please join #site17.")
        msg = msg.format(ban.reason)
        bot.write(['MODE', channel, '+b', hostmask])
        bot.write(['KICK', channel, nick], msg)
        bot.send('OP Alert: ' + jarvis.lexicon.bans.evasion.format(
            user=nick, name=ban.names[0]))
        time.sleep(900)
        bot.write(['MODE', channel, '-b', hostmask])


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
