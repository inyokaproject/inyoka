# -*- coding: utf-8 -*-
"""
    inyoka.utils.special_day
    ~~~~~~~~~~~~~~~~~~~~~~~~

    Currently supports fixed-day-events, advent and easter.

    :copyright: (c) 2007-2022 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from datetime import date, timedelta
from typing import Dict, List, Optional


def easter_sunday(year: int) -> date:
    """
    Get the date of easter sunday.
    Uses the gauss algorithm with additions
    german source: https://de.wikipedia.org/wiki/Gau%C3%9Fsche_Osterformel#Eine_erg.C3.A4nzte_Osterformel
    """

    k = year // 100
    m = 15 + (3*k+3)//4 - (8*k+13)//25
    s = 2 - (3*k+3)//4
    a = year % 19
    d = (19*a+m) % 30
    r = (d+a//11) // 29
    og = 21 + d - r
    sz = 7 - (year+year//4+s) % 7
    oe = 7 - (og-sz) % 7
    os = og + oe

    day = os
    month = 3

    if day > 31:
        day %= 31
        month += 1

    return date(year, month, day)


def fourth_advent(year: int) -> date:
    fourth_advent = date(year, 12, 24)
    fourth_weekday = date.weekday(fourth_advent)

    if fourth_weekday != 6:
        fourth_advent -= timedelta(fourth_weekday+1)

    return fourth_advent


def advent_week(n_th: int, year: int) -> List[date]:
    """
        Returns a list of date-objects that represent the given advent-week.
        The "week" of the 4th advent ends with the 26th december.
    """
    if n_th < 1 or n_th > 4:
        raise ValueError('Only 1st to (inclusive) 4th advent exists.')

    fourth = fourth_advent(year)
    if n_th == 4:
        delta = date(year, 12, 26) - fourth
        return [fourth + timedelta(days=d) for d in range(0, delta.days+1)]
    else:
        n_th_offset = 7*(4-n_th)
        return [fourth + timedelta(days=d-n_th_offset) for d in range(0, 7)]


def collect_styles(year: int) -> Dict[date, str]:
    """
        Creates a dict with scheme {date1: 'stylesheet.css', …}
        → easier for check_special_day() to determine today's style
    """
    special_styles = dict()

    easter_sunday_current = easter_sunday(year)
    easter_monday = easter_sunday_current + timedelta(days=1)
    for i in (easter_sunday_current, easter_monday):
        special_styles[i] = 'easter.css'

    for i in (date(year, 12, 31), date(year, 1, 1)):
        special_styles[i] = 'silvester.css'

    for w in range(1, 5):
        for d in advent_week(w, year):
            special_styles[d] = 'advent_{}.css'.format(w)

    return special_styles


def check_special_day() -> Optional[str]:
    """
        Checks whether today is a special day.
        If true, the function returns the name of the css-file to use.
        Otherwise returns None.
    """
    today = date.today()

    return collect_styles(today.year).get(today)
