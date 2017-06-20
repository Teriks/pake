import sys
import unittest

import os

script_dir = os.path.dirname(os.path.realpath(__file__))

sys.path.insert(1, os.path.abspath(
    os.path.join(script_dir, os.path.join('..', '..'))))

import pake
import pake.program
import pake.conf
import pake.arguments

from tests import open_devnull

pake.conf.stdout = open_devnull()
pake.conf.stderr = open_devnull()


class TaskContextProcessTest(unittest.TestCase):

    def _call_test(self, jobs):
        exit_10 = os.path.join(script_dir, 'exit_10.py')
        exit_0 = os.path.join(script_dir, 'exit_0.py')

        pake.de_init(clear_conf=False)

        pk = pake.init(args=['--jobs', str(jobs)])

        # Just so this path gets hit at least once
        pk.sync_output = False

        class TestFailException:
            def __init__(self, expected, code):
                self.code = code
                self.expected = expected

        @pk.task
        def test_10(ctx):
            return_code = ctx.call(sys.executable, exit_10,
                                   ignore_errors=True,
                                   silent=True)
            if return_code != 10:
                raise TestFailException(10, return_code)

            return_code = ctx.call(sys.executable, exit_10,
                                   ignore_errors=True,
                                   silent=True,
                                   collect_output=True)
            if return_code != 10:
                raise TestFailException(10, return_code)

        @pk.task
        def test_0(ctx):
            return_code = ctx.call(sys.executable, exit_0)
            if return_code != 0:
                raise TestFailException(0, return_code)

            return_code = ctx.call(sys.executable, exit_0,
                                   collect_output=True)
            if return_code != 0:
                raise TestFailException(0, return_code)

        try:
            pk.run(tasks=test_10)
        except pake.TaskException as err:

            if isinstance(err.exception, TestFailException):
                self.fail('pake.TaskContext.call exit_10.py failed to return '
                          'correct return code.'
                          'expected {}, got: {}'.
                          format(err.exception.expected, err.exception.code))
            else:
                raise err.exception

        try:
            pk.run(tasks=test_0)
        except pake.TaskException as err:

            if isinstance(err.exception, TestFailException):
                self.fail('pake.TaskContext.call exit_0.py failed to return '
                          'correct return code.'
                          'expected {}, got: {}'.
                          format(err.exception.expected, err.exception.code))
            else:
                raise err.exception

    def test_call(self):
        self._call_test(1)
        self._call_test(5)

