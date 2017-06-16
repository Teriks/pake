import sys
import unittest

import os

script_dir = os.path.dirname(os.path.realpath(__file__))

sys.path.insert(1, os.path.abspath(
    os.path.join(script_dir, os.path.join('..', '..'))))

from pake import process
import pake
import tempfile
import pake.returncodes


class TestStdinDefines(unittest.TestCase):

    def test_stdin_defines(self):

        # Test that the --stdin-defines feature is working, and can handle being fed bad values

        good_value = {
            'DEFINE_VALUE_TRUE': True,
            'DEFINE_VALUE_FALSE': False,
            'DEFINE_VALUE_STRING': 'string',
            'DEFINE_VALUE_LIST': ['list', 42],
            'DEFINE_VALUE_DICT': {'dict': 42},
            'DEFINE_VALUE_TUP': ('tuple', 42),
            'DEFINE_VALUE_SET': {'set', 42}
        }

        assert_script = os.path.join(script_dir, 'assert_stdin_define_values.py')

        # Temp file is the quickest way to do this

        with tempfile.TemporaryFile(mode='w+', newline='\n') as temp:

            temp.write(str(good_value))
            temp.flush()
            temp.seek(0)

            # If this raises a pake.process.CalledProcessException, test failed
            process.check_call(sys.executable, assert_script, '--stdin-define',
                               stdin=temp)

            # ==========================

            # Feed it python dictionary syntax errors

            temp.seek(0)
            temp.write("{'This dictionary is bad':}")
            temp.flush()
            temp.seek(0)

            return_code = process.call(sys.executable, assert_script, '--stdin-define',
                                       stdin=temp, stderr=process.DEVNULL, stdout=process.DEVNULL)

            # Check pake handled the syntax error in the defines dictionary correctly
            self.assertEqual(return_code, pake.returncodes.STDIN_DEFINES_SYNTAX_ERROR)

            # ==========================

            # Feed it garbage

            temp.seek(0)
            temp.write("IM THE TRASHMAN. I EAT GARBAGE.")
            temp.flush()
            temp.seek(0)

            return_code = process.call(sys.executable, assert_script, '--stdin-define',
                                       stdin=temp, stderr=process.DEVNULL, stdout=process.DEVNULL)

            # Check pake handled the syntax error in the defines dictionary correctly
            self.assertEqual(return_code, pake.returncodes.STDIN_DEFINES_SYNTAX_ERROR)

            # ==========================

            # Test that override on the command line is working by trying to override
            # a value that the assert_stdin_define_values.py script expects

            temp.seek(0)
            temp.write(str(good_value))
            temp.flush()
            temp.seek(0)

            with self.assertRaises(pake.process.CalledProcessException):
                # This should raise pake.process.CalledProcessException,
                # because the helper script is not expecting DEFINE_VALUE_TRUE=False

                process.check_call(sys.executable, assert_script,
                                   '--stdin-define', '-D', 'DEFINE_VALUE_TRUE=False',
                                   stdin=temp, stderr=process.DEVNULL, stdout=process.DEVNULL)



