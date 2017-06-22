Concurrency Inside Tasks
========================

Work can be submitted to the threadpool pake is running its tasks on to achieve a
predictable level of concurrency for sub tasks that is limited by the **--jobs** command line argument,
or the **jobs** parameter of :py:meth:`pake.run` and :py:meth:`pake.Pake.run`.

This is done using the :py:class:`pake.MultitaskContext` returned by :py:meth:`pake.TaskContext.multitask`.

:py:class:`pake.MultitaskContext` implements an **Executor** with an identical interface to
:py:class:`concurrent.futures.ThreadPoolExecutor` from the built-in python module :py:mod:`concurrent.futures`.

Submitting work to a :py:class:`pake.MultitaskContext` causes your work to be added to the
threadpool that pake is running on when the **--jobs** parameter is greater than **1**.

When the **--jobs** parameter is **1** (the default value), :py:class:`pake.MultitaskContext`
degrades to synchronous behavior.


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
               # near the bottom of this page for an explanation of 'sync_call'
               # below, and how output synchronization is achieved for
               # ctx.call and ctx.subpake

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


Output synchronization with ctx.print & ctx.io.write
----------------------------------------------------

If you are using :py:meth:`pake.TaskContext.multitask` to add concurrency to
the inside of a task, you are in charge of synchronizing output to the
task IO queue.

Pake will synchronize writing the whole task IO queue when the task finishes
if **--sync-output=False** is not specified on the command line, but it will not
be able to synchronize the output from sub tasks you submit to its threadpool by
yourself without help.

When performing multiple writes to :py:meth:`pake.TaskContext.io` from inside of a task
submitted to :py:meth:`pake.MultitaskContext`, you need to acquire a lock on
:py:attr:`pake.TaskContext.io_lock` if you want to sure all your writes show
up in the order you made them.

If **--sync-output=False** is specified on the command line or :py:attr:`pake.Pake.sync_output`
is set to **False** manually in the pakefile, then using :py:attr:`pake.TaskContext.io_lock`
in a **with** statement does not actually acquire any lock.

If you know that the function or subprocess you are calling is only ever going to write
**once** to the task IO queue (such as the functions in :py:class:`pake.FileHelper`),
then there is no need to synchronize the output.  The single write may come out
of order with respect to other sub tasks, but the message as a whole will be
intact/in-order.

Example:

.. code-block:: python

    import pake
    import random
    import time


    pk = pake.init()


    def my_sub_task(ctx):

        data = [
            'Hello ',
            'World, ',
            'I ',
            'Come ',
            'On ',
            'One ',
            'Line\n']

        # ctx.io.write and ctx.print
        # need to be guarded for guaranteed
        # write order, or they might get
        # scrambled in with other IO pake is doing

        with ctx.io_lock:
            # Lock, so all these writes come in
            # a defined order when jobs > 1

            for i in data:
               # Add a random short delay in seconds
               # to make things interesting

               time.sleep(random.uniform(0, 0.3))
               ctx.io.write(i)

        # This could get scrambled in the output for
        # the task, because your other sub tasks might
        # be interjecting and printing/writing stuff in
        # between these calls to ctx.print when jobs > 1

        data = ['These', 'Are', 'Somewhere', 'Very', 'Weird']

        for i in data:
               # Add a random short delay in seconds
               # to make things interesting

            time.sleep(random.uniform(0, 0.3))

            ctx.print(i)


    @pk.task
    def my_task(ctx):
        # Run the sub task 3 times in parallel,
        # passing it the task context

        with ctx.multitask() as mt:
            for i in range(0, 3):
                mt.submit(my_sub_task, ctx)


    pake.run(pk, tasks=my_task)


Example Output (Will vary of course):

``pake -j 10``

.. code-block:: bash

    ===== Executing Task: "my_task"
    Hello World, I Come On One Line
    Hello World, I Come On One Line
    Hello World, I Come On One Line
    These
    These
    Are
    Are
    These
    Somewhere
    Very
    Are
    Somewhere
    Somewhere
    Weird
    Very
    Very
    Weird
    Weird


Output synchronization with ctx.call & ctx.subpake
--------------------------------------------------

:py:meth:`pake.TaskContext.subpake`, and :py:meth:`pake.call` both have an argument
named **collect_output** which will do all the work required to synchronize output
from sub-pakefiles/processes in a memory efficient manner.

    *Note:*

    :py:meth:`pake.subpake` also has this argument, but you need to pass a lockable context manager object to
    **collect_output_lock** in order to properly synchronize its output to the **stdout** parameter.
    :py:meth:`pake.TaskContext.subpake` does all of this for you and a few extra things to make sure
    everything works right, so use it for multitasking inside tasks instead.  It passes in the
    :py:attr:`pake.TaskContext.io_lock` object as a lock, just FYI.

When the **collect_output** is **True** and the **silent** parameter of these functions is **False**,
they will buffer all process output to a temporary file while the process is doing work.

When the process finishes, theses functions will acquire a lock on :py:attr:`pake.TaskContext.io_lock`
and write all their output to the task's IO queue incrementally.  This way the sub-pakefile/process output
will not get scrambled in with output from other sub tasks that are running concurrently.

Reading process output incrementally from a temporary file after a process
completes will occur much faster than it takes for the actual process to finish.

This means that other processes which may have output can do work and write concurrently,
and pake only needs to lock the task IO queue when it has to relay the output from a
completed process (which is faster than locking while the process is writing).

When pake relays sub-pakefile/process output and **collect_output** is **True**,
the output will be read/written in chunks to prevent possible memory issues with
processes that produce a lot of output.

The **collect_output** parameter can be bound to a certain value with :py:meth:`functools.partial`,
which works well with :py:meth:`pake.MultitaskContext.map` and the other methods of the
multitasking context.


Example:


.. code-block:: python

    import pake

    # functools.partial is used for binding argument values to functions

    from functools import partial


    pk = pake.init()


    @pk.task(i=pake.glob('src/*.c'), o=pake.pattern('obj/%.o'))
    def compile_c(ctx):

        file_helper = pake.FileHelper(ctx)

        # Make 'obj' directory if it does not exist.
        # This does not complain if it is already there.

        file_helper.makedirs('obj')

        # Generate a command for every invocation of GCC that is needed

        compiler_commands = (['gcc', '-c', i, '-o', o] for i, o in ctx.outdated_pairs)

        # ----

        # Only use collect_output when the number of jobs is greater than 1.

        # Task context functions with collect_output parameters such as
        # ctx.call and ctx.subpake will not degrade back to non-locking
        # behavior on their own when the job count is only 1 and collect_output=True.
        # This is so you can use this feature with a thread or a threadpool you have
        # created yourself if you want to, without pake messing it up automagically.

        # You should turn collect_output off when not running pake in parallel,
        # or when you are not using ctx.call or ctx.subpake from another thread
        # that you have manually created. It will still work if you don't, but it
        # will lock IO and pause the main thread until all process output is collected,
        # even when it does not need be doing that.

        sync_call = partial(ctx.call,
                            collect_output=pk.max_jobs > 1)

        # ^^^ You can bind any other arguments to ctx.call you might need this way too.

        with ctx.multitask() as mt:

            # Apply sync_call to every command
            # in the compiler_commands list with map,
            # and force execution of the returned generator
            # by passing it to a list constructor

            # This will execute GCC in parallel on the main task
            # threadpool if pake's --jobs argument is > 1

            # sync_call will keep GCC's output from becoming
            # scrambled in with other stuff if it happens to
            # print warning information or something

            list(mt.map(sync_call, compiler_args))


    pake.run(pk, tasks=compile_c)



Sub task exceptions
-------------------

If an exception occurs inside one of the sub tasks submitted to :py:meth:`pake.MultitaskContext.submit`
or :py:meth:`pake.MultitaskContext.map`, it will be propagated out of the context manager at the end
of your **with** statement.

If more than one task completes with an exception, the one that was submitted
first will be the one to have its exception propagated out of the multitasking context.

If you are not using a **with** statement, the exception will propagate out of
:py:meth:`pake.MultitaskContext.shutdown` when you call it manually.
