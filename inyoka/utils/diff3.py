# -*- coding: utf-8 -*-
"""
    inyoka.utils.diff3
    ~~~~~~~~~~~~~~~~~~

    A diff3 algorithm implementation, based on the version of the
    MoinMoin wiki engine and some other diff/udiff stuff.


    :copyright: (c) 2007-2020 by the Inyoka Team, see AUTHORS for more details.
    :copyright: (c) by Florian Festi.
    :license: BSD, see LICENSE for more details.
"""
import difflib
import heapq
import itertools
import re

from django.utils.html import escape
from django.utils.translation import ugettext as _

DEFAULT_MARKERS = (
    '<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<',
    '========================================',
    '>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>',
)


class DiffConflict(ValueError):
    """
    Raised if a conflict occoured and the merging operated in non
    conflict mode.
    """

    def __init__(self, old_lineno, other_lineno, new_lineno):
        ValueError.__init__(self, 'conflict on line %d' % other_lineno)
        self.old_lineno = old_lineno
        self.other_lineno = other_lineno
        self.new_lineno = new_lineno


def merge(old, other, new, allow_conflicts=True, markers=None):
    """
    Works like `stream_merge` but returns a string.
    """
    return '\n'.join(stream_merge(old, other, new, allow_conflicts, markers))


def stream_merge(old, other, new, allow_conflicts=True, markers=None):
    """
    Merges three strings or lists of lines.  The return values is an iterator.
    Per default conflict markers are added to the source, you can however set
    :param allow_conflicts: to `False` which will get you a `DiffConflict`
    exception on the first encountered conflict.
    """
    if isinstance(old, str):
        old = old.splitlines()
    elif not isinstance(old, list):
        old = list(old)
    if isinstance(other, str):
        other = other.splitlines()
    elif not isinstance(other, list):
        other = list(other)
    if isinstance(new, str):
        new = new.splitlines()
    elif not isinstance(new, list):
        new = list(new)
    left_marker, middle_marker, right_marker = markers or DEFAULT_MARKERS

    old_lineno = other_lineno = new_lineno = 0
    old_len = len(old)
    other_len = len(other)
    new_len = len(new)

    while (old_lineno < old_len and
            other_lineno < other_len and
            new_lineno < new_len):

        # unchanged
        if old[old_lineno] == other[other_lineno] == new[new_lineno]:
            yield old[old_lineno]
            old_lineno += 1
            other_lineno += 1
            new_lineno += 1
            continue

        new_match = find_match(old, new, old_lineno, new_lineno)
        other_match = find_match(old, other, old_lineno, other_lineno)

        # new is changed
        if new_match != (old_lineno, new_lineno):
            new_changed_lines = new_match[0] - old_lineno

            # other is unchanged
            if match(old, other, old_lineno, other_lineno,
                     new_changed_lines) == new_changed_lines:
                for item in new[new_lineno:new_match[1]]:
                    yield item
                old_lineno = new_match[0]
                new_lineno = new_match[1]
                other_lineno += new_changed_lines

            # both changed, conflict!
            else:
                if not allow_conflicts:
                    raise DiffConflict(old_lineno, other_lineno, new_lineno)
                old_m, other_m, new_m = tripple_match(old, other, new,
                                                      other_match, new_match)
                yield left_marker
                for item in other[other_lineno:other_m]:
                    yield item
                yield middle_marker
                for item in new[new_lineno:new_m]:
                    yield item
                yield right_marker
                old_lineno = old_m
                other_lineno = other_m
                new_lineno = new_m

        # other is changed
        else:
            other_changed_lines = other_match[0] - other_lineno

            # new is unchanged
            if match(old, new, old_lineno, new_lineno,
                     other_changed_lines) == other_changed_lines:
                for item in other[other_lineno:other_match[1]]:
                    yield item
                old_lineno = other_match[0]
                other_lineno = other_match[1]
                new_lineno += other_changed_lines

            # both changed, conflict!
            else:
                if not allow_conflicts:
                    raise DiffConflict(old_lineno, other_lineno, new_lineno)

                old_m, other_m, new_m = tripple_match(old, other, new,
                                                      other_match, new_match)
                yield left_marker
                for item in other[other_lineno:other_m]:
                    yield item
                yield middle_marker
                for item in new[new_lineno:new_m]:
                    yield item
                yield right_marker
                old_lineno = old_m
                other_lineno = other_m
                new_lineno = new_m

    # all finished
    if (old_lineno == old_len and
            other_lineno == other_len and
            new_lineno == new_len):
        return

    # new added lines
    if old_lineno == old_len and other_lineno == other_len:
        for item in new[new_lineno:]:
            yield item

    # other added lines
    elif old_lineno == old_len and new_lineno == new_len:
        for item in other[other_lineno:]:
            yield item

    # conflict
    elif not (
        (new_lineno == new_len and
         (old_len - old_lineno == other_len - other_lineno) and
         match(old, other, old_lineno, other_lineno, old_len - old_lineno)
         == old_len - old_lineno) and
        (other_lineno == other_len and
         (old_len - old_lineno == new_len - new_lineno) and
         match(old, new, old_lineno, new_lineno, old_len - old_lineno)
         == old_len - old_lineno)):
        if new == other:
            for item in new[new_lineno:]:
                yield item
        else:
            if not allow_conflicts:
                raise DiffConflict(old_lineno, other_lineno, new_lineno)
            yield left_marker
            for item in other[other_lineno:]:
                yield item
            yield middle_marker
            for item in new[new_lineno:]:
                yield item
            yield right_marker


def tripple_match(old, other, new, other_match, new_match):
    """
    Find next matching pattern unchanged in both other and new return the
    position in all three lists.  Unlike `merge` this only operates on
    lists.
    """
    while True:
        difference = new_match[0] - other_match[0]

        # new changed more lines
        if difference > 0:
            match_len = match(old, other, other_match[0], other_match[1],
                              difference)
            if match_len == difference:
                return new_match[0], other_match[1] + difference, new_match[1]
            other_match = find_match(old, other,
                                     other_match[0] + match_len,
                                     other_match[1] + match_len)

        # other changed more lines
        elif difference < 0:
            difference = -difference
            match_len = match(old, new, new_match[0], new_match[1],
                              difference)
            if match_len == difference:
                return (other_match[0], other_match[1],
                        new_match[0] + difference)
            new_match = find_match(old, new,
                                   new_match[0] + match_len,
                                   new_match[1] + match_len)

        # both conflicts change same number of lines
        # or no match till the end
        else:
            return new_match[0], other_match[1], new_match[1]


def match(list1, list2, nr1, nr2, maxcount=3):
    """
    Return the number matching items after the given positions maximum
    maxcount lines are are processed.  Unlike `merge` this only operates
    on lists.
    """
    i = 0
    len1 = len(list1)
    len2 = len(list2)
    while nr1 < len1 and nr2 < len2 and list1[nr1] == list2[nr2]:
        nr1 += 1
        nr2 += 1
        i += 1
        if i >= maxcount and maxcount > 0:
            break
    return i


def find_match(list1, list2, nr1, nr2, mincount=3):
    """
    searches next matching pattern with lenght mincount
    if no pattern is found len of the both lists is returned
    """
    idx1 = nr1
    idx2 = nr2
    len1 = len(list1)
    len2 = len(list2)
    hit1 = hit2 = None

    while idx1 < len1 or idx2 < len2:
        i = nr1
        while i <= idx1:
            hit_count = match(list1, list2, i, idx2, mincount)
            if hit_count >= mincount:
                hit1 = (i, idx2)
                break
            i += 1

        i = nr2
        while i < idx2:
            hit_count = match(list1, list2, idx1, i, mincount)
            if hit_count >= mincount:
                hit2 = (idx1, i)
                break
            i += 1

        if hit1 or hit2:
            break
        if idx1 < len1:
            idx1 += 1
        if idx2 < len2:
            idx2 += 1

    if hit1 and hit2:
        return hit1
    elif hit1:
        return hit1
    elif hit2:
        return hit2
    return len1, len2


def get_close_matches(name, matches, n=10, cutoff=0.6):
    """
    This is a replacement for a function in the difflib with the same name.
    The difference between the two implementations is that this one is case
    insensitive and optimized for page names.
    """
    s = difflib.SequenceMatcher()
    s.set_seq2(name.lower())
    result = []
    for name in matches:
        s.set_seq1(name.lower())
        if s.real_quick_ratio() >= cutoff and \
           s.quick_ratio() >= cutoff and \
           s.ratio() >= cutoff:
            result.append((s.ratio(), name))
    return heapq.nlargest(n, result)


def generate_udiff(old, new, old_title='', new_title='',
                   context_lines=4):
    """
    Generate an udiff out of two texts.  If titles are given they will be
    used on the diff.  `context_lines` defaults to 5 and represents the
    number of lines used in an udiff around a changed line.
    """
    udiff = difflib.unified_diff(
        old.splitlines(),
        new.splitlines(),
        fromfile=old_title,
        tofile=new_title,
        lineterm='',
        n=context_lines)
    try:
        title_diff_1 = next(udiff)
        title_diff_2 = next(udiff)
        return '\n'.join(itertools.chain([title_diff_1, title_diff_2], udiff))
    except StopIteration:
        # Content did't cange
        return ''


def prepare_udiff(udiff):
    """
    Prepare an udiff for the template.  The `Diff` model uses this to render
    an udiff into a HTML table.
    """
    return DiffRenderer(udiff).prepare()


def process_line(line, start, end):
    last = end + len(line['line'])
    if line['action'] == 'add':
        tag = 'ins'
    else:
        tag = 'del'
    line['line'] = '%s<%s>%s</%s>%s' % (
        line['line'][:start],
        tag,
        line['line'][start:last],
        tag,
        line['line'][last:])


class DiffRenderer(object):
    """
    Give it a unified diff and it returns a list of the files that were
    mentioned in the diff together with a dict of meta information that
    can be used to render it in a HTML template.
    """
    _chunk_re = re.compile(r'@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@')

    def __init__(self, udiff):
        """
        :param udiff:   a text in udiff format
        """
        self.lines = [escape(line) for line in udiff.splitlines()]

    def _extract_rev(self, line1, line2):
        """Extract the filename and revision hint from a line."""
        try:
            if line1.startswith('--- ') and line2.startswith('+++ '):
                filename = line1[4:].split(None, 1)[0]
                return filename, _('Old'), _('New')
        except (ValueError, IndexError):
            pass
        return None, None, None

    def _highlight_line(self, line, next):
        """Highlight inline changes in both lines."""
        start = 0
        limit = min(len(line['line']), len(next['line']))
        while start < limit and line['line'][start] == next['line'][start]:
            start += 1
        end = -1
        limit -= start
        while -end <= limit and line['line'][end] == next['line'][end]:
            end -= 1
        end += 1
        if start or end:
            process_line(line, start, end)
            process_line(next, start, end)

    def _parse_udiff(self):
        """Parse the diff an return data for the template."""
        lineiter = iter(self.lines)
        files = []
        try:
            line = next(lineiter)
            while True:
                # continue until we found the old file
                if not line.startswith('--- '):
                    line = next(lineiter)
                    continue

                chunks = []
                filename, old_rev, new_rev = \
                    self._extract_rev(line, next(lineiter))
                files.append({
                    'filename': filename,
                    'old_revision': old_rev,
                    'new_revision': new_rev,
                    'chunks': chunks,
                })

                line = next(lineiter)
                while line:
                    match = self._chunk_re.match(line)
                    if not match:
                        break

                    lines = []
                    chunks.append(lines)

                    old_line, old_end, new_line, new_end = \
                        [int(x or 1) for x in match.groups()]
                    old_line -= 1
                    new_line -= 1
                    old_end += old_line
                    new_end += new_line
                    line = next(lineiter)

                    while old_line < old_end or new_line < new_end:
                        if line:
                            command, line = line[0], line[1:]
                        else:
                            command = ' '
                        affects_old = affects_new = False

                        if command == ' ':
                            affects_old = affects_new = True
                            action = 'unmod'
                        elif command == '+':
                            affects_new = True
                            action = 'add'
                        elif command == '-':
                            affects_old = True
                            action = 'del'
                        else:
                            raise RuntimeError()

                        old_line += affects_old
                        new_line += affects_new
                        lines.append({
                            'old_lineno': affects_old and old_line or '',
                            'new_lineno': affects_new and new_line or '',
                            'action': action,
                            'line': line,
                        })
                        line = next(lineiter)

        except StopIteration:
            pass

        # highlight inline changes
        for file in files:
            for chunk in chunks:
                lineiter = iter(chunk)
                try:
                    while True:
                        line = next(lineiter)
                        if line['action'] != 'unmod':
                            nextline = next(lineiter)
                            if nextline['action'] == 'unmod' or \
                               nextline['action'] == line['action']:
                                continue
                            self._highlight_line(line, nextline)
                except StopIteration:
                    pass

        return files

    def prepare(self):
        """Prepare the passed udiff for HTML rendering."""
        return self._parse_udiff()
