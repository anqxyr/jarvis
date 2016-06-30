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
STATUS = {
    'PUBLIC DOMAIN': 3,
    'BY-SA CC': 3,
    'PERMISSION GRANTED': 3,
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
    def colstatus(self):
        if self.status:
            return'\x030,{} {} \x03'.format(STATUS[self.status], self.status)
        return ''


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
        rows.append(
            wtag('row', wtag('cell', ' _\n'.join(image.notes), colspan=4)))

    wiki('images:' + category).create(
        wtag('table', *rows), category,
        comment='{} [{}]'.format(comment, user))


def find_images(target, index):
    images = [i for cat in IMAGES for i in IMAGES[cat]]
    matches = []
    for img in images:
        if img.page == target or img.page.split('/')[-1] == target:
            matches.append(img)
        if img.url == target:
            return [img]
    if not index:
        return matches
    if index < 1 or index > len(matches):
        return
    return [matches[index - 1]]


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
        img = Image(img['src'], page.url, '', '', '')
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
def images_update(inp, *, target, index, url, page, source, status):
    images = find_images(target, index)
    if not images:
        return lexicon.images.not_found
    if len(images) > 1:
        return lexicon.images.too_many.format(len(images))

    image = images[0]
    if url:
        image.url = url
    if page:
        image.page = page
    if source:
        image.source = source
    if status:
        if status not in STATUS:
            return lexicon.images.update.bad_status
        image.status = status

    save_images(image.category, 'update image', inp.user)
    return lexicon.images.update.done


@parser.images_list
def images_list(inp, *, target, index):
    if not target and not index:
        return lexicon.images.list.all

    images = find_images(target, index)
    if not images:
        return lexicon.images.not_found
    if len(images) > 5:
        return lexicon.images.too_many.format(count=len(images))

    inp.multiline = True
    return [lexicon.images.list.image.format(image=i) for i in images]


@parser.images_notes
def images_notes(inp, *, target, index, append, purge, list):
    images = find_images(target, index)
    if not images:
        return lexicon.images.not_found
    if len(images) > 1:
        return lexicon.images.too_many.format(count=len(images))
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
