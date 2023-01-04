# -*- coding: utf-8 -*-
"""
    inyoka.utils.timer
    ~~~~~~~~~~~~~~~~~~

    :copyright: (c) 2007-2023 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
import time


class StopWatch(object):
    """Very simple timer abstraction"""

    def __init__(self):
        self._start = 0.0
        self._stop = 0.0
        self._duration = 0.0

    def start(self):
        self._start = time.time()

    def stop(self):
        self._stop = time.time()
        self._duration = self._stop - self._start

    @property
    def duration(self):
        """Return the duration of the call.

        If `stop` was not called yet return the duration
        from start untill now.
        """
        if self._stop == 0.0:
            return time.time() - self._start
        return self._duration
