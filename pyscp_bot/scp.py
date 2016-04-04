#!/usr/bin/env python3
"""Bot Commands related to or interactin with the scp-wiki."""

###############################################################################
# Module Imports
###############################################################################

import arrow
import re

from . import ext

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
    wrote = '({}) '.format(', '.join(wrote))
    rewrite = ' ({} rewrites)'.format(au.rewrites.count) if au.rewrites else ''

    pages = '\x02{}\x02 {}has written \x02{}\x02 pages {}{}.'.format(
        au.name, url, au.pages.count, wrote, rewrite)
    rating = (
        'They have \x02{}\x02 net upvotes with an average of \x02{}\x02.'
        .format(au.pages.rating, au.pages.average))
    last = 'Their latest page is \x02{}\x02 at \x02{:+d}\x02.'.format(
        au.pages[0].title, au.pages[0].rating)

    return ' '.join([pages, rating, last])
