#!/usr/bin/env python3

###############################################################################
# Module Imports
###############################################################################


import jarvis
import yaml

###############################################################################


class Inp(jarvis.core.Inp):

    def __init__(self, text, user, channel):
        self.output = []
        super().__init__(
            text, user, channel,
            lambda text, private=None, notice=None: self.output.append(text),
            lambda: None, lambda: None)

    def send(self, text, private=None, notice=None, multiline=None):
        multiline = multiline if multiline is not None else self.multiline
        if multiline:
            self.output.extend([i for i in text if i])
        elif text:
            self.output.append(text)


def run(text, *args, _user='test-user', _channel='test-channel', **kwargs):
    """
    Run the input through the dispatcher and return the result.

    This creates an input instances, then overrides its send methods to
    save the result into the output variable, runs the disptacher and
    returns the output.
    """
    text = text.split()
    text.extend(map(str, args))
    for k, v in kwargs.items():
        text.append('--{} {}'.format(k, v))
    text = ' '.join(text)

    inp = Inp(text, _user, _channel)
    jarvis.core.dispatcher(inp)

    out = inp.output
    return out if len(out) > 1 else out[0] if out else None


###############################################################################


with open('jarvis/tests/resources/samples.yaml') as file:
    samples = jarvis.utils.AttrDict.from_nested_dict(yaml.safe_load(file))
