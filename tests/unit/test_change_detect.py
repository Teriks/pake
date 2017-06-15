import sys
import unittest

import os

script_dir = os.path.dirname(os.path.realpath(__file__))

sys.path.insert(1, os.path.abspath(
                   os.path.join(script_dir, os.path.join('..', '..'))))

import pake


class GraphTest(unittest.TestCase):

    def _basic_behavior_test(self, jobs):

        pake.program.shutdown()
        pk = pake.init()

        ran = False

        # runs because 'test' is missing
        @pk.task(i=[], o=['test'])
        def task_a(ctx):
            nonlocal ran, self
            ran = True
            self.assertTrue(len(ctx.outputs) == 1)
            self.assertTrue(len(ctx.outdated_outputs) == 1)
            self.assertTrue(ctx.outdated_outputs[0] == 'test')

        pk.run(tasks=task_a, jobs=jobs)

        self.assertTrue(ran)

        # ================

        pake.program.shutdown()
        pk = pake.init()

        ran = False

        # runs because 'test' is missing
        @pk.task(o=['test'])
        def task_a(ctx):
            nonlocal ran, self
            ran = True
            self.assertTrue(len(ctx.outputs) == 1)
            self.assertTrue(len(ctx.outdated_outputs) == 1)
            self.assertTrue(ctx.outdated_outputs[0] == 'test')

        pk.run(tasks=task_a, jobs=jobs)

        self.assertTrue(ran)

        # ================

        pake.program.shutdown()
        pk = pake.init()

        ran = False

        # Always runs
        @pk.task
        def task_a(ctx):
            nonlocal ran, self
            self.assertTrue(len(ctx.outputs) == 0)
            self.assertTrue(len(ctx.inputs) == 0)
            self.assertTrue(len(ctx.outdated_outputs) == 0)
            self.assertTrue(len(ctx.outdated_inputs) == 0)
            ran = True

        pk.run(tasks=task_a, jobs=jobs)

        self.assertTrue(ran)

        # ================

        pake.program.shutdown()
        pk = pake.init()

        ran = False

        # Always runs
        @pk.task(i=None, o=None)
        def task_a(ctx):
            nonlocal ran, self
            self.assertTrue(len(ctx.outputs) == 0)
            self.assertTrue(len(ctx.inputs) == 0)
            self.assertTrue(len(ctx.outdated_outputs) == 0)
            self.assertTrue(len(ctx.outdated_inputs) == 0)
            ran = True

        pk.run(tasks=task_a, jobs=jobs)

        self.assertTrue(ran)

        # ================

        pake.program.shutdown()
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

        pake.program.shutdown()
        pk = pake.init()

        ran = False

        # Wont ever run
        @pk.task(i=pake.glob('*.theres_nothing_named_this_in_the_directory'), o=pake.pattern('%.o'))
        def task_a(ctx):
            nonlocal ran
            ran = True

        pk.run(tasks=task_a, jobs=jobs)

        self.assertFalse(ran)

    def _existing_files_test(self, jobs):

        # Test file comparisons when outputs already exist

        in1 = os.path.join(script_dir, 'test_data', 'in1')
        in2 = os.path.join(script_dir, 'test_data', 'in2')
        out1 = os.path.join(script_dir, 'test_data', 'out1')
        out2 = os.path.join(script_dir, 'test_data', 'out2')

        # ================

        pake.program.shutdown()
        pk = pake.init()

        ran = False

        # Make all the modification times ancient

        os.utime(in1, (0, 0))
        os.utime(in2, (0, 0))
        os.utime(out1, (0, 0))
        os.utime(out2, (0, 0))

        # Make an input recent

        pake.FileHelper().touch(in1)

        # This should run
        @pk.task(i=[in1, in2], o=out1)
        def task_a(ctx):
            nonlocal ran
            ran = True

        pk.run(tasks=task_a, jobs=jobs)

        self.assertTrue(ran)

        # ================

        # Same test as above, except with multiple outputs

        pake.program.shutdown()
        pk = pake.init()

        ran = False

        # Make all the modification times ancient

        os.utime(in1, (0, 0))
        os.utime(in2, (0, 0))
        os.utime(out1, (0, 0))
        os.utime(out2, (0, 0))

        # Make an input recent

        pake.FileHelper().touch(in2)

        # This should run
        @pk.task(i=[in1, in2], o=[out1, out2])
        def task_a(ctx):
            nonlocal ran
            ran = True

        pk.run(tasks=task_a, jobs=jobs)

        self.assertTrue(ran)

    def _exceptions_test(self, jobs):

        pake.program.shutdown()
        pk = pake.init()

        # MissingOutputFilesException, even if 'test' does not exist on disk
        @pk.task(i=['test'], o=[])
        def task_a(ctx):
            pass

        with self.assertRaises(pake.MissingOutputsException):
            pk.run(tasks=task_a, jobs=jobs)

        # ================

        pake.program.shutdown()
        pk = pake.init()

        # MissingOutputFilesException, even if 'test' does not exist on disk
        @pk.task(i=['test'])
        def task_a(ctx):
            pass

        with self.assertRaises(pake.MissingOutputsException):
            pk.run(tasks=task_a, jobs=jobs)

        # ================

        pake.program.shutdown()
        pk = pake.init()

        # MissingOutputFilesException, even if 'test' and 'test2' do not exist on disk
        @pk.task(i=['test', 'test2'])
        def task_a(ctx):
            pass

        with self.assertRaises(pake.MissingOutputsException):
            pk.run(tasks=task_a, jobs=jobs)

        # ================

        pake.program.shutdown()
        pk = pake.init()

        # InputFileNotFoundException, since usage is valid but a.c is missing
        @pk.task(i=['a.c'], o=['a.o'])
        def task_a(ctx):
            pass

        with self.assertRaises(pake.InputNotFoundException):
            pk.run(tasks=task_a, jobs=jobs)

        # ================

        pake.program.shutdown()
        pk = pake.init()

        # Check the same case above, but this time the output exists
        @pk.task(i=['a.c'], o=os.path.join(script_dir, 'test_data', 'out1'))
        def task_a(ctx):
            pass

        with self.assertRaises(pake.InputNotFoundException):
            pk.run(tasks=task_a, jobs=jobs)

        # ================

        pake.program.shutdown()
        pk = pake.init()

        # Check the same case as above but with multiple inputs
        @pk.task(i=['a.c', 'b.c'], o=['a.o'])
        def task_a(ctx):
            pass

        with self.assertRaises(pake.InputNotFoundException):
            pk.run(tasks=task_a, jobs=jobs)

        # ================

        pake.program.shutdown()
        pk = pake.init()

        # Check the same case as above but the output exists this time around.
        @pk.task(i=['a.c', 'b.c'],
                 o=os.path.join(script_dir, 'test_data', 'out1'))
        def task_a(ctx):
            pass

        with self.assertRaises(pake.InputNotFoundException):
            pk.run(tasks=task_a, jobs=jobs)

        # ================

        pake.program.shutdown()
        pk = pake.init()

        # Check the same case as above but with multiple inputs and outputs,
        # one of the outputs exists this time around.
        @pk.task(i=['a.c', 'b.c'],
                 o=['a.o', os.path.join(script_dir, 'test_data', 'out1')])
        def task_a(ctx):
            pass

        with self.assertRaises(pake.InputNotFoundException):
            pk.run(tasks=task_a, jobs=jobs)

        # ================

        pake.program.shutdown()
        pk = pake.init()

        # Check the same case as above but this time both outputs don't exist
        @pk.task(i=['a.c', 'b.c'],
                 o=['a.o', 'b.o'])
        def task_a(ctx):
            pass

        with self.assertRaises(pake.InputNotFoundException):
            pk.run(tasks=task_a, jobs=jobs)

    def test_changedetect(self):
        self._basic_behavior_test(jobs=1)
        self._basic_behavior_test(jobs=10)

        self._existing_files_test(jobs=1)
        self._existing_files_test(jobs=10)

    def test_exceptions(self):
        self._exceptions_test(jobs=1)
        self._exceptions_test(jobs=10)



