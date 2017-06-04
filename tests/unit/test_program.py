import sys
import unittest

import os

sys.path.insert(1,
                os.path.abspath(
                    os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                 os.path.join('..', '..'))))
import pake
import pake.program
import pake.conf
import pake.arguments


class ProgramTest(unittest.TestCase):
    def test_exceptions(self):

        pake.program.shutdown()

        self.assertFalse(pake.program.is_init())

        with self.assertRaises(pake.PakeUninitializedException):
            pake.program.get_max_jobs()

        with self.assertRaises(pake.PakeUninitializedException):
            pake.program.get_subpake_depth()

        with self.assertRaises(pake.PakeUninitializedException):
            pake.program.get_init_dir()

        with self.assertRaises(pake.PakeUninitializedException):
            pake.program.get_init_file()

        with self.assertRaises(pake.PakeUninitializedException):
            pake.program.run(pake.Pake())

        with self.assertRaises(pake.PakeUninitializedException):
            pake.program.run(None)

    def test_init(self):

        pake.program.shutdown()

        self.assertFalse(pake.is_init())

        pk = pake.init()

        self.assertTrue(pk.stdout is pake.conf.stdout)

        self.assertTrue(pake.is_init())

        self.assertTrue(pake.get_subpake_depth() == 0)

        self.assertTrue(pake.get_max_jobs() == 1)

        self.assertTrue(pk.task_count == 0)

        self.assertTrue(len(pk.task_contexts) == 0)

        this_file = os.path.abspath(__file__)

        self.assertTrue(pake.get_init_file() == this_file)

        self.assertTrue(pake.get_init_dir() == os.getcwd())

        with self.assertRaises(ValueError):
            pake.program.run(None)

        pake.program.shutdown()

        pk = pake.init(args=['--jobs', '10'])

        self.assertTrue(pake.get_max_jobs() == 10)

    def test_run(self):

        pake.program.shutdown()

        pk = pake.init()

        run_count = 0

        @pk.task
        def task_one(ctx):
            nonlocal run_count
            run_count += 1

        @pk.task
        def task_two(ctx):
            nonlocal run_count
            run_count += 1

        self.assertTrue(pk.task_count == 2)

        pake.run(pk, tasks=[task_one, 'task_two'])

        self.assertTrue(pk.task_count == 2)

        self.assertTrue(pk.run_count == run_count)

        # ===========

        def test_run_helper(dry_run=False):
            nonlocal self

            pake.program.shutdown()

            if dry_run:
                pk = pake.init(args=['--dry-run'])
            else:
                pk = pake.init()

            # No tasks defined
            self.assertTrue(pake.run(pk, call_exit=False) == 4)

            @pk.task
            def task_one():
                raise Exception()

            # No tasks specified
            self.assertTrue(pake.run(pk, call_exit=False) == 5)

            # Undefined task
            self.assertTrue(pake.run(pk, tasks='undefined', call_exit=False) == 8)

            if not dry_run:
                # Exception in task
                self.assertTrue(pake.run(pk, tasks='task_one', call_exit=False) == 10)

            @pk.task(i='IDontExist.nope', o='nada')
            def task_two():
                pass

            # Input file not found
            self.assertTrue(pake.run(pk, tasks='task_two', call_exit=False) == 6)

            @pk.task(i='IDontExist.nope')
            def task_three():
                pass

            # Missing output file
            self.assertTrue(pake.run(pk, tasks='task_three', call_exit=False) == 7)

        test_run_helper()
        test_run_helper(True)
