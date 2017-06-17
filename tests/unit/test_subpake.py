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
    def test_subpake_depth(self):
        assert_depth_script = os.path.join(script_dir, 'assert_subpake_depth.py')

        pake.de_init(clear_conf=False)

        with self.assertRaises(SystemExit) as err:
            pake.subpake(os.path.join(script_dir, 'throw.py'))

        with self.assertRaises(pake.SubpakeException) as err:
            pake.subpake(os.path.join(script_dir, 'throw.py'), exit_on_error=False)

        # If pake is not initialized, there is no depth tracking

        try:
            pake.subpake(assert_depth_script, '-D', 'DEPTH=0', exit_on_error=False)
        except pake.SubpakeException as err:
            self.fail('subpake depth=0 assertion failed, return code {}.'.format(err.returncode))

        # Pake must be initialized for depth tracking
        pake.init()

        try:
            pake.subpake(assert_depth_script, '-D', 'DEPTH=1', exit_on_error=False)
        except pake.SubpakeException as err:
            self.fail('subpake depth=1 assertion failed, return code {}.'.format(err.returncode))

    def test_subpake_ignore_errors(self):
        return_code_pakefile = os.path.join(script_dir, 'returncode_pakefile.py')

        pake.de_init(clear_conf=False)

        # ====== Non Silent Path =======

        pake.export('RETURNCODE', 42)

        self.assertEqual(pake.subpake(return_code_pakefile, ignore_errors=True), 42)

        pake.export('TERMINATE', True)

        self.assertEqual(pake.subpake(return_code_pakefile, ignore_errors=True), 42)

        # ======= Silent Path =========

        pake.de_init(clear_conf=False)

        pake.export('RETURNCODE', 42)

        self.assertEqual(pake.subpake(return_code_pakefile, silent=True, ignore_errors=True), 42)

        pake.export('TERMINATE', True)

        self.assertEqual(pake.subpake(return_code_pakefile, silent=True, ignore_errors=True), 42)

        pake.EXPORTS.clear()
