#!/usr/bin/env python3
"""Commands for the Image Team."""

###############################################################################
# Module Imports
###############################################################################

import functools
import natural.number
import pyscp
import re
import time

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
    global IMAGES
    IMAGES = []
    soup = wiki('images')._soup
    for category in soup(class_='collapsible-block'):
        name = category.find(class_='collapsible-block-link').text
        claim = category.find(class_='claim')
        if claim:
            CLAIMS[name] = claim.text.split()[-1]
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
@core.alias('im')
@core.alias('img')
@parser.images
def images(inp, mode, **kwargs):
    """Image Team magic toolkit."""
    return images.dispatch(inp, mode, **kwargs)


@images.subcommand('scan')
@core.require(channel=core.config.irc.imageteam, level=2)
@core.multiline
def scan(inp, *, pages):
    """
    Scan wiki pages.

    Finds all images in the specified pages and adds them to the index.
    """
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


@images.subcommand('update')
@core.require(channel=core.config.irc.imageteam, level=2)
@targeted(1)
def update(inp, *, images, url, page, source, status, notes):
    """Update image records."""
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
        if image.notes:
            return lex.images.update.notes_conflict
        image.notes.append(notes)

    save_images(image.category, 'image updated', inp.user)
    return lex.images.update.done


@images.subcommand('list')
@core.multiline
@targeted(5)
def list_images(inp, *, images, terse):
    """Display image records."""
    out = lex.images.list.terse if terse else lex.images.list.verbose
    yield from [
        out(url=i.url, page=i.page, source=i.source, status=i.status)
        for i in images]


@images.subcommand('notes')
@core.require(channel=core.config.irc.imageteam, level=2)
@targeted(1)
def notes(inp, *, images, append, purge, list):
    """Add, change, remove, or display image notes."""
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
@core.require(channel=core.config.irc.imageteam, level=2)
@targeted()
def purge(inp, *, images):
    """Delete all records of the image from the index."""
    global IMAGES
    IMAGES = [i for i in IMAGES if i not in images]
    save_images(images[0].category, 'records purged', inp.user)
    return lex.images.purge(count=len(images))


@images.subcommand('search')
@core.multiline
@targeted(1)
def search(inp, *, images):
    """Return reverse-image-seach links for the image."""
    image = images[0]
    yield lex.images.search.tineye(url=image.url)
    yield lex.images.search.google(url=image.url)


@images.subcommand('stats')
def stats(inp, *, category):
    """Show review statistics for an image category."""
    images = [i for i in IMAGES if i.category == category]
    return lex.images.stats(
        count=len(images),
        images=[i for i in images if i.status],
        not_reviewed=len([i for i in images if not i.status]))


@images.subcommand('sync')
@core.require(channel=core.config.irc.imageteam, level=2)
def sync(inp):
    """
    Reload image index.

    Useful when the index page had to be manually edited for any reason.
    """
    load_images()
    return lex.images.sync


@images.subcommand('add')
@core.require(channel=core.config.irc.imageteam, level=2)
def add(inp, *, url, page):
    """
    Add image to the index.

    This subcommand is to be used when only when 'scan' is not applicable,
    such as in situation where the image have been taken down from the page
    before being added to the index.

    If the image is properly uploaded to the page, jarvis should be able
    to determine the page it belongs to based solely on image url. Otherwise,
    name of the image's parent page must be supplied.
    """
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
    regex = regex.format(re.escape(name))

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


@images.subcommand('remove')
@core.require(channel=core.config.irc.imageteam, level=2)
@core.multiline
def remove(inp, *, page, images):
    """
    Remove an image from the page.

    Edits the page to remove the image code from the page source. If the image
    is uploaded to the page, the image file itself will not and should not
    be deleted.

    Additionally, jarvis will automatically announce image removal via a
    discussion post, and send wikidot PMs to all authors of the page.

    When using this command, please visually confirm afterwards that no
    elements of the page except the image were removed, and that the
    formatting of the page is unaffected by the removal.
    """
    page = scpwiki(page)

    source = page.source
    for i in images:
        source = remove_image_component(source, i)
    page.edit(source, comment='removed image code. -' + inp.user)
    yield lex.images.remove.page_edited

    time.sleep(5)

    text = lex.templates.removal.post._raw
    text += lex.templates.postfix._raw
    text = text.format(user=inp.user)
    page._thread.new_post(text)
    yield lex.images.remove.posted

    time.sleep(5)

    text = lex.templates.removal.pm._raw
    text += lex.templates.postfix._raw
    text = text.format(
        page=page.title, images='\n'.join(images), user=inp.user)
    for i in page.metadata:
        scpwiki.send_pm(i, text, title='Image Removal')
    yield lex.images.remove.pm_sent


@images.subcommand('attribute')
@core.require(channel=core.config.irc.imageteam, level=2)
def attribute(inp, *, page):
    """
    Attribute page images.

    Jarvis will make a post in the page's discussion thread, attributing all
    applicable indexed images found on the page to their respective sources.
    The text of the attributions is based on the license of the image. Public
    Domain images are not attributed.
    """
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


@images.subcommand('claim')
@core.require(channel=core.config.irc.imageteam, level=2)
def claim(inp, *, category, purge):
    """
    Reserve image category.

    Adds a note on the index page indicating that the particular image
    category is being reviewed by the specific user.
    """
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
