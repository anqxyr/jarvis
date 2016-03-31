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
import pyscp_bot.jarvis as vocab

###############################################################################

Ban = collections.namedtuple('Ban', 'names hosts status reason thread')


def setup(bot):
    bot.memory['bans'] = get_ban_list()

###############################################################################


@sopel.module.commands('updatebans')
def update_bans(bot, trigger):
    if trigger.sender != '#site67':
        return
    try:
        bot.memory['bans'] = get_ban_list()
        bot.say(vocab.banlist_updated(trigger.nick))
    except:
        bot.say(vocab.banlist_update_failed(trigger.nick))


@sopel.module.event('JOIN')
@sopel.module.rule('.*')
def join_event(bot, trigger):
    bad_words = [
        'bitch', 'fuck', 'asshole', 'penis', 'vagina', 'nigger', 'retard',
        'faggot', 'chink', 'shit', 'hitler', 'douche']
    for word in bad_words:
        if word in trigger.nick.lower():
            ban_user(bot, trigger)
    for ban in bot.memory['bans']:
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
        bot.say('OP Alert: ' + vocab.profane_username(nick))
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
        bot.say('OP Alert: ' + vocab.user_in_banlist(nick, ban.names[0]))
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
