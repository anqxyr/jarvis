#!/usr/bin/env python3
"""Misc. bot commands."""

###############################################################################
# Module Imports
###############################################################################

import arrow
import bs4
import functools
import pint
import random
import tweepy

from . import core, parser, lex, __version__, utils

###############################################################################
# Global Variables
###############################################################################

BOOTTIME = arrow.now()
UREG = pint.UnitRegistry(autoconvert_offset_to_baseunit=True)

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
    return lex.hugs


@core.command
def zyn(inp):
    """Marp."""
    return lex.zyn


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
    core.stats_wiki('jarvis').edit(
        utils.load_template('help.template', funcs=funcs))
    return lex.updatehelp


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
    goi = [p for p in pages if 'goi-format' in p.tags and p.rating >= 20]
    pages = skips + tales + goi

    return random.choice(pages) if pages else None


def _get_old_article(pages, scp=True):
    """Get random old tale or scp article."""
    date = arrow.now().replace(days=-180).format('YYYY-MM-DD')
    pages = [p for p in pages if p.created < date]
    if scp:
        pages = [p for p in pages if 'scp' in p.tags]
        pages = [p for p in pages if p.rating >= 120]
    else:
        pages = [
            p for p in pages if 'tale' in p.tags or 'goi-format' in p.tags]
        pages = [p for p in pages if p.rating >= 60]
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
    attr = page.build_attribution_string(templates={
        i: '{user}' for i in 'author rewrite translation maintainer'.split()})
    text = str(text(page=page, attr=attr))
    if len(text) >= 140:
        text = lex.post_on_twitter.short(page=page)

    try:
        api.update_status(text)
        core.log.info('Tweet: ' + page.name)
    except Exception as e:
        core.log.exception(e)
        raise e

###############################################################################
# On Page
###############################################################################


@functools.lru_cache(maxsize=400)
def _members_on_page(page):
    data = core.wiki._module('membership/MembersListModule', page=page)
    soup = bs4.BeautifulSoup(data['body'], 'lxml')
    authors = soup(class_='printuser')
    authors = [i.text.lower() for i in authors]
    total = soup.find(class_='pager-no').text.split()[-1]
    return int(total), authors


@core.command
@core.multiline
@parser.onpage
def onpage(inp, user, oldest_first):
    """
    Find the member list page on which the given user appears.

    Iterates over the member lists until it find the required user.
    Be default, starts with the newest members and continues back in time.
    """
    yield lex.onpage.working
    total, _ = _members_on_page(1)
    pages = range(1, total + 1)
    if not oldest_first:
        pages = reversed(pages)

    for page in pages:
        if user in _members_on_page(page)[1]:
            yield lex.onpage.found(user=user, page=page)
            return
    yield lex.onpage.not_found(user=user)


@core.command
def mylevel(inp):
    """Show the user's permission level in the current channel."""
    return lex.mylevel(
        user=inp.user, channel=inp.channel,
        level=inp.privileges.get(inp.channel))


###############################################################################
# Convert
###############################################################################


@core.command
@parser.convert
def convert(inp, *, expression, precision):
    """
    Convert between different measurement units.

    The full list of supported units can be found here:
    https://github.com/hgrecco/pint/blob/master/pint/default_en_0.6.txt
    """
    try:
        source, destination = expression.split(' to ')
        source_value = source.split(' ')[0]
        float(source_value)
    except (IndexError, ValueError):
        return lex.convert.syntax_error
    try:
        result = UREG(source).to(destination)
    except Exception as e:
        return lex.convert.conversion_error(text=str(e))

    if precision is False:
        if '.' not in source_value:
            sigfig = len(source_value.rstrip('0')) - len(source_value)
        else:
            sigfig = len(source_value.split('.')[-1])
        value = round(result.magnitude, int(sigfig))
        if int(sigfig) <= 0:
            value = int(value)
    elif precision is True:
        value = result.magnitude
    else:
        value = round(result.magnitude, precision)
        if precision <= 0:
            value = int(value)

    return lex.convert.result(
        source=source,
        value=value,
        dimensionality=result.dimensionality,
        units=result.units)
