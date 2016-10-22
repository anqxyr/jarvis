#!/usr/bin/env python3
"""Misc. bot commands."""

###############################################################################
# Module Imports
###############################################################################

import arrow
import random
import tweepy

from . import core, parser, lex, __version__, utils

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
    """Show additional results from the last used command."""
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
    options = list(map('\x02{}\x02'.format, sorted(options)))
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
    """
    Output version info.

    Shows bot's bio, version number, github link, and uptime.
    """
    uptime = (arrow.now() - BOOTTIME)
    m, s = divmod(uptime.seconds, 60)
    h, m = divmod(m, 60)
    return lex.version(
        version=__version__, days=uptime.days, hours=h, minutes=m)


@core.require(channel=core.config.irc.sssc)
@core.command
def rejoin(inp):
    """
    Enter the specified channel.

    Staff-only command.
    """
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


def get_throw(count, sides):
    if sides == 'f':
        die = {-1: '\x034-\x0F', 0: '0', 1: '\x033+\x0F'}
    else:
        die = {i: str(i) for i in range(1, int(sides) + 1)}

    if count < 0:
        count = -count
        die = {-k: v for k, v in die.items()}

    results = [random.choice(list(die.keys())) for _ in range(count)]
    total = sum(results)
    expanded = ','.join(die[i] for i in results[:10])

    return total, expanded


@core.command
@core.alias('roll')
@parser.dice
def dice(inp, *, throws, bonus, text, expand):
    """
    Return the result of rolling multiple dice.

    Examples of valid dice throws:
    2d5
    d100 -10d5 +3d20
    3d20 +5 open the door
    3df 2d2
    """
    total = 0
    expanded = {}

    for throw in throws:
        count, sides = throw.split('d')
        count = int(count) if count else 1
        if int(count) > 5000:
            return lex.dice.too_many_dice
        if sides != 'f' and not 2 <= int(sides) <= 5000:
            return lex.dice.bad_side_count
        subtotal, subexp = get_throw(count, sides)
        total += subtotal
        expanded[throw] = subexp

    expanded = ['{}={}'.format(i, expanded[i]) for i in throws]
    expanded = '|'.join(expanded)

    if bonus:
        expanded = '{}|bonus={:+d}'.format(expanded, bonus)
        total += bonus

    msg = 'expanded' if expand else 'annotated' if text else 'simple'
    msg = getattr(lex.dice.output, msg)
    return msg(total=total, expanded=expanded, text=text)


@core.command
@core.rule(r'(?i)(^(?=.*\bjarvis)(?=.*\bhugs?\b).*)')
def hugs(inp):
    """Who's a good bot? Jarvy is a good bot."""
    return lex.silly.hugs


@core.command
def zyn(inp):
    """Marp."""
    return lex.silly.zyn


@core.command
def user(inp):
    """Get wikidot profile url for the user."""
    user = inp.text.lower().replace(' ', '-')
    return 'http://www.wikidot.com/user:info/' + user


@core.rule(r'(?i)^\.help\b(.*)')
@parser.help
def help(inp, *, command, elemental):
    """Give a link to the help page."""
    if elemental:
        return
    url = 'http://scp-stats.wikidot.com/jarvis'
    return url if not command else url + '#' + command.replace(' ', '-')


@core.command
@core.require(channel=core.config.irc.sssc)
def reloadtitles(inp):
    """Update title cache."""
    core.wiki.titles.cache_clear()
    core.wiki.titles()
    return lex.reloadtitles


###############################################################################
# Update Help
###############################################################################


#@core.command
#@core.require(channel=core.config.irc.sssc)
#def updatehelp(inp):
def updatehelp():
    funcs = sorted(
        {v for k, v in core.COMMANDS.items()}, key=lambda x: x.__name__)
    core.stats_wiki('help-test').create(
        utils.load_template('help.template', funcs=funcs), 'Help Test')


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
