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
        val = list(pake.util.flatten_non_str(['this', ['is', ('an',), 'example']]))
        self.assertListEqual(val, ['this', 'is', 'an', 'example'])

        val = list(pake.util.flatten_non_str(['this', {'is', ('an',), 'example'}]))
        self.assertCountEqual(val, {'this', 'is', 'an', 'example'})

    def test_handle_shell_args(self):
        def tester_func(*args):
            return pake.util.handle_shell_args(args)

        class StringableArgument:
            def __init__(self, data):
                self.data = data

            def __str__(self):
                return self.data

        val = tester_func(StringableArgument('this'),
                          StringableArgument('is'),
                          StringableArgument('an'),
                          StringableArgument('example'))

        self.assertListEqual(val, ['this', 'is', 'an', 'example'])

        val = tester_func(StringableArgument('this is an example'))
        # Stringable arguments are always interpreted as a single argument word
        self.assertListEqual(val, ['this is an example'])

        val = tester_func('this is an example')
        self.assertListEqual(val, ['this', 'is', 'an', 'example'])

        val = tester_func(['this', ['is', ('an',), 'example']])
        self.assertListEqual(val, ['this', 'is', 'an', 'example'])

        val = tester_func('this', ['is', ('an',), 'example'])
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

    def test_str_is_float(self):
        self.assertTrue(pake.util.str_is_float('10'))

        self.assertTrue(pake.util.str_is_float('10.0'))

        self.assertTrue(pake.util.str_is_float('.0'))

        self.assertTrue(pake.util.str_is_float('0.0'))

        self.assertTrue(pake.util.str_is_float('0.'))

        self.assertFalse(pake.util.str_is_float(''))

        self.assertFalse(pake.util.str_is_float('test'))

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

        self.assertTrue(pake.util.is_iterable_not_str(('test',)))

        self.assertTrue(pake.util.is_iterable_not_str(b'test'))

        self.assertTrue(pake.util.is_iterable_not_str(b''))

        #

        self.assertFalse(pake.util.is_iterable_not_str('test'))

        self.assertFalse(pake.util.is_iterable_not_str(''))

        self.assertFalse(pake.util.is_iterable_not_str(r'test'))

        self.assertFalse(pake.util.is_iterable_not_str(r''))

        self.assertFalse(pake.util.is_iterable_not_str(None))

    def test_parse_define_value(self):
        self.assertEqual(pake.util.parse_define_value('true'), True)
        self.assertEqual(pake.util.parse_define_value('True'), True)
        self.assertEqual(pake.util.parse_define_value('tRue'), True)

        self.assertEqual(pake.util.parse_define_value('false'), False)
        self.assertEqual(pake.util.parse_define_value('False'), False)
        self.assertEqual(pake.util.parse_define_value('faLse'), False)

        self.assertEqual(pake.util.parse_define_value('1'), 1)
        self.assertEqual(type(pake.util.parse_define_value('1')), int)

        self.assertEqual(pake.util.parse_define_value('1.0'), 1.0)
        self.assertEqual(type(pake.util.parse_define_value('.5')), float)

        self.assertListEqual(
            pake.util.parse_define_value('["hello", \'world\', "!", \'!\', 1, 1.5]'),
            ['hello', 'world', '!', '!', 1, 1.5])

        self.assertCountEqual(
            pake.util.parse_define_value('{"hello", \'world\', "!", \'!\', 1, 1.5}'),
            ['hello', 'world', '!', 1, 1.5])

        self.assertEqual(pake.util.parse_define_value('I am a string, I have no quotes'),
                         'I am a string, I have no quotes')

        self.assertEqual(pake.util.parse_define_value('\"I am a string, I have quotes\"'),
                         'I am a string, I have quotes')

        self.assertEqual(pake.util.parse_define_value("\'I am a string, I have quotes\'"),
                         'I am a string, I have quotes')

        self.assertEqual(pake.util.parse_define_value('("Tuples are cool",)'), ('Tuples are cool',))

        self.assertEqual(pake.util.parse_define_value('("Tuples are cool", \'yup\')'), ('Tuples are cool', 'yup'))

        with self.assertRaises(SyntaxError):
            pake.util.parse_define_value(' { Im not a full literal ')

        with self.assertRaises(SyntaxError):
            pake.util.parse_define_value(' " Im not a full literal ')

        with self.assertRaises(SyntaxError):
            pake.util.parse_define_value(' { "test": : "broken dict" } ')

        with self.assertRaises(SyntaxError):
            pake.util.parse_define_value(' [ "bad"  list" ] ')

        with self.assertRaises(SyntaxError):
            pake.util.parse_define_value('  "bad"  string"  ')

        with self.assertRaises(SyntaxError):
            pake.util.parse_define_value("  'bad'  string'  ")
