#!/usr/bin/env python3
"""Bot Commands related to or interactin with the scp-wiki."""

###############################################################################
# Module Imports
###############################################################################

from . import ext
from . import tools
from . import lexicon

###############################################################################
# Find And Lookup Functions
###############################################################################


def find_author(pages, partial, key):
    """this is a test message"""
    authors = {p.author for p in pages}
    matches = sorted(a for a in authors if partial.lower() in a.lower())
    if not matches:
        return lexicon.author_not_found()
    elif len(matches) == 1:
        return get_author_summary(pages, matches[0])
    else:
        tools.save_search(
            lambda x: get_author_summary(pages, x), matches, key)
        return lexicon.multiple_matches(matches)


def find_page(pages, partial, key):
    words = partial.lower().split()
    matches = [p for p in pages if all(w in p.title.lower() for w in words)]
    if not matches:
        return lexicon.page_not_found()
    elif len(matches) == 1:
        return get_page_summary(matches[0])
    else:
        tools.save_search(matches, get_page_summary, key)
        return lexicon.multiple_matches([i.title for i in matches])


def find_scp(pages, partial, key):
    return find_page([p for p in pages if 'scp' in p.tags], partial, key)


def find_tale(pages, partial, key):
    return find_page([p for p in pages if 'scp' in p.tags], partial, key)

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
