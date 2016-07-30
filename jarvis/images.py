#!/usr/bin/env python3
"""Commands for the Image Team."""

###############################################################################
# Module Imports
###############################################################################

import functools
import pyscp
import re

from . import core, parser, lex

###############################################################################
# Global Variables
###############################################################################

wiki = pyscp.wikidot.Wiki('scp-stats')
wiki.auth(core.config['wiki']['name'], core.config['wiki']['pass'])

IMAGES = []
STATUS = [
    'PUBLIC DOMAIN',
    'BY-SA CC',
    'PERMISSION GRANTED',
    'BY-NC-SA CC',
    'AWAITING REPLY',
    'SOURCE UNKNOWN',
    'UNABLE TO CONTACT',
    'PERMANENTLY REMOVED']


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
            colors = '33222444'
            colors = {a: b for a, b in zip(range(len(colors)), colors)}
            color = colors[STATUS.index(self.status)]
            return'\x02\x030,{} {} \x03\x02'.format(color, self.status)
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
            IMAGES.append(Image(url, page, source, status, notes, name))


def save_images(category, comment, user):

    def wtag(name, *data, **kwargs):
        args = []
        for k, v in kwargs.items():
            args.append('{}="{}"'.format(k, v))
        result = ['[[{} {}]]'.format(name, ' '.join(args))]
        result.extend(data)
        result.append('[[/{}]]'.format(name))
        return '\n'.join(result)

    images = [i for i in IMAGES if i.category == category]
    rows = []
    for image in sorted(images, key=lambda x: x.page):

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
        comment='{}. -{}'.format(comment, user))


def targeted(maxres=None):

    def deco(fn):

        @functools.wraps(fn)
        def inner(inp, *args, target, index, **kwargs):
            matches = []
            for img in IMAGES:
                if target in [img.page, img.page_t]:
                    matches.append(img)
                if img.url == target:
                    return fn(inp, *args, images=[img], **kwargs)
            if not matches:
                return lex.images.not_found
            if not index and maxres and maxres < len(matches):
                return lex.images.too_many(count=len(matches))
            if index:
                if index < 1 or index > len(matches):
                    return lex.input.bad_index
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

    if page.url in core.wiki('scp-001').links:
        return '001'

###############################################################################
# Bot Commands
###############################################################################


@parser.images
@core.command
def images(inp, mode, **kwargs):
    return images.dispatch(inp, mode, **kwargs)


@images.subcommand('scan')
def scan(inp, *, page):
    page = core.wiki(page)
    cat = get_page_category(page)
    if not cat:
        return lex.images.scan.unknown_category

    counter = 0
    for img in page._soup.find(id='page-content')('img'):
        if any(i.url == img['src'] for i in IMAGES):
            continue
        img = Image(img['src'], page.url, '', '', [], cat)
        IMAGES.append(img)
        counter += 1
    save_images(cat, 'new page indexed', inp.user)

    if counter == 1:
        return lex.images.scan.added_one
    elif counter > 1:
        return lex.images.scan.added_several(count=counter)
    else:
        return lex.images.scan.added_none


@images.subcommand('update')
@targeted(1)
def update(inp, *, images, url, page, source, status):
    image = images[0]
    if url:
        image.url = url
    if page:
        image.page = page
    if source:
        image.source = source
    if status:
        if status not in STATUS and status != '-':
            return lex.images.update.bad_status
        image.status = status

    save_images(image.category, 'image updated', inp.user)
    return lex.images.update.done


@images.subcommand('list')
@core.multiline
@targeted(5)
def list_images(inp, *, images, terse):
    out = lex.images.list.terse if terse else lex.images.list.verbose
    return [out(image=i) for i in images]


@images.subcommand('notes')
@targeted(1)
def notes(inp, *, images, append, purge, list):
    image = images[0]

    if append:
        image.notes.append(append)
        save_images(image.category, 'image notes appended', inp.user)
        return lex.images.notes.append

    if purge:
        image.notes = []
        save_images(image.category, 'image notes purged', inp.user)
        return lex.images.notes.purge

    if list:
        if not image.notes:
            return lex.images.notes.empty
        inp.multiline = True
        return image.notes


@images.subcommand('purge')
@targeted()
def purge(inp, *, images):
    global IMAGES
    IMAGES = [i for i in IMAGES if i not in images]
    save_images(images[0].category, 'records purged', inp.user)
    return lex.images.purge(count=len(images))


@images.subcommand('search')
@core.multiline
@targeted(1)
def search(inp, *, images):
    image = images[0]
    yield 'http://tineye.com/search?url=' + image.url
    yield 'http://www.google.com/searchbyimage?image_url=' + image.url


@images.subcommand('stats')
def stats(inp, *, category):
    images = [i for i in IMAGES if i.category == category]
    per_status = []
    for s in STATUS:
        img = [i for i in images if i.status == s]
        if not img:
            continue
        per_status.append('{} - {}'.format(img[0].status_col, len(img)))
    per_status = ', '.join(per_status)
    not_reviewed = len([i for i in images if not i.status])
    return lex.images.stats(
        count=len(images),
        per_status=per_status,
        not_reviewed=not_reviewed)


@images.subcommand('add')
def add(inp, *, url, page):
    pass

###############################################################################

load_images()
