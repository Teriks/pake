#!/usr/bin/python3

import sys
import unittest

import os

sys.path.insert(1,
                os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../../')))

import pake

script_dir = os.path.dirname(os.path.realpath(__file__))

# Force the test to occur in the correct place
os.chdir(script_dir)


pk = pake.init()

pake.export('TEST_EXPORT', 'test"test')

pake.export('TEST_EXPORT1', [1, 'te"st', [3, 4, "test'test"]])

pake.export('TEST_EXPORT2', {0: 1, 1: 'te"st', 2: [3, 4, "test'test"]})

pake.export('TEST_EXPORT3', {1, 'te"st', 3, 4, "test'test"})

pake.export('TEST_EXPORT4', (1, 'te"st', [3, 4, "test'test"]))

pake.export('TEST_EXPORT5', '')


@pk.task(i='test_data/do_stuff_first.c', o='test_data/do_stuff_first.o')
def do_stuff_first(ctx):
    file_helper = pake.FileHelper(ctx)

    ctx.print(ctx.inputs[0])
    file_helper.copy(ctx.inputs[0], ctx.outputs[0])


@pk.task(i='test_data/do_stuff_first_2.c', o='test_data/do_stuff_first_2.o')
def do_stuff_first_2(ctx):
    file_helper = pake.FileHelper(ctx)

    ctx.print(ctx.inputs[0])
    file_helper.copy(ctx.inputs[0], ctx.outputs[0], copy_metadata=True)


# If there are an un-equal amount of inputs to outputs,
# rebuild all inputs if any input is newer than any output, or if any output file is missing.

@pk.task(i=['test_data/stuffs_one.c', 'test_data/stuffs_two.c'], o='test_data/stuffs_combined.o')
def do_multiple_stuffs(ctx):
    file_helper = pake.FileHelper(ctx)

    # All inputs and outputs will be considered out of date

    for i in ctx.inputs:
        ctx.print(i)

    for o in ctx.outputs:
        file_helper.touch(o)


# Rebuild the input on the left that corresponds to the output in the same position
# on the right when that specific input is out of date, or it's output is missing.

@pk.task(i=['test_data/stuffs_three.c', 'test_data/stuffs_four.c'], o=['test_data/stuffs_three.o', 'test_data/stuffs_four.o'])
def do_multiple_stuffs_2(ctx):
    file_helper = pake.FileHelper(ctx)
    # Only out of date inputs/outputs will be in these collections

    # The elements correspond to each other when the number of inputs is the same
    # as the number of outputs.  ctx.outdated_input[i] is the input related to
    # the output: ctx.outdated_output[i]
    with ctx.multitask() as mt:
        for i in zip(ctx.outdated_inputs, ctx.outdated_outputs):
            mt.submit(file_helper.touch, i[1])


@pk.task(
    do_stuff_first, do_stuff_first_2, do_multiple_stuffs, do_multiple_stuffs_2,
    i='test_data/do_stuff.c', o='test_data/do_stuff.o'
)
def do_stuff(ctx):
    file_helper = pake.FileHelper(ctx)

    ctx.print(ctx.inputs[0])

    file_helper.touch(ctx.outputs[0])

    # Print the collective outputs of this ctxs immediate dependencies

    ctx.print('Dependency outputs: ' + str(ctx.dependency_outputs))

    # Run a test pakefile.py script in a subdirectory, build 'all' task
    ctx.subpake('test_data/subpake/pakefile.py', 'all')


# Basically a dummy task (if nothing actually depended on it)

@pk.task
def print_define(ctx):
    """
    Print Define info test. This is a very long info string
    which should be text wrapped to look nice on the command line
    by pythons built in textwrap module.  This long info string
    should be wrapped at 70 characters, which is the default
    value used by the textwrap module, and is similar if
    not the same wrap value used by the argparse module when
    formatting command help.
    """

    # Defines are interpreted into python literals.
    # If you pass and integer, you get an int.. string str, (True or False) a bool etc.
    # Defines that are not given a value explicitly are given the value of 'True'
    # Defines that don't exist return 'None'

    if pk['SOME_DEFINE']:
        ctx.print(pk['SOME_DEFINE'])

    ctx.print(pk.get_define('SOME_DEFINE2', 'SOME_DEFINE2_DEFAULT'))


@pk.task(i=pake.glob('test_data/glob_and_pattern/*.c'), o=pake.pattern('test_data/glob_and_pattern/%.o'))
def glob_and_pattern_test(ctx):
    file_helper = pake.FileHelper(ctx)
    for i, o in ctx.outdated_pairs:
        file_helper.touch(o)


@pk.task(i=[pake.glob('test_data/glob_and_pattern/src_a/*.c'), pake.glob('test_data/glob_and_pattern/src_b/*.c')],
         o=pake.pattern('{dir}/%.o'))
def glob_and_pattern_test2(ctx):
    file_helper = pake.FileHelper(ctx)
    with ctx.multitask() as mt:
        list(mt.map(file_helper.touch, ctx.outdated_outputs))


class FileToucher:
    def __init__(self, tag):
        self._tag = tag

    def __call__(self, ctx):
        ctx.print('Toucher {}'.format(self._tag))

        fp = pake.FileHelper(ctx)

        for i in ctx.outputs:
            fp.touch(i)


toucher_instance_a = FileToucher('A')
toucher_instance_b = FileToucher('B')

pk.add_task('toucher_class_task_a', toucher_instance_a, outputs=['test_data/toucher_class_file_1.o', 'test_data/toucher_class_file_2.o'])
pk.add_task('toucher_class_task_b', toucher_instance_b, dependencies=toucher_instance_a, outputs='test_data/toucher_class_file_3.o')


def toucher_task_func(ctx):
    fp = pake.FileHelper(ctx)

    for i in ctx.outputs:
        fp.touch(i)


pk.add_task('toucher_func_task_c', toucher_task_func, dependencies='toucher_class_task_b', outputs=['test_data/toucher_func_file_4.o'])


@pk.task(glob_and_pattern_test, i='test_data/glob_and_pattern', o='test_data/dir_cmp_test.o')
def directory_compare_test(ctx):
    # glob_and_pattern_test modifies the input folder, so this should run
    file_helper = pake.FileHelper(ctx)
    file_helper.touch(ctx.outputs[0])


@pk.task(o='test_data/directory_create_test')
def directory_create_test(ctx):
    # Create the above directory if it does not exist (directory compare test)
    file_helper = pake.FileHelper(ctx)
    file_helper.makedirs(ctx.outputs[0])


@pk.task(do_stuff, directory_compare_test, directory_create_test, glob_and_pattern_test2, 'toucher_func_task_c', o='test_data/main')
def all(ctx):
    file_helper = pake.FileHelper(ctx)
    file_helper.touch(ctx.outputs[0])


# Clean .o files in directories

@pk.task
def clean(ctx):
    file_helper = pake.FileHelper(ctx)

    file_helper.glob_remove('test_data/glob_and_pattern/*.o')
    file_helper.glob_remove('test_data/glob_and_pattern/src_a/*.o')
    file_helper.glob_remove('test_data/glob_and_pattern/src_b/*.o')

    file_helper.glob_remove('test_data/*.o')

    file_helper.remove('test_data/main')

    file_helper.rmtree('test_data/test')
    file_helper.remove('test_data/test2')

    ctx.subpake('test_data/subpake/pakefile.py', 'clean')


@pk.task
def one(ctx):
    ctx.print('ONE')


@pk.task
def two(ctx):
    ctx.print('TWO')


@pk.task
def three(ctx):
    ctx.print('THREE')

if __name__ == '__main__':
    pake.run(pk, tasks=[one, two, three, print_define, all])
    exit(0)


class IntegrationTest(unittest.TestCase):
    def _check_outputs(self, exist=True):
        fun = self.assertTrue if exist else self.assertFalse
        fun(os.path.exists(os.path.join(script_dir, "test_data", "do_stuff.o")))
        fun(os.path.exists(os.path.join(script_dir, "test_data", "do_stuff_first.o")))
        fun(os.path.exists(os.path.join(script_dir, "test_data", "do_stuff_first_2.o")))
        fun(os.path.exists(os.path.join(script_dir, "test_data", "main")))
        fun(os.path.exists(os.path.join(script_dir, "test_data", "stuffs_combined.o")))
        fun(os.path.exists(os.path.join(script_dir, "test_data", "stuffs_four.o")))
        fun(os.path.exists(os.path.join(script_dir, "test_data", "stuffs_three.o")))
        fun(os.path.exists(os.path.join(script_dir, "test_data", "toucher_class_file_1.o")))
        fun(os.path.exists(os.path.join(script_dir, "test_data", "toucher_class_file_2.o")))
        fun(os.path.exists(os.path.join(script_dir, "test_data", "toucher_class_file_3.o")))
        fun(os.path.exists(os.path.join(script_dir, "test_data", "toucher_func_file_4.o")))
        fun(os.path.exists(os.path.join(script_dir, "test_data", "subpake", "test.o")))

        fun(os.path.exists(os.path.join(script_dir, "test_data", "glob_and_pattern", "src_a", "a.o")))
        fun(os.path.exists(os.path.join(script_dir, "test_data", "glob_and_pattern", "src_a", "b.o")))
        fun(os.path.exists(os.path.join(script_dir, "test_data", "glob_and_pattern", "src_a", "c.o")))

        fun(os.path.exists(os.path.join(script_dir, "test_data", "glob_and_pattern", "src_b", "a.o")))
        fun(os.path.exists(os.path.join(script_dir, "test_data", "glob_and_pattern", "src_b", "b.o")))
        fun(os.path.exists(os.path.join(script_dir, "test_data", "glob_and_pattern", "src_b", "c.o")))

        fun(os.path.exists(os.path.join(script_dir, "test_data", "glob_and_pattern", "a.o")))
        fun(os.path.exists(os.path.join(script_dir, "test_data", "glob_and_pattern", "b.o")))
        fun(os.path.exists(os.path.join(script_dir, "test_data", "glob_and_pattern", "c.o")))

        fun(os.path.exists(os.path.join(script_dir, "test_data", "dir_cmp_test.o")))

    def test_integrated(self):
        print('===== STARTING INTEGRATION TEST =====')

        fh = pake.FileHelper()
        fh.glob_remove(os.path.join(script_dir, '**', '*.o'))
        fh.remove(os.path.join(script_dir, 'test_data', 'main'))

        self.assertEqual(pake.run(pk, tasks=[one, two, three, print_define, all], call_exit=False), 0)

        self._check_outputs()

        self.assertEqual(pake.run(pk, tasks=[clean], call_exit=False), 0)

        self._check_outputs(exist=False)

        print('===== FINISHED INTEGRATION TEST =====')

    def test_integrated_parallel(self):
        print('===== STARTING PARALLEL INTEGRATION TEST ====='+os.linesep)

        fh = pake.FileHelper()
        fh.glob_remove(os.path.join(script_dir, '**', '*.o'))
        fh.remove(os.path.join(script_dir, 'test_data', 'main'))

        self.assertEqual(pake.run(pk, tasks=[one, two, three, print_define, all], jobs=10, call_exit=False), 0)

        self._check_outputs()

        self.assertEqual(pake.run(pk, tasks=clean, jobs=10, call_exit=False), 0)

        self._check_outputs(exist=False)

        print('===== FINISHED PARALLEL INTEGRATION TEST =====')
