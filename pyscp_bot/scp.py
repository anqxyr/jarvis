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
    *{au.name}* ({au_url}) has written *{au.pages.count}* pages
    (*{au[scp].count}* SCPs,
     *{au[tale].count}* tales,
     *{au[goi-format].count}* GOI-format pages,
     *{au[artwork].count}* artwork galleries)
    (*{au.rewrites.count}* rewrites).
    They have *{au.pages.rating}* net upvotes
    with an average of *{au.pages.average_rating}*.
    Their latest page is *{last.title}* at *{last.rating:+d}*."""

    template = ' '.join(template.split())
    output = template.format(au=au, au_url=au_url, last=au.pages[0])

    output = re.sub(r'\*?(0|None)\*?[ \w-]*(?=(\)|,))', '', output)
    output = re.sub(r' \(\)|(, (?=[,\)]))|((?<=\(), )', '', output)
    output = output.replace('scp-wiki.wikidot.com', 'www.scp-wiki.net')
    output = output.replace('*', '\x02')
    return output
