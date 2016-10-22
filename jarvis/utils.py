#!/usr/bin/env python3

###############################################################################
# Module Imports
###############################################################################

import jinja2

###############################################################################
# Jinja2
###############################################################################


env = jinja2.Environment(
    loader=jinja2.PackageLoader('jarvis', 'resources'))
env.filters['hasattr'] = hasattr
env.filters['filldict'] = lambda x, y: [
    (k, v) if k else (y, v) for k, v in x.items()]


def load_template(name, **kwargs):
    template = env.get_template(name)
    return template.render(**kwargs)


###############################################################################


class AttrDict(dict):
    """Dictionary subclass whose entries can be accessed by attributes."""

    def __init__(self, *args, **kwargs):
        super(AttrDict, self).__init__(*args, **kwargs)
        self.__dict__ = self

    @staticmethod
    def from_nested_dict(data):
        """Construct nested AttrDicts from nested dictionaries."""
        if not isinstance(data, dict):
            return data
        return AttrDict({
            key: AttrDict.from_nested_dict(data[key])
            for key in data})

###############################################################################


def catch(exceptions, return_value=None):

    def decorator(func):

        def inner(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except exceptions:
                return return_value

        return inner

    return decorator
