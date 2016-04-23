#!/usr/bin/env python3
"""Extended wrappers for pyscp core classes."""


###############################################################################
# Module Imports
###############################################################################


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

    def __iter__(self):
        return iter(self.pages)

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

    def related(self, user, rel=None):
        pages = [p for p in self.pages if user in p.metadata]
        if rel:
            pages = [p for p in pages if p.metadata[user][0] == rel]
        return self.__class__(pages)

    def primary(self, user):
        results = []
        for p in self.related(user, 'author').articles:
            if not any(rel == 'rewrite' for rel, date in p.metadata.values()):
                results.append(p)
        for p in self.related(user, 'rewrite').articles:
            dates = [
                date for rel, date in p.metadata.values() if
                date and rel == 'rewrite']
            if not dates or p.metadata[user][1] == max(dates):
                results.append(p)
        for p in self.related(user, 'translator').articles:
            results.append(p)
        return self.__class__(results)

    @property
    def articles(self):
        return self.tags(*'scp tale goi-format artwork -_sys -hub'.split())

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
    def average(self):
        if not self.pages:
            return 0
        return self.rating // self.count
