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


class GraphTest(unittest.TestCase):
    def test_exceptions(self):

        test_case = self

        pk = pake.init()

        ran = False

        # runs because 'test' is missing
        @pk.task(i=[], o=['test'])
        def task_a(ctx):
            nonlocal ran, test_case
            ran = True
            test_case.assertTrue(len(ctx.outputs) == 1)
            test_case.assertTrue(len(ctx.outdated_outputs) == 1)
            test_case.assertTrue(ctx.outdated_outputs[0] == 'test')

        pk.run(tasks=task_a)

        self.assertTrue(ran)

        pk = pake.init()

        # ================

        pk = pake.init()

        ran = False

        # runs because 'test' is missing
        @pk.task(o=['test'])
        def task_a(ctx):
            nonlocal ran, test_case
            ran = True
            test_case.assertTrue(len(ctx.outputs) == 1)
            test_case.assertTrue(len(ctx.outdated_outputs) == 1)
            test_case.assertTrue(ctx.outdated_outputs[0] == 'test')

        pk.run(tasks=task_a)

        self.assertTrue(ran)

        # ================

        pk = pake.init()

        ran = False

        # Always runs
        @pk.task
        def task_a(ctx):
            nonlocal ran, test_case
            self.assertTrue(len(ctx.outputs) == 0)
            self.assertTrue(len(ctx.inputs) == 0)
            self.assertTrue(len(ctx.outdated_outputs) == 0)
            self.assertTrue(len(ctx.outdated_inputs) == 0)
            ran = True

        pk.run(tasks=task_a)

        self.assertTrue(ran)


        # ================

        pk = pake.init()

        ran = False

        # Always runs
        @pk.task(i=None, o=None)
        def task_a(ctx):
            nonlocal ran, test_case
            self.assertTrue(len(ctx.outputs) == 0)
            self.assertTrue(len(ctx.inputs) == 0)
            self.assertTrue(len(ctx.outdated_outputs) == 0)
            self.assertTrue(len(ctx.outdated_inputs) == 0)
            ran = True

        pk.run(tasks=task_a)

        self.assertTrue(ran)

        # ================

        pk = pake.init()

        # MissingOutputFilesException, even if 'test' does not exist on disk
        @pk.task(i=['test'], o=[])
        def task_a(ctx):
            pass

        with self.assertRaises(pake.MissingOutputFilesException):
            pk.run(tasks=task_a)

        # ================

        pk = pake.init()

        # MissingOutputFilesException, even if 'test' does not exist on disk
        @pk.task(i=['test'])
        def task_a(ctx):
            pass

        with self.assertRaises(pake.MissingOutputFilesException):
            pk.run(tasks=task_a)

        # ================

        pk = pake.init()

        # InputFileNotFoundException, since usage is valid but a.c is missing
        @pk.task(i=['a.c'], o=['a.o'])
        def task_a(ctx):
            pass

        with self.assertRaises(pake.InputFileNotFoundException):
            pk.run(tasks=task_a)

