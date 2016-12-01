#!/usr/bin/python3

import sys
import os
import glob


# the directory above tests to the path so pake can be included
# not needed if module is 'installed'
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../../')))


import pake


make = pake.init()


print(make["LIST"])
print(make["DICT"])
print(make["SET"])
print(make["TUP"])


pake.export("TEST_EXPORT", "test\"test")

pake.export("TEST_EXPORT1", [1,"te\"st", [3, 4, 'test\'test']])

pake.export("TEST_EXPORT2", {0 : 1, 1: "te\"st", 2: [3, 4, 'test\'test']})

pake.export("TEST_EXPORT3", {1,"te\"st", 3, 4, 'test\'test'})

pake.export("TEST_EXPORT4", (1,"te\"st", [3, 4, 'test\'test']))


@make.target(inputs="do_stuff_first.c", outputs="do_stuff_first.o")
def do_stuff_first(target):
    print(target.input)
    pake.touch(target.output)


@make.target(inputs="do_stuff_first_2.c", outputs="do_stuff_first_2.o")
def do_stuff_first_2(target):
    print(target.input)
    pake.touch(target.output)


# If there are an un-equal amount of inputs to outputs,
# rebuild all inputs if any input is newer than any output, or if any output file is missing.

@make.target(inputs=["stuffs_one.c", "stuffs_two.c"], outputs="stuffs_combined.o")
def do_multiple_stuffs(target):
    # All inputs and outputs will be considered out of date

    for i in target.inputs:
        print(i)

    for o in target.outputs:
        pake.touch(o)


# Rebuild the input on the left that corresponds to the output in the same position on the right when
# that specific input is out of date, or it's output is missing.

@make.target(inputs=["stuffs_three.c", "stuffs_four.c"], outputs=["stuffs_three.o", "stuffs_four.o"])
def do_multiple_stuffs_2(target):
    # Only out of date inputs/outputs will be in these collections

    # The elements correspond to each other when the number of inputs is the same as the number of outputs.
    # target.outdated_input[i] is the input related to the output: target.outdated_output[i]

    for i in target.outdated_inputs:
        print(i)

    for o in target.outdated_outputs:
        pake.touch(o)


@make.target(inputs="do_stuff.c", outputs="do_stuff.o",
             depends=[do_stuff_first, do_stuff_first_2, do_multiple_stuffs, do_multiple_stuffs_2])
def do_stuff(target):
    print(target.input)
    pake.touch(target.output)

    # Print the collective outputs of this targets immediate dependencies

    print("Dependency outputs: "+str(target.dependency_outputs))

    # Run a pakefile.py script in a subdirectory, build 'all' target

    pake.run_script("submake/pakefile.py", "all")



# Basically a dummy target (if nothing actually depended on it)

@make.target
def print_define():

    # Defines are interpreted into python literals.
    # If you pass and integer, you get an int.. string str, (True or False) a bool etc.
    # Defines that are not given a value explicitly are given the value of 'True'
    # Defines that don't exist return 'None'

    if make["SOME_DEFINE"]:
        print(make["SOME_DEFINE"])

    print(make.get_define("SOME_DEFINE2", "SOME_DEFINE2_DEFAULT"))



# Always runs, because there are no inputs or outputs to use for file change detection

@make.target(depends=[do_stuff, print_define])
def all():
    print("Finished doing stuff! nothing more to do.")



# Clean .o files in the directory

@make.target
def clean():
    for i in glob.glob("*.o"):
        os.unlink(i)

    pake.run_script("submake/pakefile.py", "clean")



pake.run(make, default_targets=all)