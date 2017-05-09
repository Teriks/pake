Running Pake
============

.. code-block:: bash

    cd your_pakefile_directory

    # Run pake with up to 10 tasks running in parallel

    pake -j 10

pake will look for "pakefile.py" or "pakefile" in the current directory and run it.

Or you can specify one or more files to run with **-f/--file**.
The switch does not have multiple arguments, but it can be used
more than once to specify multiple files.

For example:

.. code-block:: bash

    pake -f pakefile.py foo

    pake -f your_pakefile_1.py -f your_pakefile_2.py foo


You can also specify multiple tasks, but do not rely on unrelated tasks
being executed in any specific order because they won't be.  If there is a specific
order you need your tasks to execute in, the one that comes first should be declared
a dependency of the one that comes second, then the second task should be specified to run.

When running parallel builds, leaf dependencies will start executing pretty much
simultaneously, and non related tasks that have a dependency chain may execute
in parallel.


.. code-block:: bash

    pake task unrelated_task order_independent_task

Command Line Options
--------------------

.. code-block:: none

    usage:
     usage: pake [-h] [-v] [-D DEFINE] [-j JOBS] [-n] [-C DIRECTORY] [-t] [-ti] [-f FILE] [tasks [tasks ...]]

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
                             order.