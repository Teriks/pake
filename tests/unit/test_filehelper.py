import sys
import unittest

import os

sys.path.insert(1,
                os.path.abspath(
                    os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                 os.path.join('..', '..'))))

import pake

script_dir = os.path.dirname(os.path.realpath(__file__))


class SubpakeTest(unittest.TestCase):
    def file_helper_test_stub(self, ctx, silent):

        fp = pake.FileHelper(ctx)

        self.assertEqual(fp.task_ctx, ctx)

        # FileHelper.makedirs
        # =============================

        fp.makedirs('test_data/filehelper/sub', silent=silent)

        with self.assertRaises(OSError):
            fp.makedirs('test_data/filehelper/sub', exist_ok=False, silent=silent)

        with self.assertRaises(OSError):
            fp.makedirs('test_data/filehelper', exist_ok=False, silent=silent)

        with self.assertRaises(OSError):
            fp.makedirs('test_data', exist_ok=False, silent=silent)

        self.assertTrue(os.path.isdir('test_data/filehelper'))

        self.assertTrue(os.path.isdir('test_data/filehelper/sub'))

        for i in range(0, 3):
            fp.makedirs('test_data/filehelper/delete_me_{}/sub'.format(i), silent=silent)
            self.assertTrue(os.path.isdir('test_data/filehelper/delete_me_{}/sub'.format(i)))

            touch_file = 'test_data/filehelper/delete_me_{idx}/sub/file{idx}.txt'.format(idx=i)

            fp.touch(touch_file, silent=silent)

            self.assertTrue(os.path.isfile(touch_file))


        # FileHelper.copytree
        # =============================

        fp.copytree('test_data/filehelper', 'test_data/filehelper/copy_test', silent=silent)

        self.assertTrue(os.path.isdir('test_data/filehelper/copy_test'))

        for i in range(0, 3):
            touch_file = 'test_data/filehelper/copy_test/delete_me_{idx}/sub/file{idx}.txt'.format(idx=i)
            self.assertTrue(os.path.isfile(touch_file))

        with self.assertRaises(FileExistsError):
            fp.copytree('test_data/filehelper', 'test_data/filehelper/copy_test', silent=silent)


        # FileHelper.move
        # =============================

        fp.makedirs('test_data/filehelper/movedir', silent=silent)
        fp.touch('test_data/filehelper/move.txt', silent=silent)

        fp.move('test_data/filehelper/move.txt', 'test_data/filehelper/movedir', silent=silent)

        self.assertTrue(os.path.isfile('test_data/filehelper/movedir/move.txt'))

        fp.move('test_data/filehelper/movedir', 'test_data/filehelper/copy_test', silent=silent)

        self.assertTrue(os.path.isfile('test_data/filehelper/copy_test/movedir/move.txt'))


        # FileHelper.remove
        #  =============================

        fp.remove('test_data/filehelper/copy_test/movedir/move.txt', silent=silent)

        self.assertFalse(os.path.isfile('test_data/filehelper/copy_test/movedir/move.txt'))

        try:
            fp.remove('test_data/filehelper/copy_test/movedir/move.txt', silent=silent)
        except Exception:
            self.fail(
                'pake.FileHelper.remove threw removing a non existing file.  It should not do this when must_exist=True, which is default.')

        with self.assertRaises(FileNotFoundError):
            fp.remove('test_data/filehelper/copy_test/movedir/move.txt', must_exist=True, silent=silent)

        # Cannot use remove to remove directories, must use rmtree
        with self.assertRaises(OSError):
            fp.remove('test_data/filehelper/copy_test/movedir', must_exist=True, silent=silent)


        # FileHelper.touch
        # =============================

        try:
            fp.touch('test_data/filehelper/delete_me_0/sub/file0.txt', silent=silent)
        except Exception:
            self.fail(
                'pake.FileHelper.touch threw touching an existing file.  It should not do this when exist_ok=True, which is default.')

        with self.assertRaises(FileExistsError):
            fp.touch('test_data/filehelper/delete_me_0/sub/file0.txt', silent=silent, exist_ok=False)


        # FileHelper.glob_remove
        # =============================

        fp.glob_remove('test_data/filehelper/delete_me_**/sub/file*.txt', silent=silent)

        for i in range(0, 3):
            self.assertFalse(os.path.isfile('test_data/filehelper/delete_me_{idx}/sub/file{idx}.txt'.format(idx=i)))


        # FileHelper.copy
        # =============================

        fp.copy('test_data/in1', 'test_data/filehelper', silent=silent)

        self.assertTrue(os.path.isfile('test_data/filehelper/in1'))

        try:
            fp.copy('test_data/in1', 'test_data/filehelper', silent=silent)
        except Exception:
            self.fail(
                'pake.FileHelper.copy threw overwriting an existing file.  It should not do this.')

        # Just to hit the second path, there is not really a way to portably test copying the metadata,
        # it is up to the shutil module to do it anyway.

        fp.copy('test_data/in2', 'test_data/filehelper', silent=silent, copy_metadata=True)

        self.assertTrue(os.path.isfile('test_data/filehelper/in2'))

        try:
            fp.copy('test_data/in2', 'test_data/filehelper', silent=silent, copy_metadata=True)
        except Exception:
            self.fail(
                'pake.FileHelper.copy with metadata threw overwriting an existing file.  It should not do this.')


        # FileHelper.glob_remove_dirs
        # =============================

        # remove the sub folders under the folders starting with delete_me_*

        fp.glob_remove_dirs('test_data/filehelper/delete_me_**/su*', silent=silent)

        for i in range(0, 3):
            # delete_me_* should remain intact, the sub folders should not
            self.assertTrue(os.path.isdir('test_data/filehelper/delete_me_{}'.format(i)))
            self.assertFalse(os.path.isdir('test_data/filehelper/delete_me_{}/sub'.format(i)))

        fp.glob_remove_dirs('test_data/filehelper/delete_me_*', silent=silent)

        for i in range(0, 3):
            # now they should be gone
            self.assertFalse(os.path.isdir('test_data/filehelper/delete_me_{}'.format(i)))


        # FileHelper.rmtree
        # =============================

        fp.rmtree('test_data/filehelper', silent=silent)

        try:
            fp.rmtree('test_data/filehelper', silent=silent)
        except Exception:
            self.fail(
                'pake.FileHelper.rmtree threw removing a non existent directory.  It should not do this when must_exist=False, which is default.')

        with self.assertRaises(FileNotFoundError):
            fp.rmtree('test_data/filehelper', silent=silent, must_exist=True)

    def test_filehelper(self):

        fh = pake.FileHelper()

        self.assertEqual(fh.task_ctx, None)

        class SilentTestCtx:
            def print(*args, **kwargs):
                nonlocal self
                self.fail('SilentTestCtx printed from file helper function set to be silent.')

        class TestCtx:
            def print(*args, **kwargs):
                pass

        past_cwd = os.getcwd()
        os.chdir(script_dir)

        self.file_helper_test_stub(SilentTestCtx(), silent=True)

        self.file_helper_test_stub(TestCtx(), silent=False)

        self.file_helper_test_stub(None, silent=True)

        self.file_helper_test_stub(None, silent=False)

        os.chdir(past_cwd)
