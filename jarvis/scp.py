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


def find_author(pages, partial, key='global'):
    if not partial:
        return lexicon.input.incorrect
    partial = partial.strip().lower()
    authors = {u for p in pages for u in p.metadata}
    matches = sorted(a for a in authors if partial in a.lower())
    if not matches:
        return lexicon.not_found.author
    elif len(matches) == 1:
        return get_author_summary(pages, matches[0])
    else:
        tools.remember(matches, key, lambda x: get_author_summary(pages, x))
        return tools.choose_input(matches)


def update_author_details(pages, partial, stwiki, key='global'):
    if not partial:
        return lexicon.input.incorrect
    partial = partial.strip().lower()
    authors = {u for p in pages for u in p.metadata}
    matches = sorted(a for a in authors if partial in a.lower())
    if not matches:
        return lexicon.not_found.author
    elif len(matches) == 1:
        data = get_author_details(pages, matches[0])
        p = stwiki('user:' + matches[0])
        p.create(data, matches[0], 'automated update')
        return p.url
    else:
        tools.remember(
            matches, key,
            lambda x: update_author_details(pages, x, stwiki, key))
        return tools.choose_input(matches)


def find_page(pages, partial, key='global'):
    if not partial:
        return lexicon.input.missing
    words = partial.lower().split()
    matches = [p for p in pages if all(w in p.title.lower() for w in words)]
    if not matches:
        return lexicon.not_found.page
    elif len(matches) == 1:
        return get_page_summary(matches[0])
    else:
        tools.remember(matches, key, get_page_summary)
        return display_search_results([i.title for i in matches])


def find_scp(pages, partial, key='global'):
    return find_page([p for p in pages if 'scp' in p.tags], partial, key)


def find_tale(pages, partial, key='global'):
    return find_page([p for p in pages if 'tale' in p.tags], partial, key)


def find_tags(pages, tags, key='global'):
    if not tags:
        return lexicon.input.missing
    tags = set(tags.strip().split())
    matches = [p for p in pages if p.tags >= set(tags)]
    if not matches:
        return lexicon.not_found.page
    elif len(matches) == 1:
        return get_page_summary(matches[0])
    else:
        tools.remember(matches, key, get_page_summary)
        return display_search_results([i.title for i in matches])


def lookup_url(pages, url):
    if '/forum/' in url:
        return
    pages = [p for p in pages if p.url == url.lower()]
    if not pages:
        return lexicon.not_found.page
    else:
        return get_page_summary(pages[0])


def display_search_results(results):
    head, tail = results[:3], results[3:]
    output = ', '.join('\x02{}\x02'.format(i) for i in head)
    if tail:
        output += ' and {} more...'.format(len(tail))
    return output

###############################################################################
# Output Generation Functions
###############################################################################


def get_section(template, func, args, descriptions):
    template = template.replace('*', '\x02')
    results = []
    for value, desc in zip(map(func, args.split()), descriptions.split()):
        if value:
            results.append(template.format(value, desc))
    return results


def get_author_summary(pages, name):
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


def get_page_summary(page):
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


def get_author_details(pages, name):
    primary = pages.primary(name)

    row = '||{1}||{0.count}||{0.rating}||{0.average}||'
    stats = [
        '[[div class="stats"]]',
        '||~ Category||~ Page Count||~ Net Rating||~ Average Rating||',
        row.format(primary, 'Total')]
    stats.extend(get_section(
        row, lambda x: primary.tags(x),
        'scp tale goi-format artwork', 'SCPs Tales GOI-format Artwork'))
    stats.append('||||||||||')
    stats.extend(get_section(
        row, lambda x: pages.related(name, x).articles,
        'author rewrite translator maintainer',
        'Originals Rewrites Translated Maintained'))
    stats.append('[[/div]]')

    row = '||{0.title}||{0.rating:+d}||{1}||{2}||{0.created:.10}||{3}||'
    articles = [
        '++ Articles',
        '[[div class="articles"]]',
        '||~ Title||~ Rating||~ Tags||~ Link||~ Created||~ Relation||']
    for p in sorted(pages.related(name), key=lambda x: x.rating, reverse=True):
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


def get_random_page(pages, tag):
    pages = pages[tag.strip().lower()] if tag else pages
    if pages:
        return get_page_summary(random.choice(pages))
    else:
        return lexicon.not_found.page
