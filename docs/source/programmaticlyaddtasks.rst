Pake tasks may be programmatically added using the :py:meth:`pake.Pake.add_task` method of the pake instance.

When adding tasks programmatically, you may specify a callable class instance or a function as your task entry point.


Basic C to Object Compilation Task Example:


.. code-block:: python

   import pake

   pk = pake.init()


   def compile_c(ctx):
       for i, o in ctx.outdated_pairs:
           ctx.call(['gcc', '-c', i, '-o', o])

   # The task name may differ from the function name.

   pk.add_task('compile_c_to_objects', compile_c, inputs=pake.glob('src/*.c'), outputs=pake.pattern('obj/%.o'))

   pake.run(pk, tasks='compile_c_to_objects')

   # Or:

   # pake.run(pk, tasks=compile_c)


Callable Class Example:


.. code-block::python

   import pake

   pk = pake.init()

   class MessagePrinter:
       def __init__(self, message):
           self._message = message

       def __call__(self, ctx):
           ctx.print(self._message)


   pk.add_task('task_a', MessagePrinter('Hello World!'))

   instance_a = MessagePrinter('hello world again')


   # Can refer to the dependency by name, since we did not save a reference.

   pk.add_task('task_b', instance_a, dependencies='task_a')


   instance_b = MessagePrinter('Goodbye!')

   # Can also refer to the dependency by instance.

   pk.add_task('task_c', instance_b, dependencies=instance_a)

   pake.run(pk, tasks='task_c')

   # Or:

   # pake.run(pk, tasks=instance_b)