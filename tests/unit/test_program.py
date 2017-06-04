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

        self.assertEqual(pake.get_subpake_depth(), 0)

        self.assertEqual(pake.get_max_jobs(), 1)

        self.assertEqual(pk.task_count, 0)

        self.assertEqual(len(pk.task_contexts), 0)

        this_file = os.path.abspath(__file__)

        self.assertEqual(pake.get_init_file(), this_file)

        self.assertEqual(pake.get_init_dir(), os.getcwd())

        with self.assertRaises(ValueError):
            pake.program.run(None)

        pake.program.shutdown()

        pk = pake.init(args=['--jobs', '10'])

        self.assertEqual(pake.get_max_jobs(), 10)

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

        self.assertEqual(pk.task_count, 2)

        pake.run(pk, tasks=[task_one, 'task_two'])

        self.assertEqual(pk.task_count, 2)

        self.assertEqual(pk.run_count, run_count)

        # ===========

        def test_run_helper(dry_run=False):
            nonlocal self

            pake.program.shutdown()

            if dry_run:
                pk = pake.init(args=['--dry-run'])
            else:
                pk = pake.init()

            # No tasks defined
            self.assertEqual(pake.run(pk, call_exit=False), 4)

            @pk.task
            def task_one():
                raise Exception()

            # No tasks specified
            self.assertEqual(pake.run(pk, call_exit=False), 5)

            # Undefined task
            self.assertEqual(pake.run(pk, tasks='undefined', call_exit=False), 8)

            if not dry_run:
                # Exception in task
                self.assertEqual(pake.run(pk, tasks='task_one', call_exit=False), 10)

            @pk.task(i='IDontExist.nope', o='nada')
            def task_two():
                pass

            # Input file not found
            self.assertEqual(pake.run(pk, tasks='task_two', call_exit=False), 6)

            @pk.task(i='IDontExist.nope')
            def task_three():
                pass

            # Missing output file
            self.assertEqual(pake.run(pk, tasks='task_three', call_exit=False), 7)

        test_run_helper()
        test_run_helper(True)

        # =====

        # Test bad argument combinations, return code 3

        def assert_bad_args(*args):
            pake.program.shutdown()
            pk = pake.init(args=list(args))

            @pk.task
            def dummy(ctx):
                pass

            # Invalid argument combination
            self.assertEqual(pake.run(pk, call_exit=False), 3)

        # No multitasking in dry run mode.
        assert_bad_args('--dry-run', '--jobs', '2')

        # Cant run tasks when listing task info anyway.
        assert_bad_args('--dry-run', '--show-tasks')
        assert_bad_args('--dry-run', '--show-task-info')

        # Cant do both at once.
        assert_bad_args('--show-tasks', '--show-task-info')

        # Cant specify jobs with --show-task*
        assert_bad_args('--show-tasks', '--jobs', '2')
        assert_bad_args('--show-task-info', '--jobs', '2')

        # Cant show info and run a target.
        assert_bad_args('--show-task-info', 'dummy')
        assert_bad_args('--show-tasks', 'dummy')


