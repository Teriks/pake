Writing Basic Tasks
===================

Additional information about change detection is available in the form of examples in
the documentation for the :py:meth:`pake.Pake.task` function decorator.

Pake is capable of handling change detection against both files and directories, and the two can be used
as inputs or outputs interchangeably and in combination.


**Note:**

each registered task receives a :py:class:`pake.TaskContext` instance as a single argument when run.

In this example the argument is named **ctx**, but it can be named however you like.

It is not an error to leave this argument undefined, but you will most likely be using it.

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

