#!/usr/bin/env python3
"""Bot Commands related to or interactin with the scp-wiki."""

###############################################################################
# Module Imports
###############################################################################

import arrow
import collections
import re
import random

from . import core, tools, lexicon, stats

###############################################################################

lc_cooldown = {}

###############################################################################
# Find And Lookup Functions
###############################################################################


def sanitize(fn):
    return lambda inp, *args: (
        fn(inp.strip().lower(), *args) if inp else lexicon.input.missing)


def search(results, channel, zero, one, many):
    if not results:
        return getattr(lexicon.not_found, zero)
    elif len(results) == 1:
        return one(results[0])
    else:
        tools.remember(results, channel, one)
        return many(results)


@sanitize
def find_page_by_title(inp, channel, pages=None):
    pages = pages or core.pages
    all_ = {t.lstrip('+') for t in inp.split() if t.startswith('+')}
    none = {t.lstrip('-') for t in inp.split() if t.startswith('-')}
    partial = {t for t in inp.split() if t[0] not in '-+'}
    results = []
    for p in pages:
        words = re.split(r'[\s-]', p.title.lower())
        words = set(re.sub(r'[^\w]', '', i) for i in words)
        if not (words >= all_) or (words & none):
            continue
        if partial and not any(i in p.title.lower() for i in partial):
            continue
        results.append(p)
    return search(results, channel, 'page', page_summary, search_results)


def find_tale_by_title(inp, channel):
    return find_page_by_title(inp, channel, core.pages.tags('tale'))


@sanitize
def find_page_by_tags(inp, channel):
    return search(
        core.pages.tags(inp), channel, 'page', page_summary, search_results)


@sanitize
def find_page_by_url(inp):
    if '/forum/' in inp:
        return
    inp = inp.replace('/comments/show', '')
    pages = [p for p in core.pages if p.url == inp]
    return search(
        pages, None, 'page', page_summary, lambda x: page_summary(x[0]))


@sanitize
def find_author(inp, channel):
    results = sorted(
        {i for p in core.pages for i in p.metadata if inp in i.lower()})
    return search(
        results, channel, 'author', author_summary, tools.choose_input)


@sanitize
def update_author_details(inp, channel):
    results = sorted(
        {i for p in core.pages for i in p.metadata if inp in i.lower()})
    return search(
        results, channel, 'author', stats.update_user, tools.choose_input)

###############################################################################
# Output Generation Functions
###############################################################################


def search_results(results):
    results = [p.title for p in results]
    head, tail = results[:3], results[3:]
    output = ', '.join('\x02{}\x02'.format(i) for i in head)
    if tail:
        output += ' and {} more...'.format(len(tail))
    return output


def page_summary(page):

    def get_segment(rel, date, users):
        name = dict(author='written', rewrite='rewritten',
                    translator='translated', maintainer='maintained')[rel]
        if not date and rel == 'author':
            date = page.created
        if date:
            date = ' ' + arrow.get(date).humanize()
        *head, tail = users
        users = '{} and {}'.format(', '.join(head), tail) if head else tail
        return '{}{} by {}'.format(name, date, users)

    rels = collections.defaultdict(list)
    for user, (rel, date) in page.metadata.items():
        rels[(rel, date)].append(user)
    items = sorted(rels.items(), key=lambda x: (
        'author rewrite translator maintainer'
        .split().index(x[0][0]), x[0][1]))

    attribution = '; '.join(get_segment(r, d, u) for (r, d), u in items)
    return lexicon.summary.page.format(page=page, attribution=attribution)


def author_summary(name):
    pages = core.pages.related(name)
    url = pages.tags('author')[0].url if pages.tags('author') else None
    url = ' ({})'.format(url) if url else ''
    pages = pages.articles
    template = '\x02{1.count}\x02 {0}'.format
    tags = ', '.join(template(*i) for i in pages.split_page_type().items())
    rels = ', '.join(template(*i) for i in pages.split_relation(name).items())
    last = sorted(pages, key=lambda x: x.created, reverse=True)[0]
    return lexicon.summary.author.format(
        name=name, url=url, pages=pages, rels=rels, tags=tags,
        primary=pages.primary(name), last=last)

###############################################################################
# Misc
###############################################################################


def get_error_report():
    pages = [p for p in core.pages if ':' not in p.url]
    output = ''
    no_tags = ['\x02{}\x02'.format(p.title) for p in pages if not p.tags]
    if no_tags:
        output += 'Pages without tags: {}. '.format(', '.join(no_tags))
    no_title = ['\x02{}\x02'.format(p.title) for p in pages
                if re.search(r'/scp-[0-9]+$', p.url) and
                p._raw_title == p.title]
    if no_title:
        output += 'Pages without titles: {}.'.format(', '.join(no_title))
    if output:
        return output
    return 'I found no errors.'


def get_random_page(tags):
    pages = core.pages.tags(tags) if tags else core.pages.articles
    if pages:
        return page_summary(random.choice(pages))
    else:
        return lexicon.not_found.page


def get_last_created(channel):
    global lc_cooldown
    now = arrow.now()
    if channel in lc_cooldown and (now - lc_cooldown[channel]).seconds < 120:
        return [lexicon.spam]
    lc_cooldown[channel] = now
    return map(page_summary, core.wiki.list_pages(
        body='title created_by created_at rating', limit=3,
        order='created_at desc'))
