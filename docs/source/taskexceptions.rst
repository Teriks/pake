Exceptions Inside Tasks
=======================

Pake handles most exceptions occuring inside a task by wrapping them in a :py:exc:`pake.TaskException`
and throwing them from :py:meth:`pake.Pake.run`.


:py:meth:`pake.run` handles all of the exceptions from :py:meth:`pake.Pake.run` for you an prints the
exception information in a way that is useful to the user/developer.


Example:

.. code-block:: python

    import pake

    pk = pake.init()

    @pk.task
    def test(ctx):
        ctx.print('hello world')
        raise Exception('Some Exception')

    pake.run(pk, tasks=test)

    # If you were to use pk.run, a TaskException would be thrown

    # try:
    #     pk.run(tasks=test)
    # except pake.TaskException as err:
    #     print('\n'+str(err)+'\n')
    #
    #     # print to pake.conf.stderr by default
    #     # file parameter can be used to change that
    #     err.print_traceback()


Yields Output:

.. code-block:: bash

    ===== Executing Task: "test"
    hello world

    Exception "Exception" was called within task "test".

    Traceback (most recent call last):
      File "{PAKE_INSTALL_PATH_HERE}\pake\pake.py", line 1316, in func_wrapper
        return func(*args, **kwargs)
      File "{PAKEFILE_DIRECTORY_HERE}\pakefile.py", line 8, in test
        raise Exception('Some Exception')
    Exception: Some Exception


When an exception is thrown inside a task, the fully qualified exception name and the task it
occurred in will be mentioned at the very end of pake's output.  That information is followed
by a stack trace for the raised exception.

When running with multiple jobs, pake will stop as soon as possible.  Independent tasks that were
running in the background when the exception occurred will finish, and then the information for the
encountered exception will be printed at the very end of pake's output.


Calls To exit() Inside Tasks
----------------------------


You can exit pake with a specific return code from inside a task by simply calling **exit**.

**exit** inside of a task is considered a global exit, even when a task is on another thread due to
pake's **--jobs** parameter being greater than 1.  The return code passed to **exit** inside the task
will become the return code for command line call to pake.

If you exit with :py:attr:`pake.returncodes.SUCCESS`, no stack trace for the exit call will be printed.

Pake handles calls to **exit** in the same manner as it handles exceptions, although this condition is
instead signified by a :py:exc:`pake.TaskExitException` and the message sent to pake's output is slightly different.

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
      File "{PAKE_INSTALL_PATH_HERE}\pake\pake.py", line 1316, in func_wrapper
        return func(*args, **kwargs)
      File "{PAKEFILE_DIRECTORY_HERE}\pakefile.py", line 12, in test
        exit(returncodes.ERROR)
      File "{PYTHON_INSTALL_PATH_HERE}\lib\_sitebuiltins.py", line 26, in __call__
        raise SystemExit(code)
    SystemExit: 1


pake.SubprocessException Inside Tasks
-------------------------------------

Special reporting is implemented for :py:exc:`pake.SubprocessException`, which is raised from
:py:exc:`pake.TaskContext.call` and friends.


When a process called through one of the process spawning methods in :py:exc:`pake.TaskContext`
returns with a non 0 return code, a :py:exc:`pake.SubprocessException` is raised by default;  Unless you
have specified in the process spawning functions arguments to ignore non 0 return codes.

The reported exception information will contain the full path to your pakefile, the name of the process
spawning function, and the line number where it was called.  All of this will be at the very top of the
error message.

All output from the failed command will be mentioned at the bottom in a block surrounded by brackets,
which is labeled with "Command Output: "


.. code-block:: python

    import pake

    pk = pake.init()

    @pk.task
    def test(ctx):
        # pake.SubprocessException is raised because
        # which cannot find the given command and returns non 0

        # silent is specified, which means the process will not
        # send any output to the task IO queue, but the command
        # will still be printed
        ctx.call('which', "i-dont-exist", silent=True)

    pake.run(pk, tasks=test)


Yields Output:

.. code-block:: bash

    ===== Executing Task: "test"
    which i-dont-exist

    pake.process.SubprocessException(
            filename="{FULL_PAKEFILE_PATH}\pakefile.py",
            function_name="call",
            line_number=9
    )

    Message: An error occurred while executing a system command inside a pake task.

    The following command exited with return code: 1

    which i-dont-exist

    Command Output: {

    which: no i-dont-exist in ({EVERY_DIRECTORY_IN_YOUR_ENV_PATH_VAR})


    }