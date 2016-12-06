# About pake

[![Documentation Status](https://readthedocs.org/projects/pake/badge/?version=latest)](http://pake.readthedocs.io/en/latest/?badge=latest)

pake is a make like python build utility where targets, dependencies and build commands
can be expressed entirely in python, similar to ruby rake.

pake supports automatic file change detection when dealing with inputs and outputs and also
parallel builds.

===

Do not use me I am still in the kiln

How to use me anyway:

`pip install git+git://github.com/Teriks/pake.git@master`

Uninstall prior to updating.


# Small Example


```python

#!/usr/bin/python3

import sys
import os
import glob
import pake


make = pake.init()


# Export python literals as defines to scripts ran with target.run_script.

pake.export("SOME_EXPORTED_DEFINE", ["a", "b", "c"])
pake.export("SOME_EXPORTED_DEFINE2", 4)


# Prevent SOME_EXPORTED_DEFINE2 from being exported.

pake.un_export("SOME_EXPORTED_DEFINE2")


@make.target(inputs="do_stuff_first.c", outputs="do_stuff_first.o")
def do_stuff_first(target):
    target.print(target.inputs[0])
    pake.touch(target.outputs[0])


@make.target(inputs="do_stuff_first_2.c", outputs="do_stuff_first_2.o")
def do_stuff_first_2(target):
    target.print(target.inputs[0])
    pake.touch(target.outputs[0])


# If there are an un-equal amount of inputs to outputs,
# rebuild all inputs if any input is newer than any output, or if any output file is missing.

@make.target(inputs=["stuffs_one.c", "stuffs_two.c"], outputs="stuffs_combined.o")
def do_multiple_stuffs(target):
    # All inputs and outputs will be considered out of date

    for i in target.inputs:
        target.print(i)

    for o in target.outputs:
        pake.touch(o)


# Rebuild the input on the left that corresponds to the output in the same position
# on the right when that specific input is out of date, or it's output is missing.

@make.target(inputs=["stuffs_three.c", "stuffs_four.c"], outputs=["stuffs_three.o", "stuffs_four.o"])
def do_multiple_stuffs_2(target):
    # Only out of date inputs/outputs will be in these collections

    # The elements correspond to each other when the number of inputs is the same
    # as the number of outputs.  target.outdated_input[i] is the input related to
    # the output: target.outdated_output[i]

    for i in zip(target.outdated_inputs, target.outdated_outputs):
        target.print(i[0])
        pake.touch(i[1])


@make.target(inputs="do_stuff.c", outputs="do_stuff.o",
             depends=[do_stuff_first, do_stuff_first_2, do_multiple_stuffs, do_multiple_stuffs_2])
def do_stuff(target):
    target.print(target.inputs[0])

    pake.touch(target.outputs[0])

    # Print the collective outputs of this targets immediate dependencies

    target.print("Dependency outputs: " + str(target.dependency_outputs))

    # Run a pakefile.py script in a subdirectory, build 'all' target

    target.run_script("submake/pakefile.py", "all")


# Basically a dummy target (if nothing actually depended on it)

@make.target(info="Print Define info test. This is a very long info string "
                  "which should be text wrapped to look nice on the command line "
                  "by pythons built in textwrap module.  This long info string"
                  "should be wrapped at 70 characters, which is the default "
                  "value used by the textwrap module, and is similar if "
                  "not the same wrap value used by the argparse module when "
                  "formatting command help.")
def print_define(target):
    # Defines are interpreted into python literals.
    # If you pass and integer, you get an int.. string str, (True or False) a bool etc.
    # Defines that are not given a value explicitly are given the value of 'True'
    # Defines that don't exist return 'None'

    if make["SOME_DEFINE"]:
        target.print(make["SOME_DEFINE"])

    target.print(make.get_define("SOME_DEFINE2", "SOME_DEFINE2_DEFAULT"))


# Always runs, because there are no inputs or outputs to use for file change detection

@make.target(depends=[do_stuff, print_define],
             info="Make all info test.")
def all(target):
    target.print("Finished doing stuff! nothing more to do.")


# Clean .o files in the directory

@make.target
def clean(target):
    for i in glob.glob("*.o"):
        os.unlink(i)

    target.run_script("submake/pakefile.py", "clean")


pake.run(make, default_targets=all)


```

And for example, to run:

```

cd your_pakefile_directory
pake all -DSOME_DEFINE="test"

```

pake will look for "pakefile.py" or "pakefile" in the current directory and run it.

Or you can specify one or more files to run with *-f/--file*:


`pake -f your_pakefile.py all -DSOME_DEFINE="test"`


# Current Options

`pake -h`


Gives:

```

usage: pake [-h] [-v] [-j NUM_JOBS] [-n] [-t] [-ti] [-D DEFINE] [-C DIRECTORY]
            [-f FILE]
            [targets [targets ...]]

positional arguments:
  targets               Build targets.

optional arguments:
  -h, --help            show this help message and exit
  -v, --version         show program's version number and exit
  -j NUM_JOBS, --jobs NUM_JOBS
                        Max number of parallel jobs. Using this option enables
                        unrelated targets to run in parallel with a max of N
                        targets running at a time.
  -n, --dry-run         Use to preform a dry run, lists all targets that will
                        be executed in the next actual invocation.
  -t, --targets         List all target names.
  -ti, --targets-info   List all targets which have info strings provided,
                        with their info string.
  -D DEFINE, --define DEFINE
                        Add defined value.
  -C DIRECTORY, --directory DIRECTORY
                        Change directory before executing.
  -f FILE, --file FILE  Pakefile path(s). This switch can be used more than
                        once, all specified pakefiles will be executed in
                        order.


```




