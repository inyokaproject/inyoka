# -*- coding: utf-8 -*-
"""
    inyoka.utils.terminal
    ~~~~~~~~~~~~~~~~~~~~~

    Provides tools for terminals.

    :copyright: (c) 2007-2020 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
import sys
from itertools import cycle

_color_mapping = list(zip(list(range(8)),
    ('black', 'red', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'white')))
_colors = {code: '3%d' % idx for idx, code in _color_mapping}
_formats = {
    'bold': '1',
    'underscore': '4',
    'blink': '5',
    'reverse': '7',
    'conceal': '8'
}


def get_dimensions():
    """Return the current terminal dimensions or fall back to (80, 24)."""
    try:
        from struct import pack, unpack
        from fcntl import ioctl
        from termios import TIOCGWINSZ
        s = pack('HHHH', 0, 0, 0, 0)
        return unpack('HHHH', ioctl(sys.stdout.fileno(),
                                    TIOCGWINSZ, s))[1::-1]
    except:
        return (80, 24)


class FancyPrinter(object):
    """
    Prints colorful text into a terminal stream.
    """

    def __init__(self, stream=None, color=None, bold=False, underscore=False,
                 blink=False, reverse=False, conceal=False):
        self._stream = stream or sys.stdout
        self._color = color
        self._bold = bold
        self._underscore = underscore
        self._blink = blink
        self._conceal = conceal
        self._reverse = reverse

    def __getattr__(self, attr):
        if attr in _colors:
            attr = ('_color', attr)
        elif attr in _formats:
            attr = ('_' + attr, True)
        elif attr[:2] == 'no' and attr[2:] in _formats:
            attr = ('_' + attr[:2], False)
        else:
            raise AttributeError(attr)
        result = object.__new__(self.__class__)
        result.__dict__.update(self.__dict__)
        setattr(result, *attr)
        return result

    def __call__(self, text):
        if isinstance(text, str):
            encoding = getattr(self._stream, 'encoding', None) or 'latin1'
            text = text.encode(encoding, 'ignore')
        if not (hasattr(self._stream, 'isatty') and self._stream.isatty()):
            self._stream.write(text)
        else:
            codes = []
            if self._color is not None:
                codes.append(_colors[self._color])
            for format, val in _formats.items():
                if getattr(self, '_' + format):
                    codes.append(val)
            self._stream.write('\x1b[%sm%s\x1b[0m' % (';'.join(codes), text))
        return self

    __lshift__ = __call__


# original from Jochen Kupperschmidt with some modifications
class ProgressBar(object):
    """Visualize a status bar on the console."""

    def __init__(self, max_width):
        """Prepare the visualization."""
        self.max_width = max_width
        self.spin = cycle(r'-\|/').__next__
        self.tpl = '%-' + str(max_width) + 's ] %c %5.1f%%'
        show(' [ ')
        self.last_output_length = 0

    def update(self, percent):
        """Update the visualization."""
        # Remove last state.
        show('\b' * self.last_output_length)

        # Generate new state.
        width = int(percent / 100.0 * self.max_width)
        output = self.tpl % ('-' * width, self.spin(), percent)

        # Show the new state and store its length.
        show(output)
        self.last_output_length = len(output)


def show(string):
    """Show a string instantly on STDOUT."""
    sys.stdout.write(string)
    sys.stdout.flush()


def percentize(steps):
    """Generate percental values."""
    for i in range(steps + 1):
        yield i * 100.0 / steps
