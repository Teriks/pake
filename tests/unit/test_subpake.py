import sys
import unittest

import os

sys.path.insert(1,
                os.path.abspath(
                    os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                 os.path.join('..', '..'))))

import pake
import pake.program

script_dir = os.path.dirname(os.path.realpath(__file__))


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

