import sys
import unittest

import os

sys.path.insert(1,
                os.path.abspath(
                    os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                 os.path.join('..', '..'))))

import pake

script_dir = os.path.dirname(os.path.realpath(__file__))


class GraphTest(unittest.TestCase):

    def _behavior_test(self, jobs):
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

        pk.run(tasks=task_a, jobs=jobs)

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

        pk.run(tasks=task_a, jobs=jobs)

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

        pk.run(tasks=task_a, jobs=jobs)

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

        pk.run(tasks=task_a, jobs=jobs)

        self.assertTrue(ran)

        # ================

        pk = pake.init()

        ran = False

        # Wont ever run
        @pk.task(i=[], o=[])
        def task_a(ctx):
            nonlocal ran
            ran = True

        pk.run(tasks=task_a, jobs=jobs)

        self.assertFalse(ran)

        # ================

        pk = pake.init()

        ran = False

        # Wont ever run
        @pk.task(i=pake.glob('*.theres_nothing_named_this_in_the_directory'), o=pake.pattern('%.o'))
        def task_a(ctx):
            nonlocal ran
            ran = True

        pk.run(tasks=task_a, jobs=jobs)

        self.assertFalse(ran)

    def _exceptions_test(self, jobs):
        test_case = self

        pk = pake.init()

        # MissingOutputFilesException, even if 'test' does not exist on disk
        @pk.task(i=['test'], o=[])
        def task_a(ctx):
            pass

        with self.assertRaises(pake.MissingOutputsException):
            pk.run(tasks=task_a, jobs=jobs)

        # ================

        pk = pake.init()

        # MissingOutputFilesException, even if 'test' does not exist on disk
        @pk.task(i=['test'])
        def task_a(ctx):
            pass

        with self.assertRaises(pake.MissingOutputsException):
            pk.run(tasks=task_a, jobs=jobs)

        # ================

        pk = pake.init()

        # InputFileNotFoundException, since usage is valid but a.c is missing
        @pk.task(i=['a.c'], o=['a.o'])
        def task_a(ctx):
            pass

        with self.assertRaises(pake.InputNotFoundException):
            pk.run(tasks=task_a, jobs=jobs)

    def test_behaviour(self):
        self._behavior_test(jobs=1)
        self._behavior_test(jobs=10)

    def test_exceptions(self):
        self._exceptions_test(jobs=1)
        self._exceptions_test(jobs=10)



