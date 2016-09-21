#!/usr/bin/env python3
"""Commands for the Image Team."""

###############################################################################
# Module Imports
###############################################################################

import functools
import natural.number
import pyscp
import re

from . import core, parser, lex


###############################################################################
# Global Variables
###############################################################################

wiki = pyscp.wikidot.Wiki('scp-stats')
wiki.auth(core.config.wiki.name, core.config.wiki.password)

scpwiki = pyscp.wikidot.Wiki('scp-wiki')
scpwiki.auth(core.config.wiki.name, core.config.wiki.password)


IMAGES = []
CLAIMS = {}
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
# Jinja Filters
###############################################################################


def imgstatuscolor(value):
    if value not in STATUS:
        return value
    color = '33222444'[STATUS.index(value)]
    return '\x02\x030,{} {} \x03\x02'.format(color, value)


lex.jinja2.filters['imgstatuscolor'] = imgstatuscolor


###############################################################################
# Internal Functions
###############################################################################


class Image:

    def __init__(self, url, page, category, **kwargs):
        self.url = url
        self.page = page
        self.category = category
        self.source = kwargs.get('source') or ''
        self.status = kwargs.get('status') or ''
        self.notes = kwargs.get('notes') or []

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
            IMAGES.append(Image(url=url, page=page, category=name,
                                source=source, status=status, notes=notes))


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

    source = []

    if category in CLAIMS:
        claim = 'This category is maintained by **{}**'
        claim = claim.format(CLAIMS[category])
        claim = '[[span class="claim"]]{}[[/span]]'.format(claim)
        source.append(claim)

    source.append(wtag('table', *rows))
    source = '\n'.join(source)

    wiki('images:' + category).create(
        source, category, comment='{}. -{}'.format(comment, user))


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
                inp.multiline = False
                return lex.images.not_found
            if not index and maxres and maxres < len(matches):
                inp.multiline = False
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


@core.command
@core.alias('img')
@parser.images
def images(inp, mode, **kwargs):
    return images.dispatch(inp, mode, **kwargs)


@core.require(channel=core.config.irc.imageteam, level=4)
@images.subcommand('scan')
@core.multiline
def scan(inp, *, pages):
    cats = set()
    counter = 0
    for page in pages:
        page = core.wiki(page)
        cat = get_page_category(page)
        if not cat:
            yield lex.images.scan.unknown_category(page=page.name)
            continue

        for img in page._soup.find(id='page-content')('img'):
            if any(i.url == img['src'] for i in IMAGES):
                continue
            img = Image(url=img['src'], page=page.url, category=cat)
            IMAGES.append(img)
            cats.add(cat)
            counter += 1

    for cat in cats:
        save_images(cat, 'added scan results', inp.user)

    yield lex.images.scan.done(count=counter)


@core.require(channel=core.config.irc.imageteam, level=4)
@images.subcommand('update')
@targeted(1)
def update(inp, *, images, url, page, source, status, notes):
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
    if notes:
        print(repr(image.notes))
        if image.notes:
            return lex.images.update.notes_conflict
        image.notes.append(notes)

    save_images(image.category, 'image updated', inp.user)
    return lex.images.update.done


@images.subcommand('list')
@core.multiline
@targeted(5)
def list_images(inp, *, images, terse):
    out = lex.images.list.terse if terse else lex.images.list.verbose
    yield from [
        out(url=i.url, page=i.page, source=i.source, status=i.status)
        for i in images]


@core.require(channel=core.config.irc.imageteam, level=4)
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


@core.require(channel=core.config.irc.imageteam, level=4)
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


@core.require(channel=core.config.irc.imageteam, level=4)
@images.subcommand('sync')
def sync(inp):
    load_images()
    return lex.images.sync


@core.require(channel=core.config.irc.imageteam, level=4)
@images.subcommand('add')
def add(inp, *, url, page):
    if not page:
        page = re.search(r'scp-wiki.wdfiles.com/local--files/([^/]+)/', url)
        if not page:
            return lex.images.add.offsite_image
        page = page.group(1)
    page = core.wiki(page)
    category = get_page_category(page)
    IMAGES.append(Image(url=url, page=page.url, category=category))
    save_images(category, 'image added', inp.user)
    return lex.images.add.done


def remove_image_component(source, image_url):
    name = image_url.split('/')[-1]
    regex = r'(?is)\[\[include\s+component:image-block.*{}.*\]\]'
    regex = regex.format(name)

    bracketed = re.search(regex, source).group(0)

    counter = 0
    for idx, char in enumerate(bracketed):
        if char == '[':
            counter += 1
        if char == ']':
            counter -= 1
        if counter == 0:
            break

    bracketed = bracketed[:idx + 1]
    bracketed = re.escape(bracketed)
    return re.sub(bracketed, '', source)


@core.require(channel=core.config.irc.imageteam, level=4)
@images.subcommand('remove')
@core.multiline
def remove(inp, *, page, images):
    page = scpwiki(page)

    source = page.source
    for i in images:
        source = remove_image_component(source, i)
    page.edit(source, comment='removed image code. -' + inp.user)
    yield lex.images.remove.page_edited

    text = lex.templates.removal.post._raw
    text += lex.templates.postfix._raw
    text = text.format(user=inp.user)
    page._thread.new_post(text)
    yield lex.images.remove.posted

    text = lex.templates.removal.pm._raw
    text += lex.templates.postfix._raw
    text = text.format(
        page=page.title, images='\n'.join(images), user=inp.user)
    for i in page.metadata:
        scpwiki.send_pm(i, text, title='Image Removal')
    yield lex.images.remove.pm_sent


@core.require(channel=core.config.irc.imageteam, level=4)
@images.subcommand('attribute')
def attribute(inp, *, page):
    messages = []
    url = core.wiki(page).url
    images = [i for i in IMAGES if i.page == url]

    for idx, image in enumerate(images):
        if not image.source or not image.status:
            continue

        if image.status == 'BY-SA CC':
            text = lex.templates.attribution.cc
        elif image.status == 'BY-NC-SA CC':
            text = lex.templates.attribution.cc_non_commercial
        elif image.status == 'PERMISSION GRANTED':
            text = lex.templates.attribution.permission
        else:
            continue

        text = text._raw.format(
            url=image.url,
            num=natural.number.ordinal(idx + 1),
            origin=image.source)
        messages.append(text)

    if not messages:
        return lex.images.attribute.not_found

    count = len(messages)
    messages = '\n----\n'.join(messages)
    messages += lex.templates.postfix._raw.format(user=inp.user)
    scpwiki(page)._thread.new_post(messages, title='Image Attribution')
    return lex.images.attribute.done(count=count)


@core.require(channel=core.config.irc.imageteam, level=4)
@images.subcommand('claim')
def claim(inp, *, category, purge):
    if not [i for i in IMAGES if i.category == category]:
        return lex.images.claim.unknown_category
    if not purge:
        CLAIMS[category] = inp.user
        save_images(category, 'category claimed', inp.user)
        return lex.images.claim.done
    else:
        CLAIMS.pop(category)
        save_images(category, 'category claim purged', inp.user)

###############################################################################

load_images()
