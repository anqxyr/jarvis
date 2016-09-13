#!/usr/bin/env python3
"""Extended wrappers for pyscp core classes."""


###############################################################################
# Module Imports
###############################################################################

import collections

###############################################################################


class PageView:
    """Extended list of pyscp Pages."""

    ###########################################################################
    # Magic Methods
    ###########################################################################

    def __init__(self, pages):
        self.pages = list(pages)

    def __len__(self):
        return len(self.pages)

    def __eq__(self, other):
        return self.pages == other

    def __iter__(self):
        return iter(self.pages)

    def __getitem__(self, index):
        return self.pages[index]

    ###########################################################################
    # Filter Methods
    ###########################################################################

    def tags(self, tags):
        tags = tags.lower().split()
        all_ = {t.lstrip('+') for t in tags if t.startswith('+')}
        none = {t.lstrip('-') for t in tags if t.startswith('-')}
        any_ = {t for t in tags if t[0] not in '-+'}
        pages = [
            p for p in self.pages if (p.tags >= all_) and not (p.tags & none)]
        if any_:
            pages = [p for p in pages if p.tags & any_]
        return self.__class__(pages)

    def related(self, user, role=None):
        pages = [p for p in self.pages if user in p.metadata]
        if role:
            pages = [p for p in pages if p.metadata[user].role == role]
        return self.__class__(pages)

    def primary(self, user):
        results = []
        for p in self.related(user, 'author').articles:
            if 'rewrite' not in {i.role for i in p.metadata.values()}:
                results.append(p)
        for p in self.related(user, 'rewrite').articles:
            dates = [
                i.date for i in p.metadata.values() if i.role == 'rewrite']
            if not dates or p.metadata[user].date == max(dates):
                results.append(p)
        for p in self.related(user, 'translator').articles:
            results.append(p)
        return self.__class__(results)

    def with_rating(self, rating):
        pages = self.pages
        if rating.startswith('>'):
            rating = int(rating[1:])
            pages = [p for p in self.pages if p.rating > rating]
        elif rating.startswith('<'):
            rating = int(rating[1:])
            pages = [p for p in self.pages if p.rating < rating]
        elif '..' in rating:
            minr, maxr = map(int, rating.split('..'))
            pages = [p for p in self.pages if minr <= p.rating <= maxr]
        else:
            rating = int(rating.lstrip('='))
            pages = [p for p in self.pages if p.rating == rating]
        return self.__class__(pages)

    def created(self, created):
        pages = self.pages
        if created.startswith('>'):
            pages = [p for p in self.pages if p.created > created[1:]]
        elif created.startswith('<'):
            pages = [p for p in self.pages if p.created < created[1:]]
        elif '..' in created:
            mincr, maxcr = created.split('..')
            pages = [
                p for p in self.pages if
                (mincr <= p.created[:len(mincr)]) and
                (maxcr >= p.created[:len(maxcr)])]
        else:
            pages = [
                p for p in self.pages if p.created.startswith(created)]
        return self.__class__(pages)

    def sorted(self, key):
        pages = sorted(self.pages, key=lambda x: getattr(x, key))
        return self.__class__(pages)

    @property
    def articles(self):
        return self.tags('scp tale goi-format artwork -_sys -hub')

    ###########################################################################
    # Splitters
    ###########################################################################

    def split_page_type(self):
        keys = ['SCP Articles', 'Tales',
                'GOI-Format Articles', 'Artwork Galleries']
        values = [self.tags(i) for i in 'scp tale goi-format artwork'.split()]
        return collections.OrderedDict(
            (k, v) for k, v in zip(keys, values) if v)

    def split_relation(self, name):
        keys = ['Originals', 'Rewrites', 'Translations', 'Maintained']
        values = [
            self.related(name, i)
            for i in 'author rewrite translator maintainer'.split()]
        return collections.OrderedDict(
            (k, v) for k, v in zip(keys, values) if v)

    def split_date(self, span='month'):
        crop = dict(year=4, month=7, day=10)[span]
        pages = collections.defaultdict(list)
        for p in self.pages:
            pages[p.created[:crop]].append(p)
        return collections.OrderedDict(
            [(k, self.__class__(v)) for k, v in sorted(pages.items())])

    ###########################################################################
    # Scalar End-Points
    ###########################################################################

    @property
    def count(self):
        return len(self.pages)

    @property
    def rating(self):
        if not self.pages:
            return 0
        return sum(p.rating for p in self.pages)

    @property
    def authors(self):
        return list(sorted({i for p in self.pages for i in p.metadata}))

    @property
    def average(self):
        if not self.pages:
            return 0
        return self.rating // self.count
