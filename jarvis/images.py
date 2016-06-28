#!/usr/bin/env python3
"""Commands for the Image Team."""

###############################################################################
# Module Imports
###############################################################################

import collections
import pyscp
import re

from . import core, parser, lexicon

###############################################################################
# Global Variables
###############################################################################

wiki = pyscp.wikidot.Wiki('scp-stats')
wiki.auth(core.config['wiki']['name'], core.config['wiki']['pass'])

IMAGES = collections.defaultdict(list)

###############################################################################
# Internal Functions
###############################################################################


class Image:

    def __init__(self, url, page, source, status, notes):
        self.url = url
        self.page = page
        self.source = source
        self.status = status
        self.notes = notes


def load_images():
    soup = wiki('images')._soup
    for category in soup(class_='collapsible-block'):
        name = category.find(class_='collapsible-block-link').text
        rows = category('tr')
        for row, notes in zip(rows[::2], rows[1::2]):
            url, page, source, status = row('td')
            url = url.img['src']
            page = page.a['href']
            source = source.a['href'] if source('a') else ''
            status = status.text
            notes = notes.find('td').text
            IMAGES[name].append(Image(url, page, source, status, notes))


def save_images(category):

    def wtag(name, *data, **kwargs):
        args = []
        for k, v in kwargs.items():
            args.append('{}="{}"'.format(k, v))
        result = ['[[{} {}]]'.format(name, ' '.join(args))]
        result.extend(data)
        result.append('[[/{}]]'.format(name))
        return '\n'.join(result)

    rows = []
    for image in sorted(IMAGES[category], key=lambda x: x.page):

        img = '[[image {0.url} width="100px"]]'.format(image)
        img = wtag('cell', img, rowspan=2)

        page = image.page.split('/')[-1]
        page = '[{} {}]'.format(image.page, page)
        page = wtag('cell', page)

        source = re.match(r'https*://(?:www\.)?([^/]+)', image.source)
        source = source.group(1) if source else ''
        source = source and '[{} {}]'.format(image.source, source)
        source = wtag('cell', source)

        status = image.status.lower().replace(' ', '-')
        status = '[[span class="{}"]]{}[[/span]]'.format(status, image.status)
        status = wtag('cell', status)

        rows.append(wtag('row', img, page, source, status))
        rows.append(wtag('row', wtag('cell', image.notes, colspan=4)))

    wiki('images:' + category).create(wtag('table', *rows), category)


def get_page_category(page):
    if 'scp' in page.tags and re.match(r'.*scp-[0-9]+$', page.url):
        num = int(page.url.split('-')[-1])
        num = (num // 100) * 100
        return '{:03d}-{:03d}'.format(num or 2, num + 99)

    for tag in ('joke', 'explained', 'archived'):
        if tag in page.tags:
            return tag

    if 'goi-format' in page.tags:
        return 'goi'

    if 'tale' in page.tags:
        l = page.title[0].lower()
        for k, v in dict(g='A-F', n='G-M', u='N-T').items():
            if l < k:
                return v
        return 'U-Z'

    if page.url in core.wiki('001').links:
        return '001'


###############################################################################
# Bot Commands
###############################################################################


@core.command
@parser.images
def images(inp, mode):
    funcs = [images_scan]
    funcs = {f.__name__.split('_')[-1]: f for f in funcs}
    return funcs[mode](inp)


@parser.images_scan
def images_scan(inp, *, page):
    page = core.wiki(page)
    cat = get_page_category(page)
    if not cat:
        return lexicon.images.scan.unknown_category

    counter = 0
    for img in page._soup.find(id='page-content')('img'):
        print(img)
        if any(i.url == img['src'] for i in IMAGES[cat]):
            continue
        img = Image(img['src'], page.url, '', '', '')
        IMAGES[cat].append(img)
        counter += 1
    save_images(cat)

    if counter == 1:
        return lexicon.images.scan.added_one
    elif counter > 1:
        return lexicon.images.scan.added_several.format(count=counter)
    else:
        return lexicon.images.scan.added_none


###############################################################################

load_images()
