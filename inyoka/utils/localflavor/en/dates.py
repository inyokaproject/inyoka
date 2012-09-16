# -*- coding: utf-8 -*-
"""
    inyoka.utils.localflavor.en.dates
    ~~~~~~~~~~~~~~~~~~

    Various language specific utilities for datetime handling.

    :copyright: (c) 2007-2012 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""

from datetime import date
from django.utils.translation import ugettext as _
from django.template import defaultfilters

def naturalday_in_running_text(value, arg=None):
    """
    Format date according to german and english grammar. This function
    returns the date combined with the adverb `on`, if the return value
    is given in numeric date format. On the other hand it behaves like
    django.contrib.humanize.templatetags.naturalday.
    Examples: `on 27.4.12` or `tomorrow`.
    """
    try:
        value = date(value.year, value.month, value.day)
    except AttributeError:
        # Passed value wasn't a date object
        return value
    except ValueError:
        # Date arguments out of range
        return value
    delta = value - date.today()
    if delta.days == 0:
        return _(u'today')
    elif delta.days == 1:
        return _(u'tomorrow')
    elif delta.days == -1:
        return _(u'yesterday')
    return ' '.join([_(u'on'), defaultfilters.date(value, arg)])
