#!/usr/bin/env python3
"""Bot Commands related to or interactin with the scp-wiki."""

###############################################################################
# Module Imports
###############################################################################

import collections
import re
import random

from . import tools, lexicon

###############################################################################
# Find And Lookup Functions
###############################################################################


def sanitize(fn):
    return lambda pages, inp, *args: (
        fn(pages, inp.strip().lower(), *args)
        if inp else lexicon.input.missing)


def search(results, channel, zero, one, many):
    if not results:
        return getattr(lexicon.not_found, zero)
    elif len(results) == 1:
        return one(results[0])
    else:
        tools.remember(results, channel, one)
        return many(results)


@sanitize
def find_page_by_title(pages, inp, channel):
    pages = [p for p in pages if set(p.title.split()) & set(inp.split())]
    return search(pages, channel, 'page', page_summary, search_results)


def find_tale_by_title(pages, inp, channel):
    return find_page_by_title(pages.tags('tale'), inp, channel)


@sanitize
def find_page_by_tags(pages, inp, channel):
    return search(
        pages.tags(inp), channel, 'page', page_summary, search_results)


@sanitize
def find_page_by_url(pages, inp):
    if '/forum/' in inp:
        return
    inp = inp.replace('/comments/show', '')
    pages = [p for p in pages if p.url == inp]
    return search(
        pages, None, 'page', page_summary, lambda x: page_summary(x[0]))


@sanitize
def find_author(pages, inp, channel):
    results = sorted(
        {i for p in pages for i in p.metadata if inp in i.lower()})
    return search(
        results, channel, 'author',
        lambda x: author_summary(pages, x), tools.choose_input)


@sanitize
def update_author_details(pages, inp, channel, wiki):

    def update(name):
        p = wiki('user:' + name.lower())
        p.create(name, author_details(pages, name), 'automated update')
        return p.url
    results = sorted(
        {i for p in pages for i in p.metadata if inp in i.lower()})
    return search(results, channel, 'author', update, tools.choose_input)

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


def get_section(template, func, args, descriptions):
    template = template.replace('*', '\x02')
    results = []
    for value, desc in zip(map(func, args.split()), descriptions.split()):
        if value:
            results.append(template.format(value, desc))
    return results


def page_summary(page):
    rels = collections.defaultdict(list)
    for user, (rel, date) in page.metadata.items():
        rels[rel].append(user)
    for rel, users in rels.items():
        *head, tail = users
        rels[rel] = '{} and {}'.format(', '.join(head), tail) if head else tail
    attribution = '; '.join(get_section(
        '{1} by {0}', lambda x: rels[x],
        'author rewrite translator maintainer',
        'written rewritten translated maintained'))
    return lexicon.summary.page.format(
        page=page, attribution=attribution)


def author_summary(pages, name):
    pages = pages.related(name)
    url = pages.tags('author')[0].url if pages.tags('athor') else None
    url = '({}) '.format(url) if url else ''
    pages = pages.articles

    tags = get_section(
        '*{}* {}', lambda x: pages.tags(x).count,
        'scp tale goi-format artwork',
        'SCPs tales GOI-formats art-galleries')
    rels = get_section(
        '*{}* {}', lambda x: pages.related(name, x).count,
        'author rewrite translator maintainer',
        'originals rewrites translated maintained')
    tags, rels = ', '.join(tags), ', '.join(rels)
    last = sorted(pages, key=lambda x: x.created, reverse=True)[0]

    return lexicon.summary.author.format(
        name=name, url=url, pages=pages, rels=rels, tags=tags,
        primary=pages.primary(name), last=last)


def author_details(pages, name):
    primary = pages.primary(name)

    row = '||{1}||{0.count}||{0.rating}||{0.average}||'
    stats = [
        '[[div class="stats"]]',
        '||~ Category||~ Page Count||~ Net Rating||~ Average||',
        row.format(primary, 'Total'),
        '||||||||~ ||']
    stats.extend(get_section(
        row, lambda x: primary.tags(x),
        'scp tale goi-format artwork', 'SCPs Tales GOI-format Artwork'))
    stats.append('||||||||~ ||')
    stats.extend(get_section(
        row, lambda x: pages.related(name, x).articles,
        'author rewrite translator maintainer',
        'Originals Rewrites Translated Maintained'))
    stats.append('[[/div]]')
    stats.append('~~~~')

    row = '||{0.title}||{0.rating:+d}||{1}||{2}||{0.created:.10}||{3}||'
    articles = [
        '++ Articles',
        '[[div class="articles"]]',
        '||~ Title||~ Rating||~ Tags||~ Link||~ Created||~ Relation||']
    pages = [p for p in pages.related(name) if p.tags]
    for p in sorted(pages, key=lambda x: x.rating, reverse=True):
        tags = ', '.join(sorted(p.tags)) or ' '
        link = '[[[{}|{}]]]'.format(p.url, p.url.split('/')[-1])
        relation = p.metadata[name][0]
        articles.append(row.format(p, tags, link, relation))
    articles.append('[[/div]]')

    return '\n'.join(stats + articles)

###############################################################################
# Misc
###############################################################################


def get_error_report(pages):
    pages = [p for p in pages if ':' not in p.url]
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


def get_random_page(pages, tags):
    pages = pages.tags(tags) if tags else pages.articles
    if pages:
        return page_summary(random.choice(pages))
    else:
        return lexicon.not_found.page
