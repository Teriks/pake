import sys
import unittest

import os

sys.path.insert(1,
                os.path.abspath(
                    os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                 os.path.join('..', '..'))))

import pake
import pake.conf

pake.conf.stdout = open(os.devnull, 'w')
pake.conf.stderr = open(os.devnull, 'w')

script_dir = os.path.dirname(os.path.realpath(__file__))


class IntegrationTest(unittest.TestCase):
    def test_task_exceptions(self):
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

        with self.assertRaises(pake.TaskException) as cm:
            pk.run(tasks=a_task)

        self.assertTrue(type(cm.exception.exception) == Exception)

        with self.assertRaises(pake.TaskException) as cm:
            pk.run(tasks=a_task, jobs=10)

        self.assertTrue(type(cm.exception.exception) == Exception)

        def raise_exception(*args):
            raise Exception()

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

        with self.assertRaises(pake.TaskException) as cm:
            pk.run(tasks=a_task)

        self.assertTrue(type(cm.exception.exception) == Exception)

        with self.assertRaises(pake.TaskException) as cm:
            pk.run(tasks=a_task, jobs=10)

        self.assertTrue(type(cm.exception.exception) == Exception)

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

        with self.assertRaises(pake.TaskException) as cm:
            pk.run(tasks=a_task)

        self.assertTrue(type(cm.exception.exception) == Exception)

        with self.assertRaises(pake.TaskException) as cm:
            pk.run(tasks=a_task, jobs=10)

        self.assertTrue(type(cm.exception.exception) == Exception)


if __name__ == 'main':
    unittest.main()
