#!/usr/bin/env python3
"""Commands for the Image Team."""

###############################################################################
# Module Imports
###############################################################################

import collections
import functools
import pyscp
import re

from . import core, parser, lexicon

###############################################################################
# Global Variables
###############################################################################

wiki = pyscp.wikidot.Wiki('scp-stats')
wiki.auth(core.config['wiki']['name'], core.config['wiki']['pass'])

IMAGES = collections.defaultdict(list)
STATUS = {
    'PUBLIC DOMAIN': 3,
    'BY-SA CC': 3,
    'PERMISSION GRANTED': 2,
    'BY-NC-SA CC': 2,
    'AWAITING REPLY': 2,
    'SOURCE UNKNOWN': 4,
    'UNABLE TO CONTACT': 4,
    'PERMANENTLY REMOVED': 4}


###############################################################################
# Internal Functions
###############################################################################


class Image:

    def __init__(self, url, page, source, status, notes, category):
        self.url = url
        self.page = page
        self.source = source
        self.status = status
        self.notes = notes
        self.category = category

    @property
    def status_col(self):
        if self.status:
            return'\x030,{} {} \x03'.format(STATUS[self.status], self.status)
        return ''

    @property
    def url_t(self):
        return self.url.split('/')[-1]

    @property
    def page_t(self):
        return self.page.split('/')[-1]

    @property
    def source_t(self):
        source = re.match(r'https*://(?:www\.)?([^/]+)', self.source)
        return source.group(1) if source else ''


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
            notes = notes.find('td').text.split('\n')
            notes = [i for i in notes if i]
            IMAGES[name].append(Image(url, page, source, status, notes, name))


def save_images(category, comment, user):

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

        page = wtag('cell', '[{} {}]'.format(image.page, image.page_t))

        source = image.source_t
        source = source and '[{} {}]'.format(image.source, source)
        source = wtag('cell', source)

        status = image.status.lower().replace(' ', '-')
        status = '[[span class="{}"]]{}[[/span]]'.format(status, image.status)
        status = wtag('cell', status)

        notes = wtag('cell', ' _\n'.join(image.notes), colspan=4)

        rows.append(wtag('row', img, page, source, status))
        rows.append(wtag('row', notes))

    wiki('images:' + category).create(
        wtag('table', *rows), category,
        comment='{} [{}]'.format(comment, user))


def targeted(maxres):

    def deco(fn):

        @functools.wraps(fn)
        def inner(inp, *args, target, index, **kwargs):
            images = [i for cat in IMAGES for i in IMAGES[cat]]
            matches = []
            for img in images:
                if target in [img.page, img.page_t]:
                    matches.append(img)
                if img.url == target:
                    return fn(inp, *args, images=[img], **kwargs)
            if not matches:
                return lexicon.images.not_found
            if not index and maxres != 'all' and maxres < len(matches):
                return lexicon.images.too_many.format(count=len(matches))
            if index:
                if index < 1 or index > len(matches):
                    return lexicon.input.bad_index
                matches = [matches[index - 1]]
            return fn(inp, *args, images=matches, **kwargs)

        return inner

    return deco


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
    funcs = [images_scan, images_update, images_list, images_notes]
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
        if any(i.url == img['src'] for i in IMAGES[cat]):
            continue
        img = Image(img['src'], page.url, '', '', [], cat)
        IMAGES[cat].append(img)
        counter += 1
    save_images(cat, 'add images via page scan', inp.user)

    if counter == 1:
        return lexicon.images.scan.added_one
    elif counter > 1:
        return lexicon.images.scan.added_several.format(count=counter)
    else:
        return lexicon.images.scan.added_none


@parser.images_update
@targeted(1)
def images_update(inp, *, images, url, page, source, status):
    image = images[0]
    if url:
        image.url = url
    if page:
        image.page = page
    if source:
        image.source = source
    if status:
        if status not in STATUS and status != '-':
            return lexicon.images.update.bad_status
        image.status = status

    save_images(image.category, 'update image', inp.user)
    return lexicon.images.update.done


@core.multiline
@parser.images_list
@targeted(5)
def images_list(inp, *, images, terse):
    out = lexicon.images.list.terse if terse else lexicon.images.list.verbose
    return [out.format(image=i) for i in images]


@parser.images_notes
@targeted(1)
def images_notes(inp, *, images, append, purge, list):
    image = images[0]

    if append:
        image.notes.append(append)
        save_images(image.category, 'append image notes', inp.user)
        return lexicon.images.notes.append

    if purge:
        image.notes = []
        save_images(image.category, 'purge image notes', inp.user)
        return lexicon.images.notes.purge

    if list:
        if not image.notes:
            return lexicon.images.notes.empty
        inp.multiline = True
        return image.notes


###############################################################################

load_images()
