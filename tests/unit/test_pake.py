import sys
import unittest

import os

sys.path.insert(1,
                os.path.abspath(
                    os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                 os.path.join('..', '..'))))

import pake
import pake.program
import pake.util


class PakeTest(unittest.TestCase):

    def test_registration(self):

        pake.program.shutdown()

        pk = pake.init()

        script_path = os.path.dirname(os.path.abspath(__file__))

        in1 = os.path.join(script_path, 'test_data', 'in1')
        out1 = os.path.join(script_path, 'test_data', 'out1')

        pake.util.touch(in1)

        in2 = os.path.join(script_path, 'test_data', 'in2')
        out2 = os.path.join(script_path, 'test_data', 'out2')

        pake.util.touch(in2)

        @pk.task(i=in1, o=out1)
        def task_one(ctx):
            nonlocal self
            self.assertListEqual(ctx.inputs, [in1])
            self.assertListEqual(ctx.outputs, [out1])

        def other_task(ctx):
            nonlocal self
            self.assertListEqual(ctx.inputs, [in2])
            self.assertListEqual(ctx.outputs, [out2])

        ctx = pk.add_task('task_two', other_task, inputs=in2, outputs=out2, dependencies=task_one)

        self.assertEqual(ctx.name, 'task_two')

        self.assertEqual(ctx, pk.get_task_context('task_two'))
        self.assertEqual(ctx, pk.get_task_context(other_task))

        self.assertEqual(pk.get_task_context('task_one'), pk.get_task_context(task_one))

        self.assertEqual(pk.get_task_name(task_one), 'task_one')
        self.assertEqual(pk.get_task_name(other_task), 'task_two')

        self.assertEqual(pk.task_count, 2)
        self.assertEqual(len(pk.task_contexts), 2)

        self.assertEqual(pake.run(pk, tasks=['task_two'], call_exit=False), 0)

        self.assertEqual(pk.run_count, 2)