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

pake.conf.stdout = open_devnull()
pake.conf.stderr = open_devnull()


class ProgramTest(unittest.TestCase):
    def test_exceptions(self):

        pake.de_init(clear_conf=False)

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

        pake.de_init(clear_conf=False)

        self.assertFalse(pake.is_init())

        with self.assertRaises(pake.PakeUninitializedException):
            pake.terminate(pake.Pake(), 0)

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

        pake.de_init(clear_conf=False)

        pk = pake.init(args=['--jobs', '10'])

        self.assertEqual(pake.get_max_jobs(), 10)

        pake.de_init(clear_conf=False)

        with self.assertRaises(SystemExit) as cm:
            pake.init(args=['-D', 'TEST={ I am a bad define'])

        self.assertEqual(cm.exception.code, returncodes.BAD_DEFINE_VALUE)

        # These should not throw

        pake.init(args=['-D', 'TEST= {"I am a good define" } '])

        pake.init(args=['-D', 'TEST= "I am a good define" '])

        pake.init(args=['-D', 'TEST= 1 am a good define '])

        # they are strings
        pake.init(args=['-D', 'TEST= 1 2 3 '])
        pake.init(args=['-D', 'TEST=1 2 3 '])

        pake.de_init(clear_conf=False)

    def test_run(self):

        pake.de_init(clear_conf=False)

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

        with self.assertRaises(ValueError):
            # Because jobs <= 1
            pake.run(pk, tasks=[task_one, 'task_two'], jobs=0)

        with self.assertRaises(ValueError):
            # Because jobs <= 1
            pake.run(pk, tasks=[task_one, 'task_two'], jobs=-1)

        # ===========

        def test_run_helper(dry_run=False):
            nonlocal self

            pake.de_init(clear_conf=False)

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
                ctx.call(sys.executable, os.path.join(script_dir, 'throw.py'))

            if not dry_run:
                # Because 'throw.py' runs but throws an exception
                self.assertEqual(pake.run(pk, tasks='task_four', call_exit=False), returncodes.SUBPAKE_EXCEPTION)

                # Same thing, except differentiate as a task subprocess exception
                self.assertEqual(pake.run(pk, tasks=task_five, call_exit=False), returncodes.TASK_SUBPROCESS_EXCEPTION)

        test_run_helper()
        test_run_helper(True)

    def test_bad_arguments(self):
        # Test pake's reaction to bad argument combinations, code returncodes.BAD_ARGUMENTS

        def assert_bad_args(*args):
            pake.de_init(clear_conf=False)

            try:
                pake.init(args=list(args))
            except SystemExit as err:
                exit_init_code = err.code
                self.assertEqual(exit_init_code, returncodes.BAD_ARGUMENTS,
                                 msg='Passed bad command line arguments, exited with 0 (success).')
            else:
                self.fail('Bad command line arguments were passed to pake.init and it did not exit!')

        # This does not make sense
        assert_bad_args('--show-tasks', '--stdin-defines')

        # This does not make sense
        assert_bad_args('--show-task-info', '--stdin-defines')

        # No multitasking in dry run mode.
        assert_bad_args('--dry-run', '--jobs', '2')

        # because --jobs < 1
        assert_bad_args('--jobs', '0')

        # because -C directory does not exist
        assert_bad_args('-C', os.path.join(script_dir, 'IDONTEXIST'))

        # because -C directory is actually a file
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

        def assert_exit_code(*args,
                             no_tasks=False,
                             all_up_to_date=False,
                             code=returncodes.SUCCESS):

            pake.de_init(clear_conf=False)

            try:
                pk = pake.init(args=list(args))

                if no_tasks is False:
                    # Make all tasks up to date, pake does not care
                    # if the input file is the same as the output
                    # it just compares the modification time of whatever is there
                    in_out = os.path.join(script_dir, 'test_data', 'in1') if all_up_to_date else None
                    pk.add_task('dummy', lambda ctx: None, inputs=in_out, outputs=in_out)
                    pk.add_task('dummy2', lambda ctx: None, inputs=in_out, outputs=in_out)

                got_code = pake.run(pk)

                self.assertEqual(got_code, code,
                                 msg='Command line argument resulted in an unexpected exit code. '
                                 'expected {}, but got {}.'.format(code, got_code))

            except SystemExit as err:
                self.assertEqual(err.code, code,
                                 msg='Command line argument resulted in an unexpected exit code. '
                                     'expected {}, but got {}.'.format(code, err.code))

        # These assert returncodes.SUCCESS

        assert_exit_code('-ti')
        assert_exit_code('-t')

        assert_exit_code('--show-task-info')
        assert_exit_code('--show-tasks')

        assert_exit_code('dummy')

        assert_exit_code('dummy', '--sync-output', 'True')
        assert_exit_code('dummy', '--sync-output', 'true')

        assert_exit_code('dummy', '--sync-output', 'False')
        assert_exit_code('dummy', '--sync-output', 'false')

        assert_exit_code('dummy', '--sync-output', '1')
        assert_exit_code('dummy', '--sync-output', '0')

        assert_exit_code('dummy', '--jobs', '10')
        assert_exit_code('dummy', '--jobs', 10, '--sync-output', False)

        assert_exit_code('dummy', 'dummy2')
        assert_exit_code('dummy', 'dummy2', '--sync-output', False)
        assert_exit_code('dummy', 'dummy2', '--jobs', 10)
        assert_exit_code('dummy', 'dummy2', '--jobs', 10, '--sync-output', False)

        assert_exit_code('dummy', all_up_to_date=True)
        assert_exit_code('dummy', 'dummy2', all_up_to_date=True)

        assert_exit_code('dummy', '--dry-run', all_up_to_date=True)
        assert_exit_code('dummy', 'dummy2', '--dry-run', all_up_to_date=True)

        assert_exit_code('dummy', '--dry-run')
        assert_exit_code('dummy', 'dummy2', '--dry-run')

        # These assert failures

        assert_exit_code(code=returncodes.NO_TASKS_SPECIFIED)
        assert_exit_code(no_tasks=True, code=returncodes.NO_TASKS_DEFINED)

        assert_exit_code(all_up_to_date=True, code=returncodes.NO_TASKS_SPECIFIED)

    def test_run_changedir(self):

        pake.de_init(clear_conf=False)

        start_dir = os.getcwd()

        dest_dir = os.path.abspath(os.path.join(script_dir, '..'))

        # Tell pake to change directories on init

        pk = pake.init(args=['-C', dest_dir])

        self.assertEqual(dest_dir, os.getcwd())

        self.assertEqual(pake.get_init_dir(), start_dir)

        @pk.task
        def check_dir(ctx):
            if dest_dir != os.getcwd():
                raise Exception()

        self.assertEqual(pake.run(pk, tasks=check_dir, call_exit=False), returncodes.SUCCESS)

        # Should be back to normal after run

        self.assertEqual(start_dir, os.getcwd())

        # ==========================
        # Check that its forced quietly before run, even if it is changed prior

        pake.de_init(clear_conf=False)

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
