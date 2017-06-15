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


.. code-block:: python

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
        ctx.call(CC, '-c', ctx.inputs, '-o', ctx.outputs)


    # Pake can handle file change detection with multiple inputs
    # and outputs. If the amount of inputs is different from
    # the amount of outputs, the task is considered to be out
    # of date if any input file is newer than any output file.
    #
    # When the amount of inputs is equal to the amount of outputs,
    # pake will compare each input to its corresponding output
    # and collect out of date input/outputs into ctx.outdated_inputs
    # and ctx.outdated_outputs respectively.  ctx.outdated_pairs
    # can be used to get a generator over (input, output) pairs,
    # it is shorthand for zip(ctx.outdated_inputs, ctx.outdated_outputs)
    @pk.task(i=pake.glob("bar/*.c"), o=pake.pattern('bar/%.o'))
    def bar(ctx):

        # zip together the outdated inputs and outputs, since they
        # correspond to each other, this iterates of a sequence of python
        # tuple objects in the form ("input", "output")

        for i, o in ctx.outdated_pairs:
            ctx.call(CC, '-c', i, '-o', o)

    # This task depends on the foo and bar tasks, as
    # specified with the decorators leading parameters,
    # And only outputs "bin/baz" by taking the input "main.c"
    # and linking it to the object files produced in the other tasks.

    # Documentation strings can be viewed by running 'pake -ti' in
    # the directory the pakefile exists in, it will list all documented
    # tasks with their python doc strings.
    #
    # The pake.FileHelper class can be used to preform basic file
    # system operations while printing to the tasks output information
    # about what said operation is doing.
    @pk.task(foo, bar, o="bin/baz", i="main.c")
    def baz(ctx):
        """Use this to build baz"""

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
        ctx.call(CC, '-o', ctx.outputs, ctx.inputs, ctx.dependency_outputs)


    @pk.task
    def clean(ctx):
        """Clean binaries"""

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


Output from the example above:

.. code-block:: bash

    ===== Executing task: "bar"
    gcc -c "bar/bar.c" -o "bar/bar.o"
    ===== Executing task: "foo"
    gcc -c "foo/foo.c" -o "foo/foo.o"
    ===== Executing task: "baz"
    Created Directory(s): "bin"
    gcc -o bin/baz main.c foo/foo.o bar/bar.o