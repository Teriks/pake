import unittest
import sys
import os

sys.path.insert(1,
                os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../../')))

import pake.subpake

script_dir = os.path.dirname(os.path.realpath(__file__))


class IntegrationTest(unittest.TestCase):
    def test_integrated(self):
        try:
            pake.subpake.run_pake(os.path.join(script_dir, "pakefile.py"), silent=True)
        except Exception as e:
            self.fail("run_pake raised unexpected exception {}".format(e))

        self.assertTrue(os.path.exists(os.path.join(script_dir, "do_stuff.o")))
        self.assertTrue(os.path.exists(os.path.join(script_dir, "do_stuff_first.o")))
        self.assertTrue(os.path.exists(os.path.join(script_dir, "do_stuff_first_2.o")))
        self.assertTrue(os.path.exists(os.path.join(script_dir, "main")))
        self.assertTrue(os.path.exists(os.path.join(script_dir, "stuffs_combined.o")))
        self.assertTrue(os.path.exists(os.path.join(script_dir, "stuffs_four.o")))
        self.assertTrue(os.path.exists(os.path.join(script_dir, "stuffs_three.o")))
        self.assertTrue(os.path.exists(os.path.join(script_dir, os.path.join("subpake","test.o"))))

        try:
            pake.subpake.run_pake(os.path.join(script_dir, "pakefile.py"),"clean", silent=True)
        except Exception as e:
            self.fail("run_pake raised unexpected exception {}".format(e))

        self.assertFalse(os.path.exists(os.path.join(script_dir, "do_stuff.o")))
        self.assertFalse(os.path.exists(os.path.join(script_dir, "do_stuff_first.o")))
        self.assertFalse(os.path.exists(os.path.join(script_dir, "do_stuff_first_2.o")))
        self.assertFalse(os.path.exists(os.path.join(script_dir, "main")))
        self.assertFalse(os.path.exists(os.path.join(script_dir, "stuffs_combined.o")))
        self.assertFalse(os.path.exists(os.path.join(script_dir, "stuffs_four.o")))
        self.assertFalse(os.path.exists(os.path.join(script_dir, "stuffs_three.o")))
        self.assertFalse(os.path.exists(os.path.join(script_dir, os.path.join("subpake","test.o"))))

    def test_integrated_parallel(self):
        try:
            pake.subpake.run_pake(os.path.join(script_dir, "pakefile.py"), "-j", 10, silent=True)
        except Exception as e:
            self.fail("run_pake raised unexpected exception {}".format(e))

        self.assertTrue(os.path.exists(os.path.join(script_dir, "do_stuff.o")))
        self.assertTrue(os.path.exists(os.path.join(script_dir, "do_stuff_first.o")))
        self.assertTrue(os.path.exists(os.path.join(script_dir, "do_stuff_first_2.o")))
        self.assertTrue(os.path.exists(os.path.join(script_dir, "main")))
        self.assertTrue(os.path.exists(os.path.join(script_dir, "stuffs_combined.o")))
        self.assertTrue(os.path.exists(os.path.join(script_dir, "stuffs_four.o")))
        self.assertTrue(os.path.exists(os.path.join(script_dir, "stuffs_three.o")))
        self.assertTrue(os.path.exists(os.path.join(script_dir, os.path.join("subpake","test.o"))))

        try:
            pake.subpake.run_pake(os.path.join(script_dir, "pakefile.py"), "clean", "-j", 10, silent=True)
        except Exception as e:
            self.fail("run_pake raised unexpected exception {}".format(e))

        self.assertFalse(os.path.exists(os.path.join(script_dir, "do_stuff.o")))
        self.assertFalse(os.path.exists(os.path.join(script_dir, "do_stuff_first.o")))
        self.assertFalse(os.path.exists(os.path.join(script_dir, "do_stuff_first_2.o")))
        self.assertFalse(os.path.exists(os.path.join(script_dir, "main")))
        self.assertFalse(os.path.exists(os.path.join(script_dir, "stuffs_combined.o")))
        self.assertFalse(os.path.exists(os.path.join(script_dir, "stuffs_four.o")))
        self.assertFalse(os.path.exists(os.path.join(script_dir, "stuffs_three.o")))
        self.assertFalse(os.path.exists(os.path.join(script_dir, os.path.join("subpake","test.o"))))


if __name__ == 'main':
    unittest.main()
