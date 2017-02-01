#!/usr/bin/env python3

###############################################################################
# Module Imports
###############################################################################

import jarvis
import pyscp
import requests
import re
import collections
import time
import urllib.parse

###############################################################################

wiki = pyscp.wikidot.Wiki('scp-wiki')
wiki.auth(jarvis.core.config.wiki.name, jarvis.core.config.wiki.password)


def reupload(page, *images):
    page = wiki(page.split('/')[-1])
    if 'author' in page.tags:
        return
    if not all(i in page.images for i in images):
        return
    source = page.source
    for img in images:
        data = requests.get(img).content
        name = img.split('/')[-1]
        if not any(i.name == urllib.parse.unquote(name) for i in page.files):
            try:
                page.upload(urllib.parse.unquote(name), data)
            except RuntimeError as e:
                print(page.url)
                print(name)
                print(urllib.parse.unquote(name))
                raise e
            time.sleep(2)
        source = re.sub(re.escape(img), name, source)
    if source == page.source:
        raise RuntimeError('Source unchanged')

    page.edit(source, comment='localize images')
    time.sleep(2)
    for img in images:
        update_index(page.name, img)
    print(page.name)


def update_index(page, image):
    new_url = 'http://scp-wiki.wdfiles.com/local--files/{}/{}'.format(
        page, image.split('/')[-1])
    command = '.im update {} --url {}'.format(image, new_url)
    inp = jarvis.core.Inp(
        command, 'anqxyr', '#test-channel',
        lambda x, private=False, notice=False: None,
        lambda: {'#test-channel': 4}, lambda x: None)
    jarvis.core.dispatcher(inp)


images = collections.defaultdict(list)
with open('scripts/images.txt') as file:
    for line in file:
        page, image = line.split()
        images[page].append(image)


for page, urls in sorted(images.items()):
    try:
        reupload(page, *set(urls))
    except Exception as e:
        print(page, urls)
        raise e


