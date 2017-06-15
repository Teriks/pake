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
pake.conf.stdout = open_devnull() if pake.conf.stdout is sys.stdout else pake.conf.stdout
pake.conf.stderr = open_devnull() if pake.conf.stderr is sys.stderr else pake.conf.stderr


class TaskContextProcessTest(unittest.TestSuite):

    def test_call(self):

        exit_10 = os.path.join(script_dir, 'exit_10.py')

        pk = pake.init()

        class TestFailException:
            def __init__(self, code):
                self.code = code

        @pk.task
        def test_task(ctx):
            return_code = ctx.call(sys.executable, exit_10,
                                   ignore_errors=True,
                                   silent=True)
            if return_code != 10:
                raise TestFailException(return_code)

        try:
            pk.run(tasks=test_task)
        except pake.TaskException as err:

            if isinstance(err.exception, TestFailException):
                self.fail('pake.TaskContext.call failed to return correct return code.'
                          'expected 10, got: {}'.format(err.exception.code))
            else:
                raise err.exception
