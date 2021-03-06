import sys
import unittest
import os
import time

script_dir = os.path.dirname(os.path.realpath(__file__))

sys.path.insert(1, os.path.abspath(
    os.path.join(script_dir, os.path.join('..', '..'))))

import pake
import pake.conf
import pake.pake

from tests import open_devnull

pake.conf.stdout = open_devnull()
pake.conf.stderr = open_devnull()


class TaskExceptionsTest(unittest.TestCase):
    def test_task_exceptions(self):
        # =============================

        pk = pake.init()

        @pk.task
        def c_task(ctx):
            pass

        @pk.task
        def b_task(ctx):
            raise Exception()

        @pk.task(b_task, c_task)
        def a_task(ctx):
            pass

        with self.assertRaises(pake.TaskException) as exc:
            pk.run(tasks=a_task)

        self.assertEqual(type(exc.exception.exception), Exception)

        with self.assertRaises(pake.TaskException) as exc:
            pk.run(tasks=a_task, jobs=10)

        self.assertEqual(type(exc.exception.exception), Exception)

        def raise_exception(*args):
            raise Exception()

        # =============================

        pk = pake.init()

        @pk.task
        def c_task(ctx):
            pass

        @pk.task
        def b_task(ctx):
            with ctx.multitask() as mt:
                mt.submit(raise_exception)

        @pk.task(b_task, c_task)
        def a_task(ctx):
            pass

        with self.assertRaises(pake.TaskException) as exc:
            pk.run(tasks=a_task)

        self.assertEqual(type(exc.exception.exception), Exception)

        with self.assertRaises(pake.TaskException) as exc:
            pk.run(tasks=a_task, jobs=10)

        self.assertEqual(type(exc.exception.exception), Exception)

        # =============================

        pk = pake.init()

        @pk.task
        def c_task(ctx):
            pass

        @pk.task
        def b_task(ctx):
            with ctx.multitask() as mt:
                list(mt.map(raise_exception, ['test']))

        @pk.task(b_task, c_task)
        def a_task(ctx):
            pass

        with self.assertRaises(pake.TaskException) as exc:
            pk.run(tasks=a_task)

        self.assertEqual(type(exc.exception.exception), Exception)

        with self.assertRaises(pake.TaskException) as exc:
            pk.run(tasks=a_task, jobs=10)

        self.assertEqual(type(exc.exception.exception), Exception)

    def test_subprocess_task_exceptions(self):
        # =============================

        pk = pake.init()

        @pk.task
        def subpake1(ctx):
            ctx.subpake()  # ValueError

        @pk.task
        def subpake2(ctx):
            ctx.subpake('missing file')  # FileNotFound

        with self.assertRaises(pake.TaskException) as exc:
            pk.run(tasks=subpake1)

        self.assertEqual(type(exc.exception.exception), ValueError)

        with self.assertRaises(pake.TaskException) as exc:
            pk.run(tasks=subpake1, jobs=10)

        self.assertEqual(type(exc.exception.exception), ValueError)

        with self.assertRaises(pake.TaskException) as exc:
            pk.run(tasks=subpake2)

            self.assertEqual(type(exc.exception.exception), FileNotFoundError)

        with self.assertRaises(pake.TaskException) as exc:
            pk.run(tasks=subpake2, jobs=10)

        self.assertEqual(type(exc.exception.exception), FileNotFoundError)

        # =============================

        def subprocess_test_helper(method):
            pk = pake.init()

            @pk.task
            def call1(ctx):
                getattr(ctx, method)()  # ValueError

            @pk.task
            def call2(ctx):
                getattr(ctx, method)('missing file')  # FileNotFound

            @pk.task
            def call3(ctx):
                call = getattr(ctx, method)
                call(sys.executable, os.path.join(script_dir, 'throw.py'))  # Raise pake.TaskSubprocessException

            @pk.task
            def call4(ctx):
                call = getattr(ctx, method)
                call(sys.executable, os.path.join(script_dir, 'throw.py'), ignore_errors=True)  # ignore exception

            with self.assertRaises(pake.TaskException) as exc:
                pk.run(tasks=call1)

            self.assertEqual(type(exc.exception.exception), ValueError)

            with self.assertRaises(pake.TaskException) as exc:
                pk.run(tasks=call1, jobs=10)

            self.assertEqual(type(exc.exception.exception), ValueError)

            with self.assertRaises(pake.TaskException) as exc:
                pk.run(tasks=call2)

            self.assertEqual(type(exc.exception.exception), FileNotFoundError)

            with self.assertRaises(pake.TaskException) as exc:
                pk.run(tasks=call2, jobs=10)

            self.assertEqual(type(exc.exception.exception), FileNotFoundError)

            # Test pake.TaskSubprocessException propagation

            with self.assertRaises(pake.TaskException) as exc:
                pk.run(tasks=call3)

            self.assertEqual(type(exc.exception.exception), pake.TaskSubprocessException)

            exc.exception.exception.write_info(pake.conf.stdout)  # avoid unit test resource warning

            with self.assertRaises(pake.TaskException) as exc:
                pk.run(tasks=call3, jobs=10)

            self.assertEqual(type(exc.exception.exception), pake.TaskSubprocessException)

            exc.exception.exception.write_info(pake.conf.stdout)  # avoid unit test resource warning

            try:
                pk.run(tasks=call4)
            except pake.TaskException:
                self.fail('TaskContext.{} threw on non zero return code with ignore_errors=True'.format(method))

            try:
                pk.run(tasks=call4, jobs=10)
            except pake.TaskException:
                self.fail(
                    'TaskContext.{} threw on non zero return code with ignore_errors=True. with pk.run(jobs=10)'.format(
                        method))

        subprocess_test_helper('call')
        subprocess_test_helper('check_call')
        subprocess_test_helper('check_output')

        def collect_output_test_helper(jobs):
            pk = pake.init()

            @pk.task
            def call1(ctx):
                ctx.call(sys.executable, os.path.join(script_dir, 'throw.py'), collect_output=True)  # Raise pake.TaskSubprocessException

            # Test pake.TaskSubprocessException propagation

            with self.assertRaises(pake.TaskException) as exc:
                pk.run(tasks=call1, jobs=jobs)

            self.assertEqual(type(exc.exception.exception), pake.TaskSubprocessException)

            self.assertEqual(exc.exception.exception.output_stream.tell(), 0)

            # Just to test for exceptions writing the TaskSubprocessException.output prop
            exc.exception.exception.write_info(pake.conf.stdout)

            self.assertEqual(exc.exception.exception.output_stream, None)

        collect_output_test_helper(1)
        collect_output_test_helper(5)

    def test_task_exit_exception(self):

        pake.de_init(clear_conf=False)

        pk = pake.init()

        @pk.task
        def test(ctx):
            time.sleep(0.5)
            exit(100)

        @pk.task
        def test2(ctx):
            time.sleep(0.3)

        @pk.task
        def test3(ctx):
            time.sleep(0.2)

        # Make sure that exit() effects even multithreaded builds

        # The return code with call_exit=False should match the exit code in the task

        self.assertEqual(pake.run(pk, tasks=[test2, test3, test], jobs=10, call_exit=False), 100)

        self.assertEqual(pake.run(pk, tasks=[test2, test3, test], call_exit=False), 100)

        with self.assertRaises(pake.TaskExitException) as exc:
            pk.run(tasks=[test2, test3, test])

        self.assertEqual(type(exc.exception.exception), SystemExit)

        self.assertEqual(exc.exception.task_name, 'test')
        self.assertEqual(exc.exception.return_code, 100)

    def test_task_terminate_exception(self):

        pake.de_init(clear_conf=False)

        pk = pake.init()

        @pk.task
        def test(ctx):
            time.sleep(0.5)
            pk.terminate(return_code=100)

        @pk.task
        def test2(ctx):
            time.sleep(0.3)

        @pk.task
        def test3(ctx):
            time.sleep(0.2)

        # Make sure that terminate() effects even multithreaded builds

        # The return code with call_exit=False should match the exit code in the task

        self.assertEqual(pake.run(pk, tasks=[test2, test3, test], jobs=10, call_exit=False), 100)

        self.assertEqual(pake.run(pk, tasks=[test2, test3, test], call_exit=False), 100)

        with self.assertRaises(pake.TaskExitException) as exc:
            pk.run(tasks=[test2, test3, test])

        self.assertEqual(type(exc.exception.exception), pake.TerminateException)

        self.assertEqual(exc.exception.task_name, 'test')
        self.assertEqual(exc.exception.return_code, 100)


if __name__ == 'main':
    unittest.main()
