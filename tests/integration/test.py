import sys
import unittest

import os

sys.path.insert(1,
                os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../../')))

import pake

script_dir = os.path.dirname(os.path.realpath(__file__))


class IntegrationTest(unittest.TestCase):
    def _check_outputs(self, exist=True):
        fun = self.assertTrue if exist else self.assertFalse
        fun(os.path.exists(os.path.join(script_dir, "test_data", "do_stuff.o")))
        fun(os.path.exists(os.path.join(script_dir, "test_data", "do_stuff_first.o")))
        fun(os.path.exists(os.path.join(script_dir, "test_data", "do_stuff_first_2.o")))
        fun(os.path.exists(os.path.join(script_dir, "test_data", "main")))
        fun(os.path.exists(os.path.join(script_dir, "test_data", "stuffs_combined.o")))
        fun(os.path.exists(os.path.join(script_dir, "test_data", "stuffs_four.o")))
        fun(os.path.exists(os.path.join(script_dir, "test_data", "stuffs_three.o")))
        fun(os.path.exists(os.path.join(script_dir, "test_data", "toucher_class_file_1.o")))
        fun(os.path.exists(os.path.join(script_dir, "test_data", "toucher_class_file_2.o")))
        fun(os.path.exists(os.path.join(script_dir, "test_data", "toucher_class_file_3.o")))
        fun(os.path.exists(os.path.join(script_dir, "test_data", "toucher_func_file_4.o")))
        fun(os.path.exists(os.path.join(script_dir, "test_data", "subpake", "test.o")))

        fun(os.path.exists(os.path.join(script_dir, "test_data", "glob_and_pattern", "src_a", "a.o")))
        fun(os.path.exists(os.path.join(script_dir, "test_data", "glob_and_pattern", "src_a", "b.o")))
        fun(os.path.exists(os.path.join(script_dir, "test_data", "glob_and_pattern", "src_a", "c.o")))

        fun(os.path.exists(os.path.join(script_dir, "test_data", "glob_and_pattern", "src_b", "a.o")))
        fun(os.path.exists(os.path.join(script_dir, "test_data", "glob_and_pattern", "src_b", "b.o")))
        fun(os.path.exists(os.path.join(script_dir, "test_data", "glob_and_pattern", "src_b", "c.o")))

        fun(os.path.exists(os.path.join(script_dir, "test_data", "glob_and_pattern", "a.o")))
        fun(os.path.exists(os.path.join(script_dir, "test_data", "glob_and_pattern", "b.o")))
        fun(os.path.exists(os.path.join(script_dir, "test_data", "glob_and_pattern", "c.o")))

    def test_integrated(self):
        pake.subpake(os.path.join(script_dir, "pakefile.py"), silent=True)

        self._check_outputs()

        pake.subpake(os.path.join(script_dir, "pakefile.py"), "clean", silent=True)

        self._check_outputs(exist=False)

    def test_integrated_parallel(self):
        pake.subpake(os.path.join(script_dir, "pakefile.py"), "-j", 10, silent=True)

        self._check_outputs()

        pake.subpake(os.path.join(script_dir, "pakefile.py"), "clean", "-j", 10, silent=True)

        self._check_outputs(exist=False)


if __name__ == 'main':
    unittest.main()
