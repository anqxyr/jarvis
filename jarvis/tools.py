#!/usr/bin/env python3
"""Misc. bot commands."""

###############################################################################
# Module Imports
###############################################################################

import arrow
import functools
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


@core.command
@core.require(channel=core.config.irc.sssc)
def updatehelp(inp):
    """
    Update the help page.

    Staff-only command.
    """
    funcs = sorted(
        {v for k, v in core.COMMANDS.items()}, key=lambda x: x.__name__)
    core.stats_wiki('jarvis').create(
        utils.load_template('help.template', funcs=funcs), 'Help Test')
    return lex.updatehelp.finished


###############################################################################
# Twitter Announcements
###############################################################################


@functools.lru_cache()
def _get_twitter_api():
    tw = core.config.twitter
    auth = tweepy.OAuthHandler(tw.key, tw.secret)
    auth.set_access_token(tw.token, tw.token_secret)
    return tweepy.API(auth)


def _get_new_article(pages):
    """
    Get random new tale or scp article.

    Return random article yonger than 30 days, with rating of at least
    40 points for a skip and 20 points for a tale.
    """
    date = arrow.now().replace(days=-30).format('YYYY-MM-DD')
    pages = [p for p in pages if p.created > date]

    skips = [p for p in pages if 'scp' in p.tags and p.rating >= 40]
    tales = [p for p in pages if 'tale' in p.tags and p.rating >= 20]
    pages = skips + tales

    return random.choice(pages) if pages else None


def _get_old_article(pages, scp=True):
    """Get random old tale or scp article."""
    date = arrow.now().replace(days=-180).format('YYYY-MM-DD')
    pages = [p for p in pages if p.created < date]
    pages = [p for p in pages if ('scp' if scp else 'tale') in p.tags]
    pages = [p for p in pages if p.rating >= (120 if scp else 60)]
    return random.choice(pages)


def _get_post_data(api):
    tweets = api.user_timeline(count=100)
    tweets = [i for i in tweets if i.source == core.config.twitter.name]
    urls = [i.entities['urls'] for i in tweets]
    urls = [i[0]['expanded_url'] for i in urls if i]
    posted = [p for p in core.pages if p.url in urls]
    not_posted = [p for p in core.pages if p not in posted]

    new = _get_new_article(not_posted)
    if new:
        # post new articles if there are any
        return (lex.post_on_twitter.new, new)

    if tweets and tweets[0].created_at == arrow.now().naive:
        # if we posted an old article today already, don't post anything
        return None

    if any('scp' in p.tags for p in posted[:2]):
        # post tale, tale, tale, scp, tale, tale, tale, scp, tale...
        old = _get_old_article(not_posted, scp=False)
    else:
        old = _get_old_article(not_posted, scp=True)
    return (lex.post_on_twitter.old, old)


def post_on_twitter():
    api = _get_twitter_api()
    result = _get_post_data(api)

    if not result:
        return

    text, page = result
    attr = page.build_attribution_string(
        templates=lex.post_on_twitter.attribution._raw)
    text = str(text(page=page, attr=attr))

    try:
        api.update_status(text)
        core.log.info('Tweet: ' + page.name)
    except Exception as e:
        core.log.exception(e)
        raise e
