Running Commands / Subprocess's
===============================


TaskContext.call
----------------


The :py:class:`pake.TaskContext` object passed into each task contains
methods for calling subprocess's in a way that produces user friendly
error messages and halts the execution of pake if an error is reported
by the given process.


:py:meth:`pake.TaskContext.call` can be used to run a program and direct
all of its output (stdout and stderr) to the tasks IO queue.


Examples:

.. code-block:: python


    # 'call' can have its arguments passed in several different ways

    @pk.task(o='somefile.txt')
    def my_task(ctx):

        # Command line passed as a list..
        ctx.call(['echo', 'Hello!'])

        # Iterables such as the outputs property of the context
        # will be flattened.  String objects are not considered
        # for flattening which allows this sort of syntax

        ctx.call(['touch', ctx.outputs]) # We know there is only one output


        # Command line passed as a string

        ctx.call('echo "goodbye!"')

        # Try some command and ignore any errors (non zero return codes)
        # Otherwise, 'call' raises a 'pake.SubprocessException' on non zero
        # return codes.

        ctx.call(['do_something_bad'], ignore_errors=True)


    # A realistic example for compiling objects from C

    @pk.task(i=pake.glob('src/*.c'), o=pake.pattern('obj/%.o'))
    def compile_c(ctx):
        for i, o in ctx.outdated_pairs:
            ctx.call(['gcc', '-c', i, '-o', o])


    # And with multitasking, the simple way

    @pk.task(i=pake.glob('src/*.c'), o=pake.pattern('obj/%.o'))
    def compile_c(ctx):
        with ctx.multitask() as mt:
            for i, o in ctx.outdated_pairs:
                mt.submit(ctx.call, ['gcc', '-c', i, '-o', o])


    # With multitasking, the fancy way

    @pk.task(i=pake.glob('src/*.c'), o=pake.pattern('obj/%.o'))
    def compile_c(ctx):
        with ctx.multitask() as mt:

            # Force enumeration over the returned generator by constructing a temporary list..
            # the 'ctx.map' function yields 'Future' instances

            list(ctx.map(ctx.call, (['gcc', '-c', i, '-o', o] for i, o in ctx.outdated_pairs)))


TaskContext.check_output
------------------------

:py:meth:`pake.TaskContext.check_output` can be used to read all the output
from a command into a bytes object.  The args parameter of **check_output**
and in general all functions dealing with calling system commands allow for
identical syntax, including nested lists and such.

The reasoning or using this over the built in :py:meth:`subprocess.check_output`
is that if an error occurs in the subprocess, pake will be able to print more comprehensible
error information to the task output.

:py:meth:`pake.TaskContext.check_output` differs from :py:meth:`subprocess.check_output`
in that you cannot specify an **stderr** parameter, and an **ignore_errors**
option is added which can prevent the method from raising an exception on non
zero return codes from the process.  All of the processes **stderr** is directed
to it's **stdout**.

**ignore_errors** allows you to directly return the output of a command even if it errors
without having to handle an exception to get the output.

:py:meth:`pake.TaskContext.check_output` returns a **bytes** object, which means you need
to call **decode** on it if you want the output as a string.


Examples:

.. code-block:: python

    # 'which' is a unix command that returns the full path of a command's binary.
    # The exit code is non zero if the command given does not exist.  So
    # it will be easy enough to use for this example.

    @pk.task
    def my_task(ctx):
        # Print the full path of the default C compiler on linux

        ctx.print(ctx.check_output(['which', 'cc']).decode())

        # Check if some command exists

        if ctx.check_output(['which', 'some_command'],
                            ignore_errors=True).decode().strip() != '':

            ctx.print('some_command exists')

        # Using an exception handler

        try:
            path = ctx.check_output(['which', 'gcc']).decode()
            ctx.print('gcc exists!, path:', path)
        except pake.SubprocessException:
            pass



TaskContext.check_call
----------------------


:py:meth:`pake.TaskContext.check_call` has an identical signature to :py:meth:`pake.TaskContext.check_output`,
except it returns the return code of the called process.

The **ignore_errors** argument allows you to return the value of non zero return codes without
having to handle an exception such as with :py:meth:`subprocess.check_call` from pythons built
in subprocess module.

In addition if an exception is thrown, pake will be able to print comprehensible error output
about the location of the exception to the task IO queue same as the other functions dealing
with processes in the task context;  Without printing a huge stack trace.


Examples:

.. code-block:: python

    # using the 'which' command here again for this example...

    @pk.task
    def my_task(ctx):

        # Check if some command exists, a better way on linux at least

        if ctx.check_call(['which', 'some_command'],
                           ignore_errors=True) == 0:

            ctx.print('some_command exists')

        # Using an exception handler

        try:
            ctx.check_call(['which', 'gcc'])
            ctx.print('gcc exists!')
        except pake.SubprocessException:
            pass

