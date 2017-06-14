Exiting Pakefiles Before pake.run
=================================


:py:meth:`pake.terminate` is meant to be used before any tasks are run to gracefully exit a pakefile.

You can also use :py:meth:`pake.Pake.terminate` on the pake context returned by :py:meth:`pake.init`,
which is just a shorthand for :py:meth:`pake.terminate` that provides the first argument for you.

These methods are for exiting pake outside of a task after pake is initialized, they ensure that
the proper 'leaving directory / exit subpake` messages are sent to pake's output in order
to keep the output of pake consistent.

You should use these functions instead of **exit** when handling error conditions before :py:meth:`pake.run`
is called, but after :py:meth:`pake.init` has been called.

Do not call :py:meth:`pake.terminate` or :py:meth:`pake.Pake.terminate` inside of task, for that you
should simply use a call to **exit()**.  (See: :ref:`Calls To exit() Inside Tasks`)

Example Use Case:

.. code-block:: python

   import os
   import pake
   from pake import returncodes

   pk = pake.init()

   # Say you need to wimp out of a build for some reason
   # But not inside of a task.

   if os.name == 'nt':
       pk.print('You really thought you could '
                'build my software on windows? nope!')

       pake.terminate(pk, returncodes.ERROR)

       # or

       # pk.terminate(returncodes.ERROR)


   # Define some tasks...

   @pk.task
   def build(ctx):
       pass

   pake.run(pk, tasks=build)
