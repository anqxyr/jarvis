#!/usr/bin/env python3
"""Misc. bot commands."""

###############################################################################
# Module Imports
###############################################################################

import arrow
import random
import re
import tweepy

from . import core, parser, lex, __version__

###############################################################################

BOOTTIME = arrow.now()

###############################################################################
# Internal Tools
###############################################################################

MEMORY = {}


def save_results(inp, items, func=None):
    MEMORY[inp.channel] = items, func


@core.command
@core.alias('sm')
@parser.showmore
def showmore(inp, *, index):
    if index is None:
        index = 1
    if index <= 0:
        return lex.input.bad_index
    if inp.channel not in MEMORY:
        return lex.not_found.generic
    items, func = MEMORY[inp.channel]
    if index > len(items):
        return lex.input.bad_index
    return func(items[index - 1]) if func else items[index - 1]


def choose_input(options):
    options = list(map('\x02{}\x02'.format, options))
    if len(options) <= 5:
        head, tail = options[:-1], options[-1]
        msg = lex.input.options
    else:
        head, tail = options[:5], len(options[5:])
        msg = lex.input.cropped_options
    return msg(head=', '.join(head), tail=tail)


###############################################################################
# Tools for users
###############################################################################


@core.command
@core.alias('jarvis')
@core.alias('changelog')
def version(inp):
    uptime = (arrow.now() - BOOTTIME)
    m, s = divmod(uptime.seconds, 60)
    h, m = divmod(m, 60)
    return lex.version(
        version=__version__, days=uptime.days, hours=h, minutes=m)


@core.require(channel=core.config.irc.sssc)
@core.command
def rejoin(inp):
    channel = inp.text if inp.text.startswith('#') else '#' + inp.text
    inp.raw(['JOIN', channel])
    return lex.rejoin(channel=channel)


@core.command
@core.alias('ch')
def choose(inp):
    """Return one random comma-separated option."""
    if not inp.text:
        return lex.input.missing
    options = [i.strip() for i in inp.text.split(',') if i.strip()]
    if not options:
        return lex.input.incorrect
    return random.choice(options)


@core.command
@core.alias('dice')
@core.rule(r'(?i)(^(?:[+-]?[0-9]*d(?:[0-9]+|f))+(?:[+-][0-9]+)?$)')
def roll(inp):
    """Return the result of rolling multiple dice."""
    if not inp.text:
        return lex.input.missing
    rolls = re.findall(r'([+-]?)([0-9]*)d([0-9]+|f)', inp.text)
    total = 0

    def roll_die(sign, count, sides):
        nonlocal total
        results = [random.randint(1, int(sides)) for _ in range(count)]
        if sign == '-':
            results = [-i for i in results]
        total += sum(results)
        return results

    def roll_fudge_die(count):
        nonlocal total
        results = [random.choice(['+1', '0', '-1']) for _ in range(count)]
        total += sum(map(int, results))
        return [i[0] for i in results]

    results = []
    for sign, count, sides in rolls:
        count = int(count) if count else 1
        if count > 5000:
            return lex.dice.too_many
        if sides == 'f':
            results.extend(roll_fudge_die(count))
        elif int(sides) < 2:
            return lex.dice.incorrect
        else:
            results.extend(roll_die(sign, count, sides))
    results = ', '.join(map(str, results[:20]))
    results = results.replace('+', '\x033+\x0F').replace('-', '\x034-\x0F')

    bonus = re.search(r'[+-][0-9]+$', inp.text)
    if bonus:
        total += int(bonus.group(0))

    return '{} ({}={})'.format(total, inp.text, results)


@core.command
@core.rule(r'(?i)(^(?=.*\bjarvis)(?=.*\bhugs?\b).*)')
def hugs(inp):
    return lex.silly.hugs


@core.command
def zyn(inp):
    return lex.silly.zyn


@core.command
def user(inp):
    user = inp.text.lower().replace(' ', '-')
    return 'http://www.wikidot.com/user:info/' + user


@core.rule(r'(?i)^\.help\b(.*)')
@parser.help
def _help(inp, *, command, elemental):
    if elemental:
        return
    url = 'http://scp-stats.wikidot.com/jarvis'
    return url if not command else url + '#' + command.replace(' ', '-')

###############################################################################


def tweet():
    twitter = core.config.twitter
    auth = tweepy.OAuthHandler(twitter.key, twitter.secret)
    auth.set_access_token(twitter.token, twitter.token_secret)

    api = tweepy.API(auth)

    timeline = api.user_timeline(count=100)
    timeline = [i for i in timeline if i.source == twitter.name]

    def pages(tag, rating, age):
        urls = [i.entities['urls'][0]['expanded_url'] for i in timeline]
        pages = [p for p in core.pages if p.url not in urls]
        pages = [p for p in pages if tag in p.tags and p.rating >= rating]
        date = arrow.now().replace(days=-int(age[1:])).format('YYYY-MM-DD')
        if age.startswith('>'):
            pages = [p for p in pages if date > p.created]
        elif age.startswith('<'):
            pages = [p for p in pages if date < p.created]
        return pages

    queue = {
        lex.tweet.new_scp: pages('scp', 40, '<30'),
        lex.tweet.new_tale: pages('tale', 20, '<30')}

    now = arrow.now().replace

    rpages = [i for i in timeline if i.text.startswith('Random SCP')]
    rpages = [i for i in rpages if i.created_at > now(days=-7).naive]
    if not rpages:
        queue[lex.tweet.random_scp] = pages('scp', 120, '>180')

    rpages = [i for i in timeline if i.text.startswith('Random tale')]
    rpages = [i for i in rpages if i.created_at > now(days=-2).naive]
    if not rpages:
        queue[lex.tweet.random_tale] = pages('tale', 60, '>180')

    for k, v in queue.items():
        if not v:
            continue
        page = random.choice(v)
        attr = page.build_attribution_string(
            templates=lex.tweet.attribution._raw)
        api.update_status(str(k(page=page, attr=attr)))
        return
