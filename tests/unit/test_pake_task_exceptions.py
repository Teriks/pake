import sys
import unittest

import os

sys.path.insert(1,
                os.path.abspath(
                    os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                 os.path.join('..', '..'))))

import pake
import pake.conf

script_dir = os.path.dirname(os.path.realpath(__file__))


from tests import open_devnull
pake.conf.stdout = open_devnull() if pake.conf.stdout is sys.stdout else pake.conf.stdout
pake.conf.stderr = open_devnull() if pake.conf.stderr is sys.stderr else pake.conf.stderr


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
                call(sys.executable, os.path.join(script_dir, 'throw.py'), ignore_errors=True)  # ignore exception

            try:
                pk.run(tasks=call3)
            except pake.TaskException as err:
                self.fail('TaskContext.{} threw on non zero return code with ignore_errors=True'.format(method))

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

        subprocess_test_helper('call')
        subprocess_test_helper('check_call')
        subprocess_test_helper('check_output')


if __name__ == 'main':
    unittest.main()
