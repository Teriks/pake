Running Sub Pakefiles
=====================

Pake is able to run itself through the use of :py:meth:`pake.TaskContext.subpake`
or even :py:meth:`pake.subpake`.

:py:meth:`pake.TaskContext.subpake` is preferred because it handles writing program
output to the tasks output queue in a synchronized manner when multiple jobs are running.

A :py:meth:`pake.TaskContext.subpake` is passed into the single argument of each task function.

Defines can be exported to pakefiles ran with the **subpake** functions using :py:meth:`pake.export`.

Example:

.. code-block:: python

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
    # that str()'s into a literal.

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