#!/usr/bin/env python3

###############################################################################
# Module Imports
###############################################################################


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
