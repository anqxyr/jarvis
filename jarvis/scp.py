#!/usr/bin/env python3
"""Bot Commands related to or interactin with the scp-wiki."""

###############################################################################
# Module Imports
###############################################################################

import re

from . import ext
from . import tools
from . import lexicon

###############################################################################
# Find And Lookup Functions
###############################################################################


def find_author(pages, partial, key):
    authors = {p.author for p in pages}
    matches = sorted(a for a in authors if partial.lower() in a.lower())
    if not matches:
        return lexicon.author_not_found()
    elif len(matches) == 1:
        return get_author_summary(pages, matches[0])
    else:
        tools.remember(matches, key, lambda x: get_author_summary(pages, x))
        return lexicon.unclear_input(matches)


def find_page(pages, partial, key):
    words = partial.lower().split()
    matches = [p for p in pages if all(w in p.title.lower() for w in words)]
    if not matches:
        return lexicon.page_not_found()
    elif len(matches) == 1:
        return get_page_summary(matches[0])
    else:
        tools.remember(matches, key, get_page_summary)
        return display_search_results([i.title for i in matches])


def find_scp(pages, partial, key):
    return find_page([p for p in pages if 'scp' in p.tags], partial, key)


def find_tale(pages, partial, key):
    return find_page([p for p in pages if 'scp' in p.tags], partial, key)


def find_tags(pages, tags, key):
    matches = [p for p in pages if p.tags >= set(tags)]
    if not matches:
        return lexicon.page_not_found()
    elif len(matches) == 1:
        return get_page_summary(matches[0])
    else:
        tools.remember(matches, key, get_page_summary)
        return display_search_results([i.title for i in matches])


def lookup_url(pages, url):
    if '/forum/' in url:
        return
    url = url.replace('www.scp-wiki.net', 'scp-wiki.wikidot.com')
    pages = [p for p in pages if p.url == url]
    if not pages:
        return lexicon.page_not_found()
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


def get_author_summary(pages, name):
    au = ext.User(pages, name)

    au_pages = pages(tags='author', author=name)
    url = '({0[0].url}) '.format(au_pages) if au_pages else ''
    url = url.replace('scp-wiki.wikidot.com', 'www.scp-wiki.net')
    wrote = [
        '\x02{0[scp].count}\x02 SCPs',
        '\x02{0[tale].count}\x02 tales',
        '\x02{0[goi-format].count}\x02 GOI-format pages',
        '\x02{0[artwork].count}\x02 artwork galleries']
    wrote = [i.format(au) for i in wrote if '\x020\x02' not in i.format(au)]
    wrote = '({})'.format(', '.join(wrote))
    rewrite = ' ({} rewrites)'.format(au.rewrites.count) if au.rewrites else ''

    pages = '\x02{}\x02 {}has written \x02{}\x02 pages {}{}.'.format(
        au.name, url, au.pages.count, wrote, rewrite)
    rating = (
        'They have \x02{}\x02 net upvotes with an average of \x02{}\x02.'
        .format(au.pages.rating, au.pages.average))
    last = 'Their latest page is \x02{}\x02 at \x02{:+d}\x02.'.format(
        au.pages[0].title, au.pages[0].rating)

    return ' '.join([pages, rating, last])


def get_page_summary(page):
    inv = {}
    for k, v in page.authors.items():
        inv[v] = inv.get(v, [])
        inv[v].append(k)

    authors = []
    if 'author' in inv and len(inv['auhtor']) == 1:
        authors.append('written by {}'.format(inv['author'][0]))
    if 'author' in inv and len(inv['auhtor']) > 1:
        authors.append('co-written by {}'.format(' and '.join(inv['author'])))
    if 'rewrite' in inv:
        authors.append('rewritten by {}'.format(inv['rewrite'][0]))
    authors = ', '.join(authors)

    output = '\x02{0.title}\x02 ({1}; rating: {0.rating:+d}) - {0.url}'.format(
        page, authors)
    return output.replace('scp-wiki.wikidot.com', 'www.scp-wiki.net')


def get_author_details(pages, name):
    au = ext.User(pages, name)

    counts = [
        '||Pages:||{0.pages.count}||',
        '||● SCPs:||{0[scp].count}||',
        '||● Tales:||{0[tale].count}||',
        '||● GOI-format:||{0[goi-format].count}||',
        '||● Artwork:||{0[artwork].count}||',
        '||● Rewrites:||{0.rewrites.count}||']
    counts = [i.format(au) for i in counts if '||0||' not in i.format(au)]

    ratings = [
        '||Rating:||{0.pages.rating} ({0.pages.average})||',
        '||● SCPs:||{0[scp].rating} ({0[scp].average})||',
        '||● Tales:||{0[tale].rating} ({0[tale].average})||',
        '||● GOI-format:||{0[goi-format].rating} ({0[goi-format].average})||',
        '||● Artwork:||{0[artwork].rating} ({0[artwork].average})||',
        '||● Rewrites:||{0.rewrites.rating} ({0.rewrites.average})||']
    ratings = [
        i.format(au) for i in ratings if '||0 (0)||' not in i.format(au)]

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
        relation = p.authors[au.name]
        template = (
            '||{0.title}||> {0.rating:+d}||{1}||{2}||{0.created:.10}||= {3}||')
        articles.append(template.format(p, tags, link, relation))
    articles.append('[[/div]]')

    return '\n'.join(intro + articles)

###############################################################################
# Misc
###############################################################################


def get_error_report(pages):
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
