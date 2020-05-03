# -*- coding: utf-8 -*-
"""
    tests.utils.test_special_day
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: (c) 2007-2020 by the Inyoka Team, see AUTHORS for more details.
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


class GeneralTestCase(unittest.TestCase):
    def __init__(self, methodName, *args):
        super(GeneralTestCase, self).__init__(methodName)

        self.params = args

    def runTest(self):
        pass    # test function goes here


class GeneralEqualTestCase(GeneralTestCase):
    def runTest(self):
        self.assertEqual(self.params[0], self.params[1])


def add_easter_tests(suite):
    easter_dates = [date(1901, 4, 7), date(1943, 4, 25), date(2000, 4, 23),
                    date(2001, 4, 15), date(2002, 3, 31), date(2008, 3, 23),
                    date(2015, 4, 5), date(2018, 4, 1), date(2026, 4, 5),
                    date(2030, 4, 21), date(2069, 4, 14)]

    for d in easter_dates:
        suite.addTest(GeneralEqualTestCase('runTest', d, easter_sunday(d.year)))


def add_advent_tests(suite):
    first_advent_dates = [date(2014, 11, 30), date(2015, 11, 29), date(2016, 11, 27),
                          date(2017, 12, 3), date(2018, 12, 2), date(2019, 12, 1),
                          date(2020, 11, 29), date(2021, 11, 28)]

    fourth_advent_dates = [d + timedelta(3 * 7) for d in first_advent_dates]

    for d in fourth_advent_dates:
        suite.addTest(GeneralEqualTestCase('runTest', d, fourth_advent(d.year)))


class CheckSpecialDay(unittest.TestCase):
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


def load_tests(loader, tests, pattern):
    '''
        Workaround for parameterized tests in python2
        see http://stackoverflow.com/questions/32899/how-to-generate-dynamic-parametrized-unit-tests-in-python/23508426#23508426
    '''
    suite = unittest.TestSuite()

    tests = loader.loadTestsFromTestCase(CheckSpecialDay)
    suite.addTests(tests)

    add_easter_tests(suite)
    add_advent_tests(suite)

    return suite
