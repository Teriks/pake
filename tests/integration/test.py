import unittest
import sys
import os

sys.path.insert(1,
                os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../../')))

import pake

script_dir = os.path.dirname(os.path.realpath(__file__))


class IntegrationTest(unittest.TestCase):

    def _check_outputs(self, exist=True):
        fun = self.assertTrue if exist else self.assertFalse

        fun(os.path.exists(os.path.join(script_dir, "do_stuff.o")))
        fun(os.path.exists(os.path.join(script_dir, "do_stuff_first.o")))
        fun(os.path.exists(os.path.join(script_dir, "do_stuff_first_2.o")))
        fun(os.path.exists(os.path.join(script_dir, "main")))
        fun(os.path.exists(os.path.join(script_dir, "stuffs_combined.o")))
        fun(os.path.exists(os.path.join(script_dir, "stuffs_four.o")))
        fun(os.path.exists(os.path.join(script_dir, "stuffs_three.o")))
        fun(os.path.exists(os.path.join(script_dir, os.path.join("subpake","test.o"))))

        fun(os.path.exists(os.path.join(script_dir, "glob_and_pattern_test", "src_a", "a.o")))
        fun(os.path.exists(os.path.join(script_dir, "glob_and_pattern_test", "src_a", "b.o")))
        fun(os.path.exists(os.path.join(script_dir, "glob_and_pattern_test", "src_a", "c.o")))

        fun(os.path.exists(os.path.join(script_dir, "glob_and_pattern_test", "src_b", "a.o")))
        fun(os.path.exists(os.path.join(script_dir, "glob_and_pattern_test", "src_b", "b.o")))
        fun(os.path.exists(os.path.join(script_dir, "glob_and_pattern_test", "src_b", "c.o")))

        fun(os.path.exists(os.path.join(script_dir, "glob_and_pattern_test", "a.o")))
        fun(os.path.exists(os.path.join(script_dir, "glob_and_pattern_test", "b.o")))
        fun(os.path.exists(os.path.join(script_dir, "glob_and_pattern_test", "c.o")))

    def test_integrated(self):
        try:
            pake.subpake(os.path.join(script_dir, "pakefile.py"), silent=True)
        except Exception as e:
            self.fail("subpake raised unexpected exception {}".format(e))

        self._check_outputs()

        try:
            pake.subpake(os.path.join(script_dir, "pakefile.py"),"clean", silent=True)
        except Exception as e:
            self.fail("subpake raised unexpected exception {}".format(e))

        self._check_outputs(exist=False)

    def test_integrated_parallel(self):
        try:
            pake.subpake(os.path.join(script_dir, "pakefile.py"), "-j", 10, silent=True)
        except Exception as e:
            self.fail("subpake raised unexpected exception {}".format(e))

        self._check_outputs()

        try:
            pake.subpake(os.path.join(script_dir, "pakefile.py"), "clean", "-j", 10, silent=True)
        except Exception as e:
            self.fail("subpake raised unexpected exception {}".format(e))

        self._check_outputs(exist=False)


if __name__ == 'main':
    unittest.main()
