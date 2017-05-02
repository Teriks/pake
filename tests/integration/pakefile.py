#!/usr/bin/python3

import sys
import os

# the directory above tests to the path so pake can be included
# not needed if module is 'installed'
sys.path.insert(1,
    os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../../')))

import pake


pk = pake.init()

pake.export("TEST_EXPORT", "test\"test")

pake.export("TEST_EXPORT1", [1, "te\"st", [3, 4, 'test\'test']])

pake.export("TEST_EXPORT2", {0: 1, 1: "te\"st", 2: [3, 4, 'test\'test']})

pake.export("TEST_EXPORT3", {1, "te\"st", 3, 4, 'test\'test'})

pake.export("TEST_EXPORT4", (1, "te\"st", [3, 4, 'test\'test']))

pake.export("TEST_EXPORT5", "")


@pk.task(i="do_stuff_first.c", o="do_stuff_first.o")
def do_stuff_first(ctx):
    file_helper = pake.FileHelper(ctx)

    ctx.print(ctx.inputs[0])
    file_helper.copy(ctx.inputs[0], ctx.outputs[0])


@pk.task(i="do_stuff_first_2.c", o="do_stuff_first_2.o")
def do_stuff_first_2(ctx):
    file_helper = pake.FileHelper(ctx)

    ctx.print(ctx.inputs[0])
    file_helper.copy(ctx.inputs[0], ctx.outputs[0],copy_metadata=True)


# If there are an un-equal amount of inputs to outputs,
# rebuild all inputs if any input is newer than any output, or if any output file is missing.

@pk.task(i=["stuffs_one.c", "stuffs_two.c"], o="stuffs_combined.o")
def do_multiple_stuffs(ctx):
    file_helper = pake.FileHelper(ctx)

    # All inputs and outputs will be considered out of date

    for i in ctx.inputs:
        ctx.print(i)

    for o in ctx.outputs:
        file_helper.touch(o)


# Rebuild the input on the left that corresponds to the output in the same position
# on the right when that specific input is out of date, or it's output is missing.

@pk.task(i=["stuffs_three.c", "stuffs_four.c"], o=["stuffs_three.o", "stuffs_four.o"])
def do_multiple_stuffs_2(ctx):
    file_helper = pake.FileHelper(ctx)
    # Only out of date inputs/outputs will be in these collections

    # The elements correspond to each other when the number of inputs is the same
    # as the number of outputs.  ctx.outdated_input[i] is the input related to
    # the output: ctx.outdated_output[i]

    for i in zip(ctx.outdated_inputs, ctx.outdated_outputs):
        ctx.print(i[0])
        file_helper.touch(i[1])


@pk.task(
    do_stuff_first, do_stuff_first_2, do_multiple_stuffs, do_multiple_stuffs_2,
    i="do_stuff.c", o="do_stuff.o"
)
def do_stuff(ctx):
    file_helper = pake.FileHelper(ctx)

    ctx.print(ctx.inputs[0])

    file_helper.touch(ctx.outputs[0])

    # Print the collective outputs of this ctxs immediate dependencies

    ctx.print("Dependency outputs: " + str(ctx.dependency_outputs))

    # Run a pakefile.py script in a subdirectory, build 'all' task

    ctx.subpake("subpake/pakefile.py", "all")


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

    if pk["SOME_DEFINE"]:
        ctx.print(pk["SOME_DEFINE"])

    ctx.print(pk.get_define("SOME_DEFINE2", "SOME_DEFINE2_DEFAULT"))


@pk.task(i=pake.glob('glob_and_pattern_test/*.c'),o=pake.pattern('glob_and_pattern_test/%.o'))
def glob_and_pattern_test(ctx):
    file_helper = pake.FileHelper(ctx)
    for i, o in zip(ctx.outdated_inputs, ctx.outdated_inputs):
        file_helper.touch(o)


# Always runs, because there are no inputs or outputs to use for file change detection

@pk.task(do_stuff, glob_and_pattern_test, o="main")
def all(ctx):
    """Make all info test."""

    file_helper = pake.FileHelper(ctx)
    file_helper.touch(ctx.outputs[0])


# Clean .o files in directories

@pk.task
def clean(ctx):
    file_helper = pake.FileHelper(ctx)

    file_helper.glob_remove("glob_and_pattern_test/*.o")

    file_helper.glob_remove("*.o")

    file_helper.remove("main")

    file_helper.rmtree("test")
    file_helper.remove("test2")

    ctx.subpake("subpake/pakefile.py", "clean")

@pk.task
def one(ctx):
    ctx.print("ONE")

@pk.task
def two(ctx):
    ctx.print("TWO")


@pk.task
def three(ctx):
    ctx.print("THREE")





pake.run(pk, tasks=[one, two, three, print_define, all])
