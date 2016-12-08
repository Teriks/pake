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


# Writing basic targets


```python

import pake
import glob
import os

# Targets are registered the the pake.Make object
# returned by pake's initialization call, using the target decorator.

make = pake.init()

# Try to grab a command line define,
# in particular the value of -D CC=.. if
# it has been passed on the command line.
# CC will default to gcc in this case
#
# you can also use the syntax: make["CC"] to
# attempt to get the defines value, if it is not
# defined then it will return None.

CC = make.get_define("CC", "gcc")


# If you just have a single input/output, there is no
# need to pass a list to the targets inputs/ouputs

@make.target(inputs="foo/foo.c", outputs="foo/foo.o")
def foo(target):
    # Execute a program (gcc) and print its stdout/stderr to the
    # targets output.
    target.execute('gcc -c "{}" -o "{}"'
                   .format(target.inputs[0], target.outputs[0]))

# A way you could collect inputs for a target with the glob module..
BAR_CFILES = glob.glob("bar/*.c")

# Change the .c extension to .o
BAR_OBJECTS = [os.path.splitext(f)+".o" for f in BAR_CFILES]

# Pake can handle file change detection with multiple inputs
# and outputs, as long is there is the same amount of inputs as
# there are outputs.  If the amount of inputs is different from
# the amount of ouputs, the target is considered to be out
# of date if any input file is newer than any output file.
#
# When the amount of inputs is equal to the amount of outputs,
# pake will compare each input to its corresponding output
# and collect out of date input/outputs into target.outdated_inputs
# and target.outdated_outputs respectively
@make.target(inputs=BAR_CFILES, outputs=BAR_OBJECTS)
def bar(target):

    # zip together the outdated inputs and outputs, since they
    # corrispond to each other, this iterates of a sequence of python
    # tuple objects in the form ("input", "output")

    for i in zip(target.outdated_inputs, target.outdated_outputs):
        target.execute('gcc -c "{}" -o "{}"'
                       .format(i[0], i[1])

# This target depends on the foo and bar targets, as
# specified with the decorators 'depends' parameter,
# And only outputs "bin/baz".

# The target uses the 'info' parameter of the target
# decorator to document the target. Documentation
# can be viewed by running 'pake -ti' in the directory
# the pakefile exists in, it will list all documented targets
# with their documentation.
#
# The pake.FileHelper class (pake.fileutil.FileHelper)
# can be used to preform basic file system operations while
# printing to the targets output information about what said
# operation is doing.
@make.target(outputs="bin/baz", depends=[foo, bar],
             info="Use this to build baz")
def baz(target):
    # see: pake.fileutil.FileHelper
    file_helper = pake.FileHelper(target)

    # Create a bin directory, this won't complain if it exists already
    file_helper.makedirs("bin")

    # Execute gcc with target.execute, using the list argument form
    # instead of a string, this allows easily concatenating all the
    # immediate dependencies outputs to the command line arguments
    #
    # target.dependency_outputs contains a list of all outputs that this
    # targets immediate dependencies produce
    #
    target.execute(["gcc", "-o", target.output[0]] + target.dependency_outputs)


@make.target(info="Clean binaries")
def clean(target):
    # see: pake.fileutil.FileHelper
    file_helper = pake.FileHelper(target)

    # Clean up using a the FileHelper object
    # Remove any bin directory, this wont complain if "bin"
    # does not exist.
    file_helper.removedirs("bin")


# Run pake, the default target that will be executed when
# none is specified will be 'baz'. the default_targets parameter
# is optional, if it is not specified then you will have to specify
# which target needs to be ran on the command line when you run pake.

pake.run(make, default_targets=baz)


```

# Running pake scripts in pake

Pake is able to run itself through the use of target.run_script
or even pake.submake.run_script.  target.run_script is preferred
because it handles writing synchronized program output to the targets
output queue when multiple jobs ar running.

```python

import pake

# This is required to use pake.submake.run_script
# outside of a target
import pake.submake

make = pake.init()

# Try to get the CC define from the command line,
# default to "GCC".

CC = make.get_define("CC", "gcc")

# Export the CC variable's value to all invocations
# of pake.submake.run_script, or target.runscript here after
# as a define that can be retrieved with make.get_define()
#
pake.export("CC", CC)


# Execute outside of a target, by default the stdout/stderr
# of the subscript goes to this scripts stdout.  The file
# object to which stdout gets written to can be specified
# with pake.submake.run_script(..., stdout=(file))

pake.submake.run_script("sometasks/pakefile.py", "dotasks")

# This target does not depend on anything or have any inputs/outputs
# it will basically only run if you explicitly specify it as a default
# target in pake.run, or specify it on the command line

@make.target
def my_phony_target(target):
    # Arguments are passed in a variadic parameter...
    # Run a sub script with the same amount of jobs as this file was requested
    # to run with, also specify that the "foo" target is to be ran.
    # The scripts output is written to this targets output queue,
    # or immediately printed if pake is running a non parallel build.

    target.run_script("library/pakefile.py", "foo", "-j", make.get_max_jobs())

```

Running pake:

```bash

cd your_pakefile_directory

# Run pake with up to 10 targets running in parallel

pake -j 10

```

pake will look for "pakefile.py" or "pakefile" in the current directory and run it.

Or you can specify one or more files to run with **-f/--file**.
The switch does not have multiple arguments, but it can be used more than once to specify multiple files.

For example:

`pake -f pakefile.py foo`

`pake -f your_pakefile_1.py -f your_pakefile_2.py foo`


# Pakes current options


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




