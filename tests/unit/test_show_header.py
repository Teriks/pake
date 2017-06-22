import sys
import tempfile
import unittest

import os

script_dir = os.path.dirname(os.path.realpath(__file__))

sys.path.insert(1, os.path.abspath(
    os.path.join(script_dir, os.path.join('..', '..'))))

import pake


class ShowHeaderTest(unittest.TestCase):

    def test_show_header(self):

        # This test verifies that the pake.Pake.show_task_headers option
        # and the show_header parameter of pk.add_task and pk.task
        # are working correctly in conjunction with each other

        with tempfile.TemporaryFile(mode='w+') as pk_stdout:

            pake.de_init(clear_conf=False)

            pk = pake.init(stdout=pk_stdout)

            self.assertTrue(pk.show_task_headers)

            @pk.task
            def test_task(ctx):
                # I will print a header by default
                pass

            pake.run(pk, tasks=test_task)

            self.assertGreater(pk_stdout.tell(), 0,
                               msg='Task with show_header=None (default value) did not write '
                                   'a header when pk.show_task_headers=True.')

            pk_stdout.seek(0)

            # ============

            pake.de_init(clear_conf=False)

            pk = pake.init(stdout=pk_stdout)

            self.assertTrue(pk.show_task_headers)

            @pk.task(show_header=False)
            def test_task(ctx):
                # I will print nothing at all,
                # even if pk.show_task_headers is True
                pass

            pake.run(pk, tasks=test_task)

            self.assertEqual(pk_stdout.tell(), 0,
                             msg='Task with show_header=False wrote to header to pakes output '
                                 'when pk.show_task_headers=True.')

            pk_stdout.seek(0)

            # ============

            pake.de_init(clear_conf=False)

            pk = pake.init(stdout=pk_stdout)

            pk.show_task_headers = False

            @pk.task
            def test_task(ctx):
                # I will print nothing at all,
                # because pk.show_task_headers is False
                # and it was not overridden with show_header=True
                pass

            pake.run(pk, tasks=test_task)

            self.assertEqual(pk_stdout.tell(), 0,
                             msg='Task with show_header=None (default value) wrote a header '
                                 'to pakes output when pk.show_task_headers=False.')

            pk_stdout.seek(0)

            # ============

            pake.de_init(clear_conf=False)

            pk = pake.init(stdout=pk_stdout)

            pk.show_task_headers = False

            @pk.task(show_header=True)
            def test_task(ctx):
                # I will print a header regardless
                # of pk.show_task_headers being False,
                # because show_header has been forced to True
                # on the task
                pass

            pake.run(pk, tasks=test_task)

            self.assertGreater(pk_stdout.tell(), 0,
                               msg='Task with show_header=True did not write header to pakes '
                                   'output when pk.show_task_headers=False.')