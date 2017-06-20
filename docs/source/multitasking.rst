Parallelism Inside Tasks
========================

Work can be submitted to the threadpool pake is running it's tasks on in order to achieve a predictable level
of parallelism that is limited by the **--jobs** command line argument or the **jobs** parameter of :py:meth:`pake.Pake.run`.

This is done using the :py:class:`pake.MultitaskContext` returned by :py:meth:`pake.TaskContext.multitask`.

:py:class:`pake.MultitaskContext` implements an **Executor** with an identical interface to
:py:class:`concurrent.futures.ThreadPoolExecutor` from the built-in python module :py:mod:`concurrent.futures`

When you use multitasking inside of a task, you are responsible for any output synchronization
that may be necessary, if you need to run a process that writes multiple times **stdout** or **stderr**,
you will need to collect the process output and write it in one big chunk (one write) to the tasks
IO queue (:py:attr:`pake.TaskContext.io`).

If any of the gcc invocations below experience an error, they will have multiple lines
of output that might get scrambled in with output from other commands as they finish running.

However, ctx.call duplicates process output to a file and pake reads it back upon error.
And since exceptions will propagate out of the tasks submitted to the multitasking context,
pake would report the :py:pake:`pake.TaskSubprocessException` that occurred with the full
unscrambled command output at the bottom of the build log.

Example:

.. code-block:: python

    import pake

    pk=pake.init()

    @pk.task(i=pake.glob('src/*.c'), o=pake.pattern('obj/%.o'))
    def build_c(ctx)

       # Start multitasking

       with ctx.multitask() as mt:
           for i, o in ctx.outdated_pairs:
               # Submit a work function with arguments to the threadpool

               mt.submit(ctx.call, ['gcc', '-c', i, '-o', o])


    @pk.task(build_c, i=pake.glob('obj/*.o'), o='main')
    def build(ctx):

       # Utilizing the automatic non string iterable
       # flattening here to pass ctx.inputs and ctx.outputs

       ctx.call(['gcc', ctx.inputs, '-o', ctx.outputs])


    pake.run(pk, tasks=build)