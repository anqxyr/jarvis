#!/usr/bin/env python3
"""Bot Commands related to or interactin with the scp-wiki."""

###############################################################################
# Module Imports
###############################################################################

import collections
import re
import random

from . import ext, tools, lexicon

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


def get_section(func, template, keys, aliases):
    results = []
    for count, alias in zip(map(func, keys), aliases):
        if count:
            results.append(template.format(count, alias))
    return results


def get_author_summary(pages, name):
    au = ext.User(pages, name)

    aupage = [p for p in pages['author'] if name in p.metadata]
    url = '({0[0].url}) '.format(aupage) if aupage else ''

    tags = get_section(
        lambda x: au[x].count, '\x02{}\x02 {}',
        'scp tale goi-format artwork'.split(),
        ['SCPs', 'tales', 'GOI-format pages', 'artwork galleries'])
    types = get_section(
        lambda x: au.pages(**{x: name}).count, '\x02{}\x02 {}',
        'author rewrite translator maintainer'.split(),
        'originals rewrites translated maintained'.split())
    tags, types = ', '.join(tags), ', '.join(types)

    pages = (
        '\x02{}\x02 {}has \x02{}\x02 pages ({}) ({}).'
        .format(au.name, url, au.pages.count, types, tags))
    rating = (
        'They have \x02{}\x02 net upvotes with an average of \x02{}\x02.'
        .format(au.owned.rating, au.owned.average))
    last = (
        'Their latest page is \x02{0.title}\x02 at \x02{0.rating:+d}\x02.'
        .format(sorted(au.pages, key=lambda x: x.created, reverse=True)[0]))

    return ' '.join([pages, rating, last])


def get_page_summary(page):
    rels = collections.defaultdict(list)
    for user, (rel, date) in page.metadata.items():
        rels[rel].append((user, date))
    for k, v in rels.items():
        dates = [d for u, d in v if d]
        if dates:
            users = [u for u, d in v if d == max(dates)]
        else:
            users = [u for u, d in v]
        *head, tail = sorted(users)
        rels[k] = '{} and {}'.format(', '.join(head), tail) if head else tail
    attrib = []
    for key, alias in zip(
            ['author', 'rewrite', 'translator', 'maintainer'],
            ['written', 'rewritten', 'translated', 'maintained']):
        if key not in rels:
            continue
        attrib.append('{} by {}'.format(alias, rels[key]))
    return '\x02{0.title}\x02 ({1}; rating: {0.rating:+d}) - {0.url}'.format(
        page, '; '.join(attrib))


def get_author_details(pages, name):
    au = ext.User(pages, name)

    counts = ['||Pages:||{}||'.format(au.pages.count)]
    ratings = ['||Rating:||{}||'.format(au.owned.rating)]
    for li, pv, fn in zip(
            [counts, ratings], [au.pages, au.owned],
            [
                lambda x: x.count,
                lambda x: '{} / {}'.format(x.rating, x.average)]):
        li.extend(get_section(
            lambda x: fn(pv[x]), '||-- {1}:||{0}||',
            'scp tale goi-format artwork'.split(),
            'SCPs Tales GOI-format Artwork'.split()))
        li.extend(get_section(
            lambda x: fn(pv(**{x: name})), '||-- {1}:||{0}||',
            'author rewrite translator maintainer'.split(),
            'Originals Rewritten Translated Maintained'.split()))
    intro = ['[[div class="author-summary"]]']
    intro.extend(counts)
    intro.append('|| || ||')
    intro.extend(ratings)
    intro.extend(['[[/div]]', '~~~~'])

    articles = [
        '[[div class="articles"]]',
        '++ Articles',
        '||~ Title||~ Rating||~ Tags||~ Link||~ Created||~ Relation||']
    for p in sorted(au.pages, key=lambda x: x.rating, reverse=True):
        tags = ', '.join(sorted(p.tags))
        link = '[[[{}|{}]]]'.format(p.url, p.url.split('/')[-1])
        relation = p.metadata[au.name][0]
        template = (
            '||{0.title}||> {0.rating:+d}||{1}||{2}||{0.created:.10}||= {3}||')
        articles.append(template.format(p, tags, link, relation))
    articles.append('[[/div]]')

    return '\n'.join(intro + articles)

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
