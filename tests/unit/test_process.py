import sys
import unittest

import os

sys.path.insert(1,
                os.path.abspath(
                    os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                 os.path.join('..', '..'))))

from pake import process

script_dir = os.path.dirname(os.path.realpath(__file__))


class ProcessTest(unittest.TestCase):

    def test_call(self):
        cmd = [sys.executable, os.path.join(script_dir, 'timeout.py')]

        with self.assertRaises(process.TimeoutExpired) as exc:
            process.call(*cmd, timeout=0.1, stderr=process.DEVNULL, stdout=process.DEVNULL)

        self.assertSequenceEqual((cmd, 0.1), exc.exception.cmd)

        self.assertNotEqual(process.call(sys.executable, os.path.join(script_dir, 'throw.py'),
                                         stderr=process.DEVNULL, stdout=process.DEVNULL), 0)

    def test_check_call(self):

        cmd = [sys.executable, os.path.join(script_dir, 'timeout.py')]

        with self.assertRaises(process.TimeoutExpired) as exc:
            process.check_call(cmd, timeout=0.1,
                               stderr=process.DEVNULL, stdout=process.DEVNULL)

        self.assertSequenceEqual((cmd, 0.1), exc.exception.cmd)

        _ = str(exc.exception)  # just test for serialization exceptions

        cmd = [sys.executable, os.path.join(script_dir, 'throw.py')]

        with self.assertRaises(process.CalledProcessException) as exc:
            process.check_call(cmd, stderr=process.DEVNULL, stdout=process.DEVNULL)

        self.assertListEqual(cmd, exc.exception.cmd)

        _ = str(exc.exception)  # just test for serialization exceptions

    def test_check_output(self):
        cmd = [sys.executable, os.path.join(script_dir, 'timeout.py')]

        with self.assertRaises(process.TimeoutExpired) as exc:
            process.check_output(*cmd, timeout=0.1, stderr=process.DEVNULL)

        _ = str(exc.exception)  # just test for serialization exceptions

        cmd = [sys.executable, os.path.join(script_dir, 'throw.py')]

        with self.assertRaises(process.CalledProcessException) as exc:
            process.check_output(cmd, stderr=process.DEVNULL)

        _ = str(exc.exception)  # just test for serialization exceptions

