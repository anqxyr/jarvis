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

    def __getitem__(self, key):
        """
        Filter pages based on the key and return a PageView of results.

        Because accessing pages based on their tags is a very common
        operation, __getitem__ is override to accept a tag string as well as
        the usual indexes.
        """
        if isinstance(key, str):
            return self.__class__(p for p in self.pages if key in p.tags)
        return self.pages[key]

    def __call__(self, **kwargs):
        results = self.pages
        if 'tags' in kwargs:
            for tag in kwargs['tags'].split():
                results = [p for p in results if tag in p.tags]
        if 'author' in kwargs:
            results = [p for p in results if kwargs['author'] in p.authors]
        return results

    ###########################################################################
    # Other Nice Methods
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


class User:
    """Extended User Methods."""

    def __init__(self, pages, name):
        """Create user."""
        good_tags = {'scp', 'tale', 'goi-format', 'artwork'}
        self.pages = PageView(
            p for p in pages if name == p.author and p.tags & good_tags)
        self.name = name

    def __getitem__(self, key):
        return self.pages[key]

    ###########################################################################

    @property
    def rewrites(self):
        return PageView(
            p for p in self.pages if p.authors[self.name] == 'rewrite')
