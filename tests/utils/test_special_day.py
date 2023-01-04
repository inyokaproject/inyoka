"""
    tests.utils.test_special_day
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: (c) 2007-2023 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

import unittest
from datetime import date, timedelta

from freezegun import freeze_time

from inyoka.utils.special_day import (
    check_special_day,
    easter_sunday,
    fourth_advent,
)


class TestInternalDateFunctions(unittest.TestCase):
    def test_easter_dates(self):
        """
        Tests the return value of easter_sunday()
        """
        easter_dates = [date(1901, 4, 7), date(1943, 4, 25), date(2000, 4, 23),
                        date(2001, 4, 15), date(2002, 3, 31), date(2008, 3, 23),
                        date(2015, 4, 5), date(2018, 4, 1), date(2026, 4, 5),
                        date(2030, 4, 21), date(2069, 4, 14)]

        for d in easter_dates:
            with self.subTest(date=d):
                self.assertEqual(d, easter_sunday(d.year))

    def test_advent_dates(self):
        """
        Tests the return value of fourth_advent()
        """
        first_advent_dates = [date(2014, 11, 30), date(2015, 11, 29), date(2016, 11, 27),
                              date(2017, 12, 3), date(2018, 12, 2), date(2019, 12, 1),
                              date(2020, 11, 29), date(2021, 11, 28)]

        fourth_advent_dates = [d + timedelta(3 * 7) for d in first_advent_dates]

        for d in fourth_advent_dates:
            with self.subTest(date=d):
                self.assertEqual(d, fourth_advent(d.year))


class TestCheckSpecialDay(unittest.TestCase):
    """
    Tests that check_special_day() returns the intended CSS-file (or none)
    """
    @freeze_time("2015-1-1")
    def test_newyear(self):
        self.assertEqual(check_special_day(), 'silvester.css')

    @freeze_time("2015-11-28")
    def test_before_first_advent(self):
        self.assertEqual(check_special_day(), None)

    @freeze_time("2015-11-29")
    def test__first_advent(self):
        self.assertEqual(check_special_day(), 'advent_1.css')

    @freeze_time("2015-12-6")
    def test_second_advent(self):
        self.assertEqual(check_special_day(), 'advent_2.css')

    @freeze_time("2015-12-8")
    def test_while_second_advent(self):
        self.assertEqual(check_special_day(), 'advent_2.css')

    @freeze_time("2015-12-13")
    def test_third_advent(self):
        self.assertEqual(check_special_day(), 'advent_3.css')

    @freeze_time("2015-12-20")
    def test_fourth_advent(self):
        self.assertEqual(check_special_day(), 'advent_4.css')

    @freeze_time("2015-12-26")
    def test_fourth_after_xmas_advent(self):
        self.assertEqual(check_special_day(), 'advent_4.css')

    @freeze_time("2015-12-27")
    def test_after_xmas(self):
        self.assertEqual(check_special_day(), None)

    @freeze_time("2015-12-31")
    def test_silvester(self):
        self.assertEqual(check_special_day(), 'silvester.css')

    @freeze_time("2021-04-04")
    def test_easter_sunday(self):
        self.assertEqual(check_special_day(), 'easter.css')

    @freeze_time("2021-04-05")
    def test_easter_monday(self):
        self.assertEqual(check_special_day(), 'easter.css')
