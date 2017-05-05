# About pake

[![Documentation Status](https://readthedocs.org/projects/pake/badge/?version=latest)](http://pake.readthedocs.io/en/latest/?badge=latest)

pake is a make like python build utility where tasks, dependencies and build commands
can be expressed entirely in python, similar to ruby rake.

pake supports automatic file change detection when dealing with inputs and outputs and also
parallel builds.

pake requires python3.4+

# Installing

Do not use me I am still in the kiln

How to use me anyway:

`pip install git+git://github.com/Teriks/pake.git@master`

Uninstall prior to updating.


# Example project using pake


I am using libasm_io to help test pake and have included a pakefile
build along side the makefiles in that project.

https://github.com/Teriks/libasm_io


# Writing basic tasks


```python

import pake

# Tasks are registered the the pake.Pake object
# returned by pake's initialization call, using the task decorator.

pk = pake.init()

# Try to grab a command line define,
# in particular the value of -D CC=.. if
# it has been passed on the command line.
# CC will default to gcc in this case
#
# you can also use the syntax: pk["CC"] to
# attempt to get the defines value, if it is not
# defined then it will return None.

CC = pk.get_define("CC", "gcc")


# If you just have a single input/output, there is no
# need to pass a list to the tasks inputs/outputs

@pk.task(i="foo/foo.c", o="foo/foo.o")
def foo(ctx):
    # Execute a program (gcc) and print its stdout/stderr to the tasks output.
    ctx.call('gcc -c "{}" -o "{}"'
             .format(ctx.inputs[0], ctx.outputs[0]))


# Pake can handle file change detection with multiple inputs
# and outputs. If the amount of inputs is different from
# the amount of outputs, the task is considered to be out
# of date if any input file is newer than any output file.
#
# When the amount of inputs is equal to the amount of outputs,
# pake will compare each input to its corresponding output
# and collect out of date input/outputs into ctx.outdated_inputs
# and ctx.outdated_outputs respectively
@pk.task(i=pake.glob("bar/*.c"), o=pake.pattern('bar/%.o'))
def bar(ctx):

    # zip together the outdated inputs and outputs, since they
    # correspond to each other, this iterates of a sequence of python
    # tuple objects in the form ("input", "output")

    for i, o in zip(ctx.outdated_inputs, ctx.outdated_outputs):
        ctx.call('gcc -c "{}" -o "{}"'.format(i, o))

# This task depends on the foo and bar tasks, as
# specified with the decorators leading parameters,
# And only outputs "bin/baz" by taking the input "main.c"
# and linking it to the object files produced in the other tasks.

# Documentation strings can be viewed by running 'pake -ti' in 
# the directory the pakefile exists in, it will list all documented
# tasks with their python doc strings.
#
# The pake.FileHelper class (pake.fileutil.FileHelper)
# can be used to preform basic file system operations while
# printing to the tasks output information about what said
# operation is doing.
@pk.task(foo, bar, o="bin/baz", i="main.c")
def baz(ctx):
    """Use this to build baz"""
    
    # see: pake.fileutil.FileHelper
    file_helper = pake.FileHelper(ctx)

    # Create a bin directory, this won't complain if it exists already
    file_helper.makedirs("bin")

    # Execute gcc with ctx.call, using the list argument form
    # instead of a string, this allows easily concatenating all the
    # immediate dependencies outputs to the command line arguments
    #
    # ctx.dependency_outputs contains a list of all outputs that this
    # tasks immediate dependencies produce
    #
    ctx.call(["gcc", "-o", ctx.outputs[0]] + ctx.inputs + ctx.dependency_outputs)


@pk.task
def clean(ctx):
    """Clean binaries"""
    
    # see: pake.fileutil.FileHelper
    file_helper = pake.FileHelper(ctx)

    # Clean up using a the FileHelper object
    # Remove any bin directory, this wont complain if "bin"
    # does not exist.
    file_helper.rmtree("bin")

    # Glob remove object files from the foo and bar directories
    file_helper.glob_remove("foo/*.o")
    file_helper.glob_remove("bar/*.o")


# Run pake, the default task that will be executed when
# none are specified will be 'baz'. the tasks parameter
# is optional, if it is not specified then you will have to specify
# which tasks need to be run on the command line.

pake.run(pk, tasks=baz)


```

Output from the example above:

```

===== Executing task: "bar"
gcc -c "bar/bar.c" -o "bar/bar.o"
===== Executing task: "foo"
gcc -c "foo/foo.c" -o "foo/foo.o"
===== Executing task: "baz"
Created Directory(s): "bin"
gcc -o bin/baz main.c foo/foo.o bar/bar.o


```

# Running pake scripts in pake

Pake is able to run itself through the use of ctx.subpake
or even pake.subpake.  ctx.subpake is preferred
because it handles writing program output to the tasks
output queue in a synchronized manner when multiple jobs are running.

```python

import pake

pk = pake.init()

# Try to get the CC define from the command line,
# default to "GCC".

CC = pk.get_define("CC", "gcc")

# Export the CC variable's value to all invocations
# of pake.subpake or ctx.subpake as a define that can be 
# retrieved with pk.get_define()
#
pake.export("CC", CC)


# You can also export lists, dictionaries sets and tuples,
# as long as they only contain literal values.
# Literal values being: strings, integers, floats; and
# other lists, dicts, sets and tuples (if they only contain literals)

pake.export("CC_FLAGS", ['-Wextra', '-Wall'])


# Nesting works with composite literals,
# as long as everything is a pure literal or something
# that str()'s or repr()'s into a literal.

pake.export("STUFF",
            ['you',
             ['might',
              ('be',
               ['a',
                {'bad' :
                     ['person', ['if', {'you', 'do'}, ("this",) ]]
                 }])]])


# Execute outside of a task, by default the stdout/stderr
# of the subscript goes to this scripts stdout.  The file
# object to which stdout gets written to can be specified
# with pake.subpake(..., stdout=(file))

pake.subpake("sometasks/pakefile.py", "dotasks")

# This task does not depend on anything or have any inputs/outputs
# it will basically only run if you explicitly specify it as a default
# task in pake.run, or specify it on the command line

@pk.task
def my_phony_task(ctx):
    # Arguments are passed in a variadic parameter...
    
    # Specify that the "foo" task is to be ran.
    # The scripts output is written to this tasks output queue

    ctx.subpake("library/pakefile.py", "foo")



# Run this pake script, with a default task of 'my_phony_task'

pake.run(pk, tasks=my_phony_task)

```

Output from the example above:

```

*** enter subpake[1]:
pake[1]: Entering Directory "(REST OF PATH...)/paketest/sometasks"
===== Executing Task: "dotasks"
Do Tasks
pake[1]: Exiting Directory "(REST OF PATH...)/paketest/sometasks"
*** exit subpake[1]:
===== Executing Task: "my_phony_task"
*** enter subpake[1]:
pake[1]: Entering Directory "(REST OF PATH...)/paketest/library"
===== Executing Task: "foo"
Foo!
pake[1]: Exiting Directory "(REST OF PATH...)/paketest/library"
*** exit subpake[1]:

```


# Running pake

```bash

cd your_pakefile_directory

# Run pake with up to 10 tasks running in parallel

pake -j 10

```

pake will look for "pakefile.py" or "pakefile" in the current directory and run it.

Or you can specify one or more files to run with **-f/--file**.
The switch does not have multiple arguments, but it can be used more than once to specify multiple files.

For example:

`pake -f pakefile.py foo`

`pake -f your_pakefile_1.py -f your_pakefile_2.py foo`


You can also specify multiple tasks, but do not rely on unrelated tasks
being executed in any specific order because they won't be.  If there is a specific
order you need your tasks to execute in, the one that comes first should be declared
a dependency of the one that comes second, then the second task should be specified to run.

When running parallel builds, leaf dependencies will start executing pretty much
simultaneously, and non related tasks that have a dependency chain may execute
in parallel.


`pake task unrelated_task order_independent_phony`


# Pakes current options


```

usage: pake [-h] [-v] [-D DEFINE] [-j JOBS] [-n] [-C DIRECTORY] [-t] [-ti]
            [-f FILE]
            [tasks [tasks ...]]

positional arguments:
  tasks                 Build tasks.

optional arguments:
  -h, --help            show this help message and exit
  -v, --version         show program's version number and exit
  -D DEFINE, --define DEFINE
                        Add defined value.
  -j JOBS, --jobs JOBS  Max number of parallel jobs. Using this option enables
                        unrelated tasks to run in parallel with a max of N
                        tasks running at a time.
  -n, --dry-run         Use to preform a dry run, lists all tasks that will be
                        executed in the next actual invocation.
  -C DIRECTORY, --directory DIRECTORY
                        Change directory before executing.
  -t, --show-tasks      List all task names.
  -ti, --show-task-info
                        List all tasks along side their doc string. Only tasks
                        with doc strings present will be shown.
  -f FILE, --file FILE  Pakefile path(s). This switch can be used more than
                        once, all specified pakefiles will be executed in
                        order.


```




