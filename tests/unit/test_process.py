import sys
import unittest

import os

script_dir = os.path.dirname(os.path.realpath(__file__))

sys.path.insert(1, os.path.abspath(
    os.path.join(script_dir, os.path.join('..', '..'))))

from pake import process
import pake.program
import pake


class ProcessTest(unittest.TestCase):
    def test_call(self):
        cmd = [sys.executable, os.path.join(script_dir, 'timeout.py')]

        with self.assertRaises(process.TimeoutExpired) as exc:
            process.call(*cmd, timeout=0.1, stderr=process.DEVNULL, stdout=process.DEVNULL)

        self.assertSequenceEqual((cmd, 0.1), exc.exception.cmd)

        self.assertNotEqual(process.call(sys.executable, os.path.join(script_dir, 'throw.py'),
                                         stderr=process.DEVNULL, stdout=process.DEVNULL), 0)

        self.assertNotEqual(process.call(sys.executable, os.path.join(script_dir, 'killself.py'),
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

        # Check pake propagates the exception correctly

        pake.shutdown(clear_conf=False)

        pk = pake.init()

        @pk.task
        def dummy(ctx):
            process.check_call(cmd, stderr=process.DEVNULL, stdout=process.DEVNULL)

        with self.assertRaises(pake.TaskException) as exc:
            pk.run(tasks=dummy)

        self.assertEqual(type(exc.exception.exception), process.CalledProcessException)

    def test_check_output(self):

        cmd = [sys.executable, os.path.join(script_dir, 'timeout.py')]

        with self.assertRaises(process.TimeoutExpired) as exc:
            process.check_output(*cmd, timeout=0.1, stderr=process.DEVNULL)

        _ = str(exc.exception)  # just test for serialization exceptions

        cmd = [sys.executable, os.path.join(script_dir, 'throw.py')]

        with self.assertRaises(process.CalledProcessException) as exc:
            process.check_output(cmd, stderr=process.DEVNULL)

        _ = str(exc.exception)  # just test for serialization exceptions

        # Check pake propagates the exception correctly

        pake.shutdown(clear_conf=False)

        pk = pake.init()

        @pk.task
        def dummy(ctx):
            process.check_output(cmd, stderr=process.DEVNULL)

        with self.assertRaises(pake.TaskException) as exc:
            pk.run(tasks=dummy)

        self.assertEqual(type(exc.exception.exception), process.CalledProcessException)
