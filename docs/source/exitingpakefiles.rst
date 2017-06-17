Exiting Pakefiles Gracefully
============================

:py:meth:`pake.terminate` can be used to gracefully exit a pakefile from anywhere.

You can also use :py:meth:`pake.Pake.terminate` on the pake context returned by :py:meth:`pake.init`.

:py:meth:`pake.Pake.terminate` is just a shortcut for calling :py:meth:`pake.terminate` with the first argument filled out.

These methods are for exiting pake with a given return code after it is initialized, they ensure
that the proper 'leaving directory / exit subpake` messages are sent to pake's output in order
to keep pake's output consistent.

You should use these functions instead of **exit** when handling error conditions
that occur outside of pake tasks before :py:meth:`pake.run` is called.

It is optional to use :py:meth:`pake.terminate` inside tasks, **exit** will always
work inside tasks but :py:meth:`pake.terminate` may provide additional functionality
in the future.

Example Use Case:

.. code-block:: python

    import os
    import pake
    from pake import returncodes

    pk = pake.init()

    # Say you need to wimp out of a build for some reason
    # But not inside of a task.  pake.terminate will make sure the
    # 'leaving directory/exiting subpake' message is printed
    # if it needs to be.

    if os.name == 'nt':
       pk.print('You really thought you could '
                'build my software on windows? nope!')

       pake.terminate(pk, returncodes.ERROR)

       # or

       # pk.terminate(returncodes.ERROR)


    # Define some tasks...

    @pk.task
    def build(ctx):
        # You can use pake.terminate() inside of a task as well as exit()
        # pake.terminate() may offer more functionality than a raw exit()
        # in the future, however exit() will always work too.

        something_bad_happened = True

        if something_bad_happened:
            pake.terminate(pk, returncodes.ERROR)

            # Or:

            # pk.terminate(returncodes.ERROR)

    pake.run(pk, tasks=build)

    # If you were to use pk.run, a TaskExitException would be thrown
    # the inner exception (err.exception) would be set to
    # pake.TerminateException

    # try:
    #     pk.run(tasks=test)
    # except pake.TaskExitException as err:
    #     print('\n'+str(err)+'\n')
    #
    #     # print to pake.conf.stderr by default
    #     # file parameter can be used to change that
    #     err.print_traceback()


Calls To exit() inside tasks
----------------------------

You can also exit pake with a specific return code when inside a task by simply calling **exit**.

**exit** inside of a task is considered a global exit, even when a task is on another thread due to
pake's **--jobs** parameter being greater than 1.  The return code passed to **exit** inside the task
will become the return code for command line call to pake.

**exit** will always work inside of a task and cause a graceful exit, however :py:meth:`pake.terminate`
may offer more functionality than **exit** sometime in the future.

If you exit with :py:attr:`pake.returncodes.SUCCESS`, no stack trace for the exit call will be printed.

Pake handles calls to **exit** in the same manner as it handles exceptions, although this condition is
instead signified by a :py:exc:`pake.TaskExitException` from :py:meth:`pake.Pake.run` and the message
sent to pake's output is slightly different.

The behavior when running parallel pake is the same as when a normal exception is thrown.


Example:

.. code-block:: python

    import pake
    from pake import returncodes

    pk = pake.init()

    @pk.task
    def test(ctx):
        ctx.print('hello world')

        # We could also use anything other than 0 to signify an error.
        # returncodes.SUCCESS and returncodes.ERROR will always be 0 and 1.
        exit(returncodes.ERROR)

    pake.run(pk, tasks=test)

    # If you were to use pk.run, a TaskExitException would be thrown

    # try:
    #     pk.run(tasks=test)
    # except pake.TaskExitException as err:
    #     print('\n'+str(err)+'\n')
    #
    #     # print to pake.conf.stderr by default
    #     # file parameter can be used to change that
    #     err.print_traceback()


Yields Output:

.. code-block:: bash

    ===== Executing Task: "test"
    hello world

    exit(1) was called within task "test".

    Traceback (most recent call last):
      File "{PAKE_INSTALL_PATH}/pake/pake.py", line 1316, in func_wrapper
        return func(*args, **kwargs)
      File "{FULL_PAKEFILE_DIR_PATH}/pakefile.py", line 12, in test
        exit(returncodes.ERROR)
      File "{PYTHON_INSTALL_PATH}/lib/_sitebuiltins.py", line 26, in __call__
        raise SystemExit(code)
    SystemExit: 1


Stack traces from exit/terminate in tasks
-----------------------------------------

Calls to **exit()**, :py:meth:`pake.terminate`, or :py:meth:`pake.Pake.terminate` with non-zero return codes
will result in a stack trace being printed with information about the location of the exit or terminate call.

This is not the case if you call **exit()** or pake's terminate functions with a return code of zero,
there will be no stack trace or any information printed if the return code is zero (which indicates success).


Example **exit(1)** stack trace:

.. code-block:: python

    import pake
    from pake import returncodes

    pk = pake.init()


    @pk.task
    def build(ctx):
        exit(returncodes.ERROR)

    pake.run(pk, tasks=build)

Yields Output:

.. code-block:: bash

    ===== Executing Task: "build"

    Exit exception "SystemExit" with return-code(1) was raised in task "build".

    Traceback (most recent call last):
      File "{PAKE_INSTALL_PATH}/pake/pake.py", line 1504, in func_wrapper
        return func(*args, **kwargs)
      File "{FULL_PAKEFILE_DIR_PATH}/pakefile.py", line 9, in build
        exit(returncodes.ERROR)
      File "{PYTHON_INSTALL_PATH}/lib/_sitebuiltins.py", line 26, in __call__
        raise SystemExit(code)
    SystemExit: 1


Example **terminate(1)** stack trace:

.. code-block:: python

    import pake
    from pake import returncodes

    pk = pake.init()


    @pk.task
    def build(ctx):
        pk.terminate(returncodes.ERROR)

    pake.run(pk, tasks=build)


Yields Output:

.. code-block:: bash

    ===== Executing Task: "build"

    Exit exception "pake.program.TerminateException" with return-code(1) was raised in task "build".

    Traceback (most recent call last):
      File "{PAKE_INSTALL_PATH}/pake/pake.py", line 1504, in func_wrapper
        return func(*args, **kwargs)
      File "{FULL_PAKEFILE_DIR_PATH}/pakefile.py", line 9, in build
        pk.terminate(returncodes.ERROR)
      File "{PAKE_INSTALL_PATH}/pake/pake.py", line 1027, in terminate
        pake.terminate(self, return_code=return_code)
      File "{PAKE_INSTALL_PATH}/pake/program.py", line 614, in terminate
        m_exit(return_code)
      File "{PAKE_INSTALL_PATH}/pake/program.py", line 605, in m_exit
        raise TerminateException(code)
    pake.program.TerminateException: 1


