import inspect
import sys
import unittest

import os

script_dir = os.path.dirname(os.path.realpath(__file__))

sys.path.insert(1, os.path.abspath(
    os.path.join(script_dir, os.path.join('..', '..'))))

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

        self.assertEqual(pake.util.parse_define_value('None'), None)
        self.assertEqual(pake.util.parse_define_value('none'), None)
        self.assertEqual(pake.util.parse_define_value('noNe'), None)

        self.assertEqual(pake.util.parse_define_value(' true'), True)
        self.assertEqual(pake.util.parse_define_value(' True'), True)
        self.assertEqual(pake.util.parse_define_value(' tRue'), True)

        self.assertEqual(pake.util.parse_define_value(' false'), False)
        self.assertEqual(pake.util.parse_define_value(' False'), False)
        self.assertEqual(pake.util.parse_define_value(' faLse'), False)

        self.assertEqual(pake.util.parse_define_value(' None'), None)
        self.assertEqual(pake.util.parse_define_value(' none'), None)
        self.assertEqual(pake.util.parse_define_value(' noNe'), None)

        self.assertEqual(pake.util.parse_define_value(' true '), True)
        self.assertEqual(pake.util.parse_define_value(' True '), True)
        self.assertEqual(pake.util.parse_define_value(' tRue '), True)

        self.assertEqual(pake.util.parse_define_value(' false '), False)
        self.assertEqual(pake.util.parse_define_value(' False '), False)
        self.assertEqual(pake.util.parse_define_value(' faLse '), False)

        self.assertEqual(pake.util.parse_define_value(' None '), None)
        self.assertEqual(pake.util.parse_define_value(' none '), None)
        self.assertEqual(pake.util.parse_define_value(' noNe '), None)

        self.assertEqual(pake.util.parse_define_value('1 2 3 '), '1 2 3 ')

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

        self.assertEqual(pake.util.parse_define_value(''), '')

        with self.assertRaises(ValueError):
            pake.util.parse_define_value(None)

        with self.assertRaises(ValueError):
            pake.util.parse_define_value(' { Im not a full literal ')

        with self.assertRaises(ValueError):
            pake.util.parse_define_value(' " Im not a full literal ')

        with self.assertRaises(ValueError):
            pake.util.parse_define_value(' { "test": : "broken dict" } ')

        with self.assertRaises(ValueError):
            pake.util.parse_define_value(' [ "bad"  list" ] ')

        with self.assertRaises(ValueError):
            pake.util.parse_define_value('  "bad"  string"  ')

        with self.assertRaises(ValueError):
            pake.util.parse_define_value("  'bad'  string'  ")

    def test_get_pakefile_caller_detail(self):

        def get_line():
            return inspect.getframeinfo(inspect.stack()[1][0]).lineno

        pake.de_init()

        pake.init()  # This file is the init file now

        caller_detail, line = pake.util.get_pakefile_caller_detail(), get_line()

        self.assertEqual(caller_detail.line_number, line)

        # This is the init file

        self.assertEqual(caller_detail.filename, os.path.join(script_dir, __file__))

        # Because get_pakefile_caller_detail is the first pake module function
        # in the stack that was called inside the init file, which is this file

        self.assertEqual(caller_detail.function_name, 'get_pakefile_caller_detail')

        # ====

        # Test without init

        pake.de_init()

        caller_detail = pake.util.get_pakefile_caller_detail()

        # Cant figure it out without knowing the init file

        self.assertEqual(caller_detail, None)


