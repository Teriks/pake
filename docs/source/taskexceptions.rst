Exceptions Inside Tasks
=======================

Pake handles most exceptions occuring inside a task by wrapping them in a :py:exc:`pake.TaskException`
and throwing them from :py:meth:`pake.Pake.run`.


:py:meth:`pake.run` handles all of the exceptions from :py:meth:`pake.Pake.run` and prints the exception
information to **pake.conf.stderr** in a way that is useful to the user/developer.


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
      File "{PAKE_INSTALL_PATH}/pake/pake.py", line 1316, in func_wrapper
        return func(*args, **kwargs)
      File "{FULL_PAKEFILE_DIR_PATH}/pakefile.py", line 8, in test
        raise Exception('Some Exception')
    Exception: Some Exception


When an exception is thrown inside a task, the fully qualified exception name and the task it
occurred in will be mentioned at the very end of pake's output.  That information is followed
by a stack trace for the raised exception.

When running with multiple jobs, pake will stop as soon as possible.  Independent tasks that were
running in the background when the exception occurred will finish, and then the information for the
encountered exception will be printed at the very end of pake's output.


pake.TaskSubprocessException
----------------------------

Special error reporting is implemented for :py:exc:`pake.TaskSubprocessException`, which is
raised from :py:exc:`pake.TaskContext.call`, :py:exc:`pake.TaskContext.check_call`, and
:py:exc:`pake.TaskContext.check_output`.

When a process called through one of these process spawning methods returns with a non-zero return code,
a :py:exc:`pake.TaskSubprocessException` is raised by default.  That will always be true unless you have
supplied **ignore_errors=True** as an argument to these functions.

The reported exception information will contain the full path to your pakefile, the name of the process
spawning function, and the line number where it was called.  All of this will be at the very top of the
error message.

All output from the failed command will be mentioned at the bottom in a block surrounded by brackets,
which is labeled with **"Command Output: "**


Example:

.. code-block:: python

    import pake


    pk = pake.init()

    @pk.task
    def test(ctx):
        # pake.TaskSubprocessException is raised because
        # which cannot find the given command and returns non-zero

        # silent is specified, which means the process will not
        # send any output to the task IO queue, but the command
        # will still be printed
        ctx.call('which', "i-dont-exist", silent=True)

    pake.run(pk, tasks=test)


Yields Output:

.. code-block:: bash

    ===== Executing Task: "test"
    which i-dont-exist

    pake.pake.TaskSubprocessException(
            filename="{FULL_PAKEFILE_DIR_PATH}/pakefile.py",
            function_name="call",
            line_number=9
    )

    Message: A subprocess spawned by the task context exited with a non-zero return code.

    The following command exited with return code: 1

    which i-dont-exist

    Command Output: {

    which: no i-dont-exist in ({EVERY_DIRECTORY_IN_YOUR_ENV_PATH_VAR})


    }



pake.SubpakeException
---------------------

:py:exc:`pake.SubpakeException` is derived from :py:exc:`pake.process.StreamingSubprocessException`
just like :py:exc:`pake.TaskSubprocessException`, and produces similar error information when raised
inside a task.


Example: ``subfolder/pakefile.py``

.. code-block:: python

    import pake

    pk = pake.init()

    @pk.task
    def sub_test(ctx):
        raise Exception('Test Exception')

    pake.run(pk, tasks=sub_test)


Example: ``pakefile.py``

.. code-block:: python

    import pake

    pk = pake.init()

    @pk.task
    def test(ctx):
        # pake.SubpakeException is raised because
        # 'subfolder/pakefile.py' raises an exception inside a task
        # and returns with a non-zero exit code.

        # Silent prevents the pakefiles output from being printed
        # to the task IO queue, keeping the output short for this example

        ctx.subpake('subfolder/pakefile.py', silent=True)

    pake.run(pk, tasks=test)



Yields Output:

.. code-block:: bash

    ===== Executing Task: "test"

    pake.subpake.SubpakeException(
            filename="{REST_OF_FULL_PATH}/pakefile.py",
            function_name="subpake",
            line_number=13
    )

    Message: A pakefile invoked by pake.subpake exited with a non-zero return code.

    The following command exited with return code: 13

    {PYTHON_INSTALL_DIR}/python3 subfolder/pakefile.py --_subpake_depth 1 --stdin-defines --directory {REST_OF_FULL_PATH}/subfolder

    Command Output: {

    *** enter subpake[1]:
    pake[1]: Entering Directory "{REST_OF_FULL_PATH}/subfolder"
    ===== Executing Task: "sub_test"

    Exception "Exception" was called within task "sub_test".

    Traceback (most recent call last):
      File "{PAKE_INSTALL_DIRECTORY}/pake/pake.py", line 1323, in func_wrapper
        return func(*args, **kwargs)
      File "subfolder/pakefile.py", line 7, in sub_test
    Exception: Test Exception

    pake[1]: Exiting Directory "{REST_OF_FULL_PATH}/subfolder"
    *** exit subpake[1]:


    }



