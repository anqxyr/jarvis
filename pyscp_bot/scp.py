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
    au_url = au_pages[0].url if au_pages else None

    template = """
    \x02{au.name}\x02 ({au_url}) has written \x02{au.pages.count}\x02 pages
    (\x02{au[scp].count}\x02 SCPs,
     \x02{au[tale].count}\x02 tales,
     \x02{au[goi-format].count}\x02 GOI-format pages,
     \x02{au[artwork].count}\x02 artwork galleries)
    (\x02{au.rewrites.count}\x02 rewrites).
    They have \x02{au.pages.rating}\x02 net upvotes
    with an average of \x02{au.pages.average_rating}\x02.
    Their latest page is \x02{last.title}\x02 at \x02{last.rating:+d}\x02."""

    template = ' '.join(template.split())
    output = template.format(au=au, au_url=au_url, last=au.pages[0])

    output = re.sub(r'\*?(0|None)\*?[ \w-]*(?=(\)|,))', '', output)
    output = re.sub(r' \(\)|(, (?=[,\)]))|((?<=\(), )', '', output)
    return output
