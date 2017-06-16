Running Pake
============

.. code-block:: bash

    cd your_pakefile_directory

    # Run pake with up to 10 tasks running in parallel

    pake -j 10

pake will look for "pakefile.py" or "pakefile" in the current directory and run it if it exists.


Manually Specifying Pakefile(s)
-------------------------------

You can specify one or more files to run with **-f/--file**.
The switch does not have multiple arguments, but it can be used
more than once to specify multiple files.

If you specify more than one pakefile with a **--jobs** parameter greater than 1,
the specified pakefiles will still be run synchronously (one after another).  The tasks
inside each pakefile will be ran in parallel however.

For example:

.. code-block:: bash

    pake -f pakefile.py foo

    pake -f your_pakefile_1.py -f your_pakefile_2.py foo


Executing In Another Directory
------------------------------

The **-C** or **--directory** option can be used to execute pake in an arbitrary directory.

If you do not specify a file with **-f** or **--file**, then a pakefile must exist in the given directory:

Example:

.. code-block:: bash

    # Pake will find the 'pakefile.py' in 'build_directory'
    # then change directories into it and start running

    pake -C build_directory my_task

You can also tell pake to run a pakefile (or multiple pakefiles) in a different working directory.

Example:

.. code-block:: bash

    # Pake will run 'my_pakefile.py' with a working directory of 'build_directory'

    pake -f my_pakefile.py -C build_directory my_task

    # Pake will run all the given pakefiles with a working directory of 'build_directory'

    pake -f pakefile1.py -f pakefile2.py -f pakefile3.py -C build_directory my_task


Specifying Multiple Tasks
-------------------------

You can specify multiple tasks, but do not rely on unrelated tasks being executed in any
specific order because they won't be.  If there is a specific order you need your tasks to
execute in, the one that comes first should be declared a dependency of the one that comes
second, then the second task should be specified to run.

When running parallel builds, leaf dependencies will start executing pretty much
simultaneously, and non related tasks that have a dependency chain may execute
in parallel.

In general, direct dependencies of a task have no defined order of execution when
there is more than one of them.

``pake task unrelated_task order_independent_task``

Command Line Options
--------------------

.. code-block:: none

    usage: pake [-h] [-v] [-D DEFINE] [-j JOBS] [--stdin-defines] [-n]
                [-C DIRECTORY] [-t] [-ti] [-f FILE]
                [tasks [tasks ...]]

    positional arguments:
      tasks                 Build tasks.

    optional arguments:
      -h, --help            show this help message and exit
      -v, --version         show program's version number and exit
      -D DEFINE, --define DEFINE
                            Add defined value.
      -j JOBS, --jobs JOBS  Max number of parallel jobs. Using this option enables
                            unrelated tasks to run in parallel with a max of N
                            tasks running at a time.
      --stdin-defines       Read defines from a Python Dictionary piped into
                            stdin. Defines read with this option can be
                            overwritten by defines specified on the command line
                            with -D/--define.
      -n, --dry-run         Use to preform a dry run, lists all tasks that will be
                            executed in the next actual invocation.
      -C DIRECTORY, --directory DIRECTORY
                            Change directory before executing.
      -t, --show-tasks      List all task names.
      -ti, --show-task-info
                            List all tasks along side their doc string. Only tasks
                            with doc strings present will be shown.
      -f FILE, --file FILE  Pakefile path(s). This switch can be used more than
                            once, all specified pakefiles will be executed in
                            order with the current directory as the working
                            directory (unless -C is specified).


Return Codes
------------

See the :py:mod:`pake.returncodes` module, pake's return codes are defined
as constants and each is described in detail in the module documentation.

