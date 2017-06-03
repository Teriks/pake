import sys
import unittest

import os

sys.path.insert(1,
                os.path.abspath(
                    os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                 os.path.join('..', '..'))))

import pake.util


class UtilTest(unittest.TestCase):

    def test_flatten_non_str(self):

        val = list(pake.util.flatten_non_str(['this', ['is', ('an', ), 'example']]))
        self.assertListEqual(val, ['this', 'is', 'an', 'example'])

        val = list(pake.util.flatten_non_str(['this', {'is', ('an', ), 'example'}]))
        self.assertCountEqual(val, {'this', 'is', 'an', 'example'})

    def test_handle_shell_args(self):

        def tester_func(*args):
            return pake.util.handle_shell_args(args)

        val = tester_func(['this', ['is', ('an', ), 'example']])
        self.assertListEqual(val, ['this', 'is', 'an', 'example'])

        val = tester_func('this', ['is', ('an', ), 'example'])
        self.assertListEqual(val, ['this', 'is', 'an', 'example'])

        val = tester_func('this', 'is', 'an', 'example')
        self.assertListEqual(val, ['this', 'is', 'an', 'example'])

        val = tester_func('this')
        self.assertListEqual(val, ['this'])

        val = tester_func()
        self.assertListEqual(val, [])

    def test_str_is_int(self):

        self.assertTrue(pake.util.str_is_int('10'))

        self.assertFalse(pake.util.str_is_int('10.0'))

        self.assertFalse(pake.util.str_is_int('.0'))

        self.assertFalse(pake.util.str_is_int(''))

        self.assertFalse(pake.util.str_is_int('test'))

    def test_is_iterable(self):

        self.assertTrue(pake.util.is_iterable('test'))

        self.assertTrue(pake.util.is_iterable(b'test'))

        self.assertTrue(pake.util.is_iterable(r'test'))

        self.assertTrue(pake.util.is_iterable([]))

        self.assertTrue(pake.util.is_iterable({}))

        self.assertTrue(pake.util.is_iterable({'test': 1}))

        #

        self.assertFalse(pake.util.is_iterable(None))

    def test_is_iterable_not_str(self):

        self.assertTrue(pake.util.is_iterable_not_str(['test']))

        self.assertTrue(pake.util.is_iterable_not_str({'test'}))

        self.assertTrue(pake.util.is_iterable_not_str({'test': 10}))

        self.assertTrue(pake.util.is_iterable_not_str(('test', )))

        self.assertTrue(pake.util.is_iterable_not_str(b'test'))

        self.assertTrue(pake.util.is_iterable_not_str(b''))

        #

        self.assertFalse(pake.util.is_iterable_not_str('test'))

        self.assertFalse(pake.util.is_iterable_not_str(''))

        self.assertFalse(pake.util.is_iterable_not_str(r'test'))

        self.assertFalse(pake.util.is_iterable_not_str(r''))

        self.assertFalse(pake.util.is_iterable_not_str(None))