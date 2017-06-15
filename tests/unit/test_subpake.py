import sys
import unittest

import os

script_dir = os.path.dirname(os.path.realpath(__file__))

sys.path.insert(1, os.path.abspath(
                   os.path.join(script_dir, os.path.join('..', '..'))))

import pake
import pake.program


from tests import open_devnull
pake.conf.stdout = open_devnull() if pake.conf.stdout is sys.stdout else pake.conf.stdout
pake.conf.stderr = open_devnull() if pake.conf.stderr is sys.stderr else pake.conf.stderr


class SubpakeTest(unittest.TestCase):

    def test_subpake(self):

        pake.program.shutdown()

        with self.assertRaises(SystemExit) as err:
            pake.subpake(os.path.join(script_dir, 'throw.py'))

        with self.assertRaises(pake.SubpakeException) as err:
            pake.subpake(os.path.join(script_dir, 'throw.py'), exit_on_error=False)

        # If pake is not initialized, there is no depth tracking

        try:
            pake.subpake(os.path.join(script_dir, 'assert_subpake_depth.py'), '-D', 'DEPTH=0', exit_on_error=False)
        except pake.SubpakeException as err:
            self.fail('subpake depth=0 assertion failed, return code {}.'.format(err.returncode))

        # Pake must be initialized for depth tracking
        pake.init()

        try:
            pake.subpake(os.path.join(script_dir, 'assert_subpake_depth.py'), '-D', 'DEPTH=1', exit_on_error=False)
        except pake.SubpakeException as err:
            self.fail('subpake depth=1 assertion failed, return code {}.'.format(err.returncode))

