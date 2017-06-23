Running Pake
============

.. code-block:: bash

    cd your_pakefile_directory

    # Run pake with up to 10 tasks running in parallel

    pake -j 10

pake will look for "pakefile.py" or "pakefile" in the current directory and run it if it exists.


Manually specifying pakefile(s)
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


Executing in another directory
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


Running multiple tasks
----------------------

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



Specifying define values
------------------------

The **-D/--define** option is used to specify defines on the command line that can be retrieved
with the :py:meth:`pake.Pake.get_define` method, or **__getitem__** indexer on the :py:class:`pake.Pake`
object (which is returned by :py:meth:`pake.init`).

Define values are parsed partially with the built in :py:mod:`ast` module, the only caveat is that the
values **True**, **False** and **None** are case insensitive.

Defines which are specified without a value, default to the value of **True**.

Basic Example:

.. code-block:: bash

    pake -D IM_TRUE=True \
         -D IM_TRUE_TOO=true \
         -D IM_NONE=none \
         -D NO_VALUE \
         -D IM_STRING="Hello" \
         -D IM_INT=1 \
         -D IM_FLOAT=0.5

Retrieval:

.. code-block:: python

    import pake

    pk = pake.init()

    im_true = pk.get_define('IM_TRUE')

    im_true_too = pk.get_define('IM_TRUE_TOO')

    im_none = pk.get_define('IM_NONE')

    no_value = pk.get_define('NO_VALUE')

    im_string = pk.get_define('IM_STRING')

    im_int = pk.get_define('IM_INT')

    im_float = pk.get_define('IM_FLOAT')


    print(type(im_true)) # -> <class 'bool'>
    print(im_true) # -> True

    print(type(im_true_too)) # -> <class 'bool'>
    print(im_true_too) # -> True

    print(type(im_none)) # -> <class 'NoneType'>
    print(im_none) # -> None

    print(type(no_value)) # -> <class 'bool'>
    print(no_value) # -> True

    print(type(im_string)) # -> <class 'str'>
    print(im_string) # -> Hello

    print(type(im_int)) # -> <class 'int'>
    print(im_int) # -> 1

    print(type(im_float)) # -> <class 'float'>
    print(im_float) # -> 0.5

    pk.terminate(0)


You can pass complex python literals such as lists, sets, tuples, dictionaries, etc.. as a define value.
pake will recognize and fully deserialize them into the correct type.

Complex Types Example:

.. code-block:: bash

    pake -D IM_A_DICT="{'im': 'dict'}" \
         -D IM_A_SET="{'im', 'set'}" \
         -D IM_A_LIST="['im', 'list']" \
         -D IM_A_TUPLE="('im', 'tuple')"

Retrieval:

.. code-block:: python

    import pake

    pk = pake.init()

    im_a_dict = pk.get_define('IM_A_DICT')

    im_a_set = pk.get_define('IM_A_SET')

    im_a_list = pk.get_define('IM_A_LIST')

    im_a_tuple = pk.get_define('IM_A_TUPLE')


    print(type(im_a_dict)) # -> <class 'dict'>
    print(im_a_dict) # -> {'im': 'dict'}

    print(type(im_a_set)) # -> <class 'set'>
    print(im_a_set) # -> {'im', 'set'}

    print(type(im_a_list)) # -> <class 'list'>
    print(im_a_list) # -> ['im': 'list']

    print(type(im_a_tuple)) # -> <class 'tuple'>
    print(im_a_tuple) # -> ('im': 'tuple')

    pk.terminate(0)


Reading defines from STDIN
--------------------------

The **--stdin-defines** option allows you to pipe defines into pake in the form of a python dictionary.

Any defines that are set this way can be overwritten by defines set on the command line using **-D/--define**

The dictionary that you pipe in is parsed into a python literal using the built in :py:mod:`ast` module,
so you can use complex types such as lists, sets, tuples, dictionaries ect.. as the value for your defines.

Pake reads the defines from **stdin** on the first call to :py:meth:`pake.init` and caches them in memory.
Later calls to **init** will read the specified defines back from cache and apply them to a newly created
:py:class:`pake.Pake` instance.

Calls to :py:meth:`pake.de_init` will not clear cached defines read from **stdin**.


Example Pakefile:

.. code-block:: python

    import pake

    pk = pake.init()

    a = pk['MY_DEFINE']
    b = pk['MY_DEFINE_2']

    print(a)
    print(b)

    pk.terminate(0)


Example Commands:

.. code-block:: bash

    # Pipe in two defines, MY_DEFINE=True and MY_DEFINE_2=42

    echo "{'MY_DEFINE': True, 'MY_DEFINE_2': 42}" | pake --stdin-defines

    # Prints:

    True
    42


    # Overwrite the value of MY_DEFINE_2 that was piped in, using the -D/--define option
    # it will have a value of False instead of 42

    echo "{'MY_DEFINE': True, 'MY_DEFINE_2': 42}" | pake --stdin-defines -D MY_DEFINE_2=False

    # Prints:

    True
    False


Environmental variables
-----------------------

Pake currently recognizes only one environmental variable named ``PAKE_SYNC_OUTPUT``.

This variable corresponds to the command line option **--sync-output**.
Using the **--sync-output** option will override the environmental variable however.
Pake will use the value from the command line option instead of the value in the environment.

When this environmental variable and **--sync-output** are not defined/specified,
the default value pake uses is **--sync-output True**.

:py:meth:`pake.init` has an argument named **sync_output** that can also be used to
permanently override both the **--sync-output** switch and the ``PAKE_SYNC_OUTPUT``
environmental variable from inside of a pakefile.

The **--sync-output** option controls whether pake tries to synchronize task output
by queueing it when running with more than one job.

**--sync-output False** causes :py:class:`pake.TaskContext.io_lock` to yield a lock
object which actually does nothing when it is acquired, and it also forces pake
to write all run output to :py:attr:`pake.Pake.stdout` instead of task output
queues, even when running tasks concurrently.

The output synchronization setting is inherited by all :py:meth:`pake.subpake`
and :py:meth:`pake.Pake.subpake` invocations.

You can stop this inheritance by manually passing a different value for **--sync-output**
as a shell argument when using one of the **subpake** functions.  The new value will
be inherited by the pakefile you invoked with **subpake** and all of its children.


Command line options
--------------------

.. code-block:: none

    usage: pake [-h] [-v] [-D DEFINE] [--stdin-defines] [-j JOBS] [-n]
                    [-C DIRECTORY] [-t] [-ti] [--sync-output {True, False, 1, 0}]
                    [-f FILE]
                    [tasks [tasks ...]]

        positional arguments:
          tasks                 Build tasks.

        optional arguments:
          -h, --help            show this help message and exit
          -v, --version         show program's version number and exit
          -D DEFINE, --define DEFINE
                                Add defined value.
          --stdin-defines       Read defines from a Python Dictionary piped into
                                stdin. Defines read with this option can be
                                overwritten by defines specified on the command line
                                with -D/--define.
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
          --sync-output {True, False, 1, 0}
                                Tell pake whether it should synchronize task output
                                when running with multiple jobs. Console output can
                                get scrambled under the right circumstances with this
                                turned off, but pake will run slightly faster. This
                                option will override any value in the PAKE_SYNC_OUTPUT
                                environmental variable, and is inherited by subpake
                                invocations unless the argument is re-passed with a
                                different value or overridden in pake.init.
          -f FILE, --file FILE  Pakefile path(s). This switch can be used more than
                                once, all specified pakefiles will be executed in
                                order with the current directory as the working
                                directory (unless -C is specified).


Return codes
------------

See the :py:mod:`pake.returncodes` module, pake's return codes are defined
as constants and each is described in detail in the module documentation.

