import sys
import unittest

import os

script_dir = os.path.dirname(os.path.realpath(__file__))

sys.path.insert(1, os.path.abspath(
    os.path.join(script_dir, os.path.join('..', '..'))))

import pake
import pake.program
import pake.util
import pake.conf
import pake.returncodes

from tests import open_devnull

pake.conf.stdout = open_devnull() if pake.conf.stdout is sys.stdout else pake.conf.stdout
pake.conf.stderr = open_devnull() if pake.conf.stderr is sys.stderr else pake.conf.stderr


class PakeTest(unittest.TestCase):
    def test_registration_and_run(self):

        pake.program.shutdown()

        pk = pake.init()

        def undefined_task():
            pass

        with self.assertRaises(pake.UndefinedTaskException):
            _ = pk.get_task_name(undefined_task)

        with self.assertRaises(pake.UndefinedTaskException):
            _ = pk.get_task_context(undefined_task)

        with self.assertRaises(pake.UndefinedTaskException):
            _ = pk.get_task_name("undefined_task")

        with self.assertRaises(pake.UndefinedTaskException):
            _ = pk.get_task_context("undefined_task")

        script_path = os.path.dirname(os.path.abspath(__file__))

        in1 = os.path.join(script_path, 'test_data', 'in1')

        # Does not need to exist, easier than dealing with
        # a full path.

        out1 = 'out1'

        pake.util.touch(in1)

        in2 = os.path.join(script_path, 'test_data', 'in2')

        # Does not need to exist either.

        out2 = 'out2'

        pake.util.touch(in2)

        @pk.task(o='dep_one.o')
        def dep_one(ctx):
            pass

        @pk.task(o=['dep_two.o', out2])
        def dep_two(ctx):
            pass

        @pk.task(o='dep_three.o')
        def dep_three(ctx):
            pass

        @pk.task(dep_one, dep_two, i=in1, o=out1)
        def task_one(ctx):
            nonlocal self
            self.assertListEqual(ctx.inputs, [in1])
            self.assertListEqual(ctx.outputs, [out1])

            self.assertListEqual(ctx.outdated_inputs, [in1])
            self.assertListEqual(ctx.outdated_outputs, [out1])

            self.assertListEqual(list(ctx.outdated_pairs), [(in1, out1)])

            # Check that the correct immediate dependency outputs are reported.
            self.assertCountEqual(['dep_one.o', 'dep_two.o', out2], ctx.dependency_outputs)

            dep_one_ctx = pk.get_task_context(dep_one)
            dep_two_ctx = pk.get_task_context(dep_two)

            # Check that the correct immediate dependencies are reported.
            self.assertCountEqual([dep_one_ctx, dep_two_ctx], ctx.dependencies)

        def other_task(ctx):
            nonlocal self
            self.assertListEqual(ctx.inputs, [in2])
            self.assertListEqual(ctx.outputs, [out2])

            self.assertListEqual(ctx.outdated_inputs, [in2])
            self.assertListEqual(ctx.outdated_outputs, [out2])

            self.assertListEqual(list(ctx.outdated_pairs), [(in2, out2)])

            task_one_ctx = pk.get_task_context(task_one)
            dep_three_ctx = pk.get_task_context(dep_three)

            # Check that the correct immediate dependency outputs are reported.
            self.assertCountEqual(['dep_three.o', out1], ctx.dependency_outputs)

            # Check that the correct immediate dependencies are reported.
            self.assertCountEqual([task_one_ctx, dep_three_ctx], ctx.dependencies)

        ctx = pk.add_task('task_two', other_task,
                          inputs=in2, outputs=out2,
                          dependencies=[task_one, dep_three])

        task_one_ctx = pk.get_task_context(task_one)
        dep_three_ctx = pk.get_task_context(dep_three)

        # Check that the correct immediate dependencies are reported.
        # ctx.dependencies should return a meaningful value outside of a task
        # as well as inside. That is not the case with ctx.dependency_outputs
        self.assertCountEqual([task_one_ctx, dep_three_ctx], ctx.dependencies)

        # Not available yet
        self.assertListEqual([], ctx.dependency_outputs)

        # Not available yet
        self.assertListEqual([], ctx.outputs)

        # Not available yet
        self.assertListEqual([], ctx.inputs)

        # Not available yet
        self.assertListEqual([], ctx.outdated_outputs)

        # Not available yet
        self.assertListEqual([], ctx.outdated_inputs)

        self.assertEqual(ctx.name, 'task_two')

        self.assertEqual(ctx, pk.get_task_context('task_two'))
        self.assertEqual(ctx, pk.get_task_context(other_task))

        self.assertEqual(pk.get_task_context('task_one'), pk.get_task_context(task_one))

        self.assertEqual(pk.get_task_name(task_one), 'task_one')
        self.assertEqual(pk.get_task_name(other_task), 'task_two')

        self.assertEqual(pk.task_count, 5)
        self.assertEqual(len(pk.task_contexts), 5)

        with self.assertRaises(pake.UndefinedTaskException):
            pk.get_task_context('undefined')

        with self.assertRaises(pake.UndefinedTaskException):
            pk.get_task_name('undefined')

        with self.assertRaises(ValueError):
            pk.get_task_name(1)

        with self.assertRaises(ValueError):
            pk.get_task_name(None)

        with self.assertRaises(pake.RedefinedTaskException):
            pk.add_task('task_one', task_one)

        with self.assertRaises(pake.RedefinedTaskException):
            pk.add_task('task_two', other_task)

        # Raises an exception if there is an issue
        # Makes this test easier to debug
        pk.run(tasks='task_two')

        with self.assertRaises(ValueError):
            # Because jobs <= 1
            pk.run(tasks='task_two', jobs=-1)

        with self.assertRaises(ValueError):
            # Because jobs <= 1
            pk.run(tasks='task_two', jobs=0)

        with self.assertRaises(ValueError):
            # Because tasks is None
            pk.run(tasks=None)

        with self.assertRaises(ValueError):
            # Because tasks is empty
            pk.run(tasks=[])

        self.assertEqual(pake.run(pk, tasks=['task_two'], call_exit=False), 0)

        self.assertEqual(pk.run_count, 5)

    def _cyclic_exception_test(self, pake_args):
        pake.program.shutdown()

        pk = pake.init(args=pake_args)

        @pk.task
        def dep_one():
            pass

        @pk.task(dep_one)
        def task_one():
            pass

        # task_two depends on dep_one.
        # but it also depends on task_one, which in turn
        # depends on dep_one again.

        # Pake considers this a cyclic dependency, and it is (I think) the
        # only way you can write a pakefile with a cycle in it, given how
        # you must define tasks before they are referenced.

        @pk.task(task_one, dep_one)
        def task_two():
            pass

        with self.assertRaises(pake.CyclicGraphException):
            pk.run(tasks=task_two)

        self.assertEqual(pake.run(pk, tasks=task_two, call_exit=False),
                         pake.returncodes.CYCLIC_DEPENDENCY)

    def test_cyclic_exception(self):
        self._cyclic_exception_test(None)
        self._cyclic_exception_test(['--jobs', '10'])
        self._cyclic_exception_test(['--dry-run'])

    def _is_running_test(self, jobs=1):

        # Test that the is_running and threadpool properties
        # of the Pake object maintain the correct state

        class TestException(Exception):
            def __init__(self, *args):
                super().__init__(*args)

        pake.program.shutdown()

        pk = pake.init()

        self.assertEqual(pk.is_running, False)
        self.assertEqual(pk.threadpool, None)

        @pk.task
        def task_a(ctx):
            if not pk.is_running:
                raise TestException('Test failed, pk.is_running is False while pake is running.')

            if jobs == 1 and pk.threadpool:
                raise TestException('Test failed, pk.threadpool is NOT None when jobs == 1.')

            if jobs > 1 and not pk.threadpool:
                raise TestException('Test failed, pk.threadpool is None when jobs > 1.')

        try:
            pk.run(tasks=[task_a], jobs=jobs)
        except pake.TaskException as err:
            self.fail(str(err.exception))

        self.assertEqual(pk.is_running, False)
        self.assertEqual(pk.threadpool, None)

    def _is_running_exception_test(self, jobs=1):

        # Test that the state of pk.is_running and pk.threadpool
        # are correct even after pake experiences an exception inside
        # of a task

        class TestException(Exception):
            def __init__(self, *args):
                super().__init__(*args)

        pake.program.shutdown()

        pk = pake.init()

        self.assertEqual(pk.is_running, False)
        self.assertEqual(pk.threadpool, None)

        @pk.task
        def task_a(ctx):
            raise TestException()

        def task_b(ctx):
            pass

        def task_c(ctx):
            pass

        try:
            pk.run(tasks=[task_a, task_b, task_c], jobs=jobs)
        except pake.TaskException as err:
            if not isinstance(err.exception, TestException):
                self.fail('Unexpected exception "{}" in pake.is_running exception test!, '
                          'expected TestException.'
                          .format(pake.util.qualified_name(err.__name__)))
            pass
        else:
            self.fail('Expected pake.TaskException, no exception was raised!')

        self.assertEqual(pk.is_running, False)
        self.assertEqual(pk.threadpool, None)

    def _is_running_exit_test(self, jobs, exit_method):

        # Test that the state of pk.is_running and pk.threadpool
        # are correct even after pake experiences an exception inside
        # of a task

        class TestException(Exception):
            def __init__(self, *args):
                super().__init__(*args)

        pake.program.shutdown()

        pk = pake.init()

        self.assertEqual(pk.is_running, False)
        self.assertEqual(pk.threadpool, None)

        @pk.task
        def task_a(ctx):
            exit_method(pk)

        def task_b(ctx):
            pass

        def task_c(ctx):
            pass

        try:
            pk.run(tasks=[task_a, task_b, task_c], jobs=jobs)
        except pake.TaskExitException as err:
            if not isinstance(err.exception, SystemExit):
                self.fail('Unexpected exception "{}" in pake.is_running exit test!, '
                          'expected SystemExit.'
                          .format(pake.util.qualified_name(err.__name__)))
        else:
            self.fail('Expected pake.TaskExitException, no exception was raised!')

        self.assertEqual(pk.is_running, False)
        self.assertEqual(pk.threadpool, None)

    def test_is_running(self):
        self._is_running_test()
        self._is_running_test(10)
        self._is_running_exception_test()
        self._is_running_exception_test(10)

        self._is_running_exit_test(jobs=10,
                                   exit_method=lambda pk: exit(0))

        self._is_running_exit_test(jobs=1,
                                   exit_method=lambda pk: exit(0))

        self._is_running_exit_test(jobs=10,
                                   exit_method=lambda pk: pk.terminate(0))

        self._is_running_exit_test(jobs=1,
                                   exit_method=lambda pk: pk.terminate(0))
