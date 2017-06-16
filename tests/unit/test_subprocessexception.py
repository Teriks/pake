import sys
import unittest

import os

import pake.pake

script_dir = os.path.dirname(os.path.realpath(__file__))

sys.path.insert(1, os.path.abspath(
    os.path.join(script_dir, os.path.join('..', '..'))))

import pake


class SubprocessExceptionTest(unittest.TestCase):
    def test_subprocess_exception(self):
        with self.assertRaises(ValueError):
            # Because output is not a bytes object
            _ = pake.TaskSubprocessException(
                cmd=['test'],
                returncode=1,
                output='I should be bytes')

        with self.assertRaises(ValueError):
            # Because cmd is empty
            _ = pake.TaskSubprocessException(
                cmd=(),
                returncode=1)

        with self.assertRaises(ValueError):
            # Because cmd is None
            _ = pake.TaskSubprocessException(
                cmd=None,
                returncode=1)

        with self.assertRaises(ValueError):
            # Because output and output_stream
            # cannot be used together
            _ = pake.TaskSubprocessException(
                cmd=None,
                returncode=1,
                output=b'test',
                output_stream=sys.stdin)

        class DummyFile:
            def write(self, *args):
                pass

        # Just make sure write_info does not raise anything
        # when the output parameter is in use.

        ex = pake.TaskSubprocessException(cmd=['test'],
                                          returncode=1,
                                          output=b'test')

        ex.write_info(DummyFile())

        ex = pake.TaskSubprocessException(cmd=['test'],
                                          returncode=1,
                                          output=b'test',
                                          message='test')
        ex.write_info(DummyFile())
