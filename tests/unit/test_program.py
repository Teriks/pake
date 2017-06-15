import sys
import unittest

import os

script_dir = os.path.dirname(os.path.realpath(__file__))

sys.path.insert(1, os.path.abspath(
                   os.path.join(script_dir, os.path.join('..', '..'))))

import pake
import pake.program
import pake.conf
import pake.arguments
import pake.returncodes as returncodes


from tests import open_devnull
pake.conf.stdout = open_devnull() if pake.conf.stdout is sys.stdout else pake.conf.stdout
pake.conf.stderr = open_devnull() if pake.conf.stderr is sys.stderr else pake.conf.stderr


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

        pake.program.shutdown()

        with self.assertRaises(SystemExit) as cm:
            pake.init(args=['-D', 'TEST={ I am a bad define'])

        self.assertEqual(cm.exception.code, returncodes.BAD_DEFINE_VALUE)

        pake.program.shutdown()

    def test_run(self):

        pake.program.shutdown()

        pk = pake.init()

        # should still be parsed and the object available, even with no arguments passed
        self.assertTrue(pake.arguments.args_are_parsed())

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
            self.assertEqual(pake.run(pk, call_exit=False), returncodes.NO_TASKS_DEFINED)

            @pk.task
            def task_one():
                raise Exception()

            # No tasks specified
            self.assertEqual(pake.run(pk, call_exit=False), returncodes.NO_TASKS_SPECIFIED)

            # Undefined task
            self.assertEqual(pake.run(pk, tasks='undefined', call_exit=False), returncodes.UNDEFINED_TASK)

            if not dry_run:
                # Exception in task
                self.assertEqual(pake.run(pk, tasks='task_one', call_exit=False), returncodes.TASK_EXCEPTION)

            @pk.task(i='IDontExist.nope', o='nada')
            def task_two():
                pass

            # Input file not found
            self.assertEqual(pake.run(pk, tasks='task_two', call_exit=False), returncodes.TASK_INPUT_NOT_FOUND)

            @pk.task(i='IDontExist.nope')
            def task_three():
                pass

            # Missing output file
            self.assertEqual(pake.run(pk, tasks='task_three', call_exit=False), returncodes.TASK_OUTPUT_MISSING)

            # ======== Cover Subpake and Call exception propagation

            @pk.task
            def task_four(ctx):
                ctx.subpake(os.path.join(script_dir, 'throw.py'))

            @pk.task
            def task_five(ctx):
                # execute with the current interpreter
                ctx.call(sys.executable, os.path.join(script_dir,'throw.py'))

            if not dry_run:
                # Because 'throw.py' runs but throws an exception
                self.assertEqual(pake.run(pk, tasks='task_four', call_exit=False), returncodes.SUBPAKE_EXCEPTION)

                # Same thing, except differentiate as a task subprocess exception
                self.assertEqual(pake.run(pk, tasks=task_five, call_exit=False), returncodes.TASK_SUBPROCESS_EXCEPTION)

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
            self.assertEqual(pake.run(pk, call_exit=False), returncodes.BAD_ARGUMENTS)

        # No multitasking in dry run mode.
        assert_bad_args('--dry-run', '--jobs', '2')

        with self.assertRaises(BaseException):
            # calls exit(2) because --jobs < 1
            assert_bad_args( '--jobs', '0')

        with self.assertRaises(BaseException):
            # calls exit(2) because -C directory does not exist
            assert_bad_args('-C', os.path.join(script_dir, 'IDONTEXIST'))

        with self.assertRaises(BaseException):
            # calls exit(2) because -C directory is actually a file
            assert_bad_args('-C', os.path.join(script_dir, 'test_program.py'))

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

    def test_run_changedir(self):

        pake.program.shutdown()

        start_dir = os.getcwd()

        dest_dir = os.path.abspath(os.path.join(script_dir, '..'))

        # Tell pake to change directories on init

        pk = pake.init(args=['-C', dest_dir])

        self.assertEqual(dest_dir, os.getcwd())

        @pk.task
        def check_dir(ctx):
            if dest_dir != os.getcwd():
                raise Exception()

        self.assertEqual(pake.run(pk, tasks=check_dir, call_exit=False), returncodes.SUCCESS)

        # Should be back to normal after run

        self.assertEqual(start_dir, os.getcwd())

        # ==========================
        # Check that its forced quietly before run, even if it is changed prior

        pake.program.shutdown()

        pk = pake.init(args=['-C', dest_dir])

        self.assertEqual(dest_dir, os.getcwd())

        @pk.task
        def check_dir(ctx):
            if dest_dir != os.getcwd():
                raise Exception()

        # Try changing it back...
        os.chdir(script_dir)

        # Directory should change here to dest_dir
        self.assertEqual(pake.run(pk, tasks=check_dir, call_exit=False), returncodes.SUCCESS)

        # Should be back to normal after run

        self.assertEqual(start_dir, os.getcwd())


