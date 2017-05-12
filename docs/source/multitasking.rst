Parallelism Inside Tasks
========================

Work can be submitted to the threadpool pake is running it's tasks on in order to achieve a predictable level
of parallelism that is limited by the **--jobs** command line argument or the **jobs** parameter of :py:meth:`pake.Pake.run`.

This is done using the :py:class:`pake.MultitaskContext` returned by :py:meth:`pake.TaskContext.multitask`.

:py:class:`pake.MultitaskContext` implements an **Executor** with an identical interface to
:py:class:`concurrent.futures.ThreadPoolExecutor` from the built-in python module :py:mod:`concurrent.futures`

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