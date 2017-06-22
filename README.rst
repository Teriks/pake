About pake
==========

|Master Documentation Status| |Develop Documentation Status| |codecov|

pake is a make-like python build utility where tasks, dependencies and
build commands can be expressed entirely in python, similar to ruby
rake.

pake supports automatic file/directory change detection when dealing with
task inputs and outputs, and also parallel builds.

pake requires python3.5+


This readme contains only a little information about how to use pake, please
checkout the latest documentation at the links above for an expansive
overview on how pake works and how pakefiles should be written.

Installing
==========

Note: pake is Alpha and likely to change some.


To install the latest release use:

``sudo pip3 install python-pake --upgrade``


If you want to install the development branch you can use:

``sudo pip3 install git+git://github.com/Teriks/pake@develop``


Example project using pake
==========================

I am using libasm\_io to help test pake and have included a pakefile
build along side the makefiles in that project.

https://github.com/Teriks/libasm\_io

Writing Basic Tasks
===================

Here's a contrived pake demo which demonstrates how tasks are written:

.. code-block:: python

    import pake

    # Tasks are registered the the pake.Pake object
    # returned by pake's initialization call, using the task decorator.

    pk = pake.init()

    # Try to grab a command line define.
    # In particular the value of -D CC=..
    # CC will default to 'gcc' in this case if
    # it was not specified.

    CC = pk.get_define('CC', 'gcc')

    # you can also use the syntax: pk["CC"] to
    # attempt to get the defines value, if it is not
    # defined then it will return None.

    # ===

    # If you just have a single input/output, there is no
    # need to pass a list to the tasks inputs/outputs

    @pk.task(i='foo/foo.c', o='foo/foo.o')
    def foo(ctx):
        # Execute a program (gcc) and print its stdout/stderr to the tasks output.

        # ctx.call can be passed a command line as variadic arguments, an iterable, or
        # as a string.  It will automatically flatten out non string iterables in your variadic
        # arguments or iterable object, so you can pass an iterable such as ctx.inputs
        # as part of your full command line invocation instead of trying to create the command
        # line by concatenating lists or using the indexer on ctx.inputs/ctx.outputs

        ctx.call(CC, '-c', ctx.inputs, '-o', ctx.outputs)


    # Pake can handle file change detection with multiple inputs
    # and outputs. If the amount of inputs is different from
    # the amount of outputs, the task is considered to be out
    # of date if any input file is newer than any output file.

    # When the amount of inputs is equal to the amount of outputs,
    # pake will compare each input to its corresponding output
    # and collect out of date input/outputs into ctx.outdated_inputs
    # and ctx.outdated_outputs respectively.  ctx.outdated_pairs
    # can be used to get a generator over (input, output) pairs,
    # it is shorthand for zip(ctx.outdated_inputs, ctx.outdated_outputs)

    @pk.task(i=pake.glob('bar/*.c'), o=pake.pattern('bar/%.o'))
    def bar(ctx):

        # zip together the outdated inputs and outputs, since they
        # correspond to each other, this iterates of a sequence of python
        # tuple objects in the form (input, output)

        for i, o in ctx.outdated_pairs:
            ctx.call(CC, '-c', i, '-o', o)


    # This task depends on the 'foo' and 'bar' tasks, as
    # specified with the decorators leading parameters.
    # It outputs 'bin/baz' by taking the input 'main.c'
    # and linking it to the object files produced in the other tasks.

    @pk.task(foo, bar, o='bin/baz', i='main.c')
    def baz(ctx):
        """Use this to build baz"""

        # Documentation strings can be viewed by running 'pake -ti' in
        # the directory the pakefile exists in, it will list all documented
        # tasks with their python doc strings.

        # The pake.FileHelper class can be used to preform basic file
        # system operations while printing information about the operations
        # it has completed to the tasks output.

        file_helper = pake.FileHelper(ctx)

        # Create a bin directory, this won't complain if it exists already
        file_helper.makedirs('bin')

        # ctx.dependency_outputs contains a list of all outputs that this
        # tasks immediate dependencies produce

        ctx.call(CC, '-o', ctx.outputs, ctx.inputs, ctx.dependency_outputs)


    @pk.task
    def clean(ctx):
        """Clean binaries"""

        file_helper = pake.FileHelper(ctx)

        # Clean up using the FileHelper object.
        # Remove the bin directory, this wont complain if 'bin'
        # does not exist.

        file_helper.rmtree('bin')

        # Glob remove object files from the foo and bar directories

        file_helper.glob_remove('foo/*.o')
        file_helper.glob_remove('bar/*.o')


    # Run pake; The default task that will be executed when
    # none are specified on the command line will be 'baz' in
    # this case.

    # The tasks parameter is optional, but if it is not specified
    # here, you will be required to specify a task or tasks on the
    # command line.

    pake.run(pk, tasks=baz)


Output from command ``pake``:

.. code-block:: bash

    ===== Executing task: "bar"
    gcc -c bar/bar.c -o bar/bar.o
    ===== Executing task: "foo"
    gcc -c foo/foo.c -o foo/foo.o
    ===== Executing task: "baz"
    Created Directory(s): "bin"
    gcc -o bin/baz main.c foo/foo.o bar/bar.o


Output from command ``pake clean``:

.. code-block:: bash

    ===== Executing task: "clean"
    Removed Directory(s): "bin"
    Glob Removed Files: "foo/*.o"
    Glob Removed Files: "bar/*.o"


Concurrency Inside Tasks
========================

Work can be submitted to the threadpool pake is running its tasks on to achieve a
predictable level of concurrency for sub tasks that is limited by the **--jobs** command line argument,
or the **jobs** parameter of **pake.run** and **pake.Pake.run**.

Example:

.. code-block:: python

    import pake

    # functools.partial is used for binding argument values to functions

    from functools import partial


    pk = pake.init()


    @pk.task(i=pake.glob('src/*.c'), o=pake.pattern('obj/%.o'))
    def build_c(ctx)

       file_helper = pake.FileHelper(ctx)

       # Make 'obj' directory if it does not exist.
       # This does not complain if it is already there.

       file_helper.makedirs('obj')

       # Start multitasking

       with ctx.multitask() as mt:
           for i, o in ctx.outdated_pairs:

               # Read the section 'Output synchronization with ctx.call & ctx.subpake'
               # in the 'Concurrency Inside Tasks` page on http://pake.readthedocs.io
               # for an explanation of 'sync_call' below, and how output
               # synchronization is achieved for ctx.call and ctx.subpake

               sync_call = partial(ctx.call,
                                   collect_output=pk.max_jobs > 1)

               # Submit a work function with arguments to the threadpool
               mt.submit(sync_call, ['gcc', '-c', i, '-o', o])


    @pk.task(build_c, i=pake.glob('obj/*.o'), o='main')
    def build(ctx):

       # Utilizing the automatic non string iterable
       # flattening here to pass ctx.inputs and ctx.outputs

       ctx.call('gcc', ctx.inputs, '-o', ctx.outputs)


    pake.run(pk, tasks=build)


Running Sub Pakefiles
=====================

Pake is able to run itself through the use of **pake.TaskContext.subpake**
and **pake.subpake**.

**pake.subpake** is meant to be used outside of tasks, and can even be
called before pake is initialized.

**pake.TaskContext.subpake** is preferred for use inside of tasks because
it handles writing to the task's output queue for you, without having to specify
extra parameters to **pake.subpake** to get it working correctly.

**pake.TaskContext** instance is passed into the single argument of each task function,
which you can in turn call **subpake** from.

Defines can be exported to pakefiles ran with the **subpake** functions using **pake.export**.

**pake.subpake** and **pake.TaskContext.subpake** use the **--stdin-defines** option of
pake to pass exported define values into the new process instance, which means you can overwrite your
exported define values with **-D/--define** in the subpake command arguments if you need to.

Export / Subpake Example:

.. code-block:: python

    import pake

    pk = pake.init()

    # Try to get the CC define from the command line,
    # default to 'gcc'.

    CC = pk.get_define('CC', 'gcc')

    # Export the CC variable's value to all invocations
    # of pake.subpake or ctx.subpake as a define that can be
    # retrieved with pk.get_define()

    pake.export('CC', CC)


    # You can also export lists, dictionaries sets and tuples,
    # as long as they only contain literal values.
    # Literal values being: strings, integers, floats; and
    # other lists, dicts, sets and tuples.  Collections must only
    # contain literals, or objects that repr() into a parsable literal.

    pake.export('CC_FLAGS', ['-Wextra', '-Wall'])


    # Nesting works with composite literals,
    # as long as everything is a pure literal or something
    # that str()'s into a literal.

    pake.export('STUFF',
                ['you',
                 ['might',
                  ('be',
                   ['a',
                    {'bad' :
                         ['person', ['if', {'you', 'do'}, ('this',) ]]
                     }])]])


    # This export will be overrode in the next call
    pake.export('OVERRIDE_ME', False)


    # Execute outside of a task, by default the stdout/stderr
    # of the subscript goes to this scripts stdout.  The file
    # object to which stdout gets written to can be specified
    # with pake.subpake(..., stdout=(file))

    # This command also demonstrates that you can override
    # your exports using the -D/--define option

    pake.subpake('sometasks/pakefile.py', 'dotasks', '-D', 'OVERRIDE_ME=True')


    # This task does not depend on anything or have any inputs/outputs
    # it will basically only run if you explicitly specify it as a default
    # task in pake.run, or specify it on the command line

    @pk.task
    def my_phony_task(ctx):
        # Arguments are passed in a variadic parameter...

        # Specify that the "foo" task is to be ran.
        # The scripts output is written to this tasks output queue

        ctx.subpake('library/pakefile.py', 'foo')



    # Run this pake script, with a default task of 'my_phony_task'

    pake.run(pk, tasks=my_phony_task)


Output from the example above:

.. code-block:: bash

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


Running pake
============

.. code-block:: bash

    cd your_pakefile_directory

    # Run pake with up to 10 tasks running in parallel

    pake -j 10

pake will look for "pakefile.py" or "pakefile" in the current directory
and run it.

Or you can specify one or more files to run with **-f/--file**. The
switch does not have multiple arguments, but it can be used more than
once to specify multiple files.

For example:

``pake -f pakefile.py foo``

``pake -f your_pakefile_1.py -f your_pakefile_2.py foo``

You can also specify multiple tasks, but do not rely on unrelated tasks
being executed in any specific order because they won't be. If there is
a specific order you need your tasks to execute in, the one that comes
first should be declared a dependency of the one that comes second, then
the second task should be specified to run.

When running parallel builds, leaf dependencies will start executing
pretty much simultaneously, and non related tasks that have a dependency
chain may execute in parallel.

``pake task unrelated_task order_independent_phony``

Command Line Options
--------------------

::

    usage: pake [-h] [-v] [-D DEFINE] [--stdin-defines] [-j JOBS] [-n]
                [-C DIRECTORY] [-t] [-ti] [--sync-output {True, False, 1, 0}]
                [-f FILE]
                [tasks [tasks ...]]

    positional arguments:
      tasks                 Build tasks.

    optional arguments:
      -h, --help            show this help message and exit
      -v, --version         show program's version number and exit
      -D DEFINE, --define DEFINE
                            Add defined value.
      --stdin-defines       Read defines from a Python Dictionary piped into
                            stdin. Defines read with this option can be
                            overwritten by defines specified on the command line
                            with -D/--define.
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
      --sync-output {True, False, 1, 0}
                            Tell pake whether it should synchronize task output
                            when running with multiple jobs. Console output can
                            get scrambled under the right circumstances with this
                            turned off, but pake will run slightly faster. This
                            option will override any value in the PAKE_SYNC_OUTPUT
                            environmental variable, and is inherited by subpake
                            invocations unless the argument is re-passed with a
                            different value.
      -f FILE, --file FILE  Pakefile path(s). This switch can be used more than
                            once, all specified pakefiles will be executed in
                            order with the current directory as the working
                            directory (unless -C is specified).


.. |Master Documentation Status| image:: https://readthedocs.org/projects/pake/badge/?version=latest
   :target: http://pake.readthedocs.io/en/latest/?badge=latest
.. |Develop Documentation Status| image:: https://readthedocs.org/projects/pake/badge/?version=develop
   :target: http://pake.readthedocs.io/en/develop/?badge=develop
.. |codecov| image:: https://codecov.io/gh/Teriks/pake/branch/master/graph/badge.svg
   :target: https://codecov.io/gh/Teriks/pake
