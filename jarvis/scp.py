#!/usr/bin/env python3
"""Bot Commands related to or interactin with the scp-wiki."""

###############################################################################
# Module Imports
###############################################################################

import arrow
import collections
import random as rand
import re

from . import core, parser, lexicon, stats, tools

###############################################################################
# Find And Lookup Functions
###############################################################################


def page_search(inp, results):
    """Process page search results."""
    if not results:
        return lexicon.not_found.page
    elif len(results) == 1:
        return page_summary(results[0])
    else:
        tools.save_results(inp, results, page_summary)
        return search_results(results)


def author_search(inp, func):
    """Find author via partial name, and process results."""
    text = (inp.text or inp.user).lower()
    authors = {i for p in core.pages for i in p.metadata}
    results = sorted(i for i in authors if text in i.lower())
    if not results:
        return lexicon.not_found.author
    elif len(results) == 1:
        return func(results[0])
    else:
        tools.save_results(inp, results, func)
        return tools.choose_input(results)


def find_pages(
        pages, partial, exclude, strict,
        tags, author, rating, created, fullname):
    if tags:
        pages = pages.tags(tags)
    if author:
        pages = pages.related(author)
    if rating:
        pages = pages.with_rating(rating)
    if created:
        pages = pages.created(created)

    if fullname:
        return next(p for p in pages if p.title.lower() == fullname)

    results = []
    for p in pages:
        words = p.title.lower().split()
        words = {''.join(filter(str.isalnum, w)) for w in words}

        if exclude and words & set(exclude):
            continue
        if strict and not words >= set(strict):
            continue
        if partial and not all(i in p.title.lower() for i in partial):
            continue

        results.append(p)
    return results


@core.command
@parser.search
def search(inp, **kwargs):
    if not inp.text:
        return lexicon.input.incorrect
    return page_search(inp, find_pages(core.pages, **kwargs))


@core.command
@parser.search
def tale(inp, **kwargs):
    if not inp.text:
        return lexicon.input.incorrect
    return page_search(inp, find_pages(core.pages.tags('tale'), **kwargs))


@core.command
@parser.search
def wanderers_library(inp, **kwargs):
    if not inp.text:
        return lexicon.input.incorrect
    return page_search(inp, find_pages(core.wlpages, **kwargs))


@core.command
def tags(inp):
    return page_search(inp, core.pages.tags(inp.text))


@core.command
def name_lookup(inp):
    pages = [p for p in core.pages if p.url.split('/')[-1] == inp.text.lower()]
    return page_search(inp, pages)


@core.command
def author(inp):
    return author_search(inp, author_summary)


@core.command
def author_details(inp):
    return author_search(inp, stats.update_user)


###############################################################################
# Output Generation Functions
###############################################################################


def search_results(results):
    """Display search results."""
    results = [p.title for p in results]
    head, tail = results[:3], results[3:]
    output = ', '.join('\x02{}\x02'.format(i) for i in head)
    if tail:
        output += ' and {} more...'.format(len(tail))
    return output


def page_summary(page):
    """Compose page summary."""
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
    """Compose author summary."""
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


@core.command
def errors(inp):
    """!errors -- Get error report."""
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


@core.command
@parser.search
def random(inp, **kwargs):
    pages = core.pages if not inp.text else find_pages(core.pages, **kwargs)
    if pages:
        return page_summary(rand.choice(pages))
    else:
        return lexicon.not_found.page


@core.command
@core.multiline
def last_created(inp, cooldown={}, **kwargs):
    kwargs = dict(
        body='title created_by created_at rating',
        order='created_at desc',
        limit=3)
    now = arrow.now()

    if inp.channel not in cooldown:
        pass
    elif (now - cooldown[inp.channel]).seconds < 120:
        yield lexicon.spam
        return

    cooldown[inp.channel] = now

    yield from map(page_summary, core.wiki.list_pages(**kwargs))


@core.command
@parser.unused
def unused(inp, *, random, last, prime, palindrome, divisible):
    numbers = range(2, 3000)

    if prime:
        numbers = [i for i in numbers if all(i % k for k in range(2, i))]
    if palindrome:
        numbers = [
            i for i in numbers if str(i).zfill(3) == str(i).zfill(3)[::-1]]
    if divisible:
        numbers = [i for i in numbers if i % divisible == 0]

    slots = ['scp-{:03d}'.format(i) for i in numbers]
    used_slots = {p._body['fullname'] for p in core.pages.tags('scp')}
    unused_slots = [i for i in slots if i not in used_slots]

    if not unused_slots:
        return lexicon.not_found.unused

    if random:
        result = rand.choice(unused_slots)
    elif last:
        result = unused_slots[-1]
    else:
        result = unused_slots[0]

    return 'http://www.scp-wiki.net/' + result
