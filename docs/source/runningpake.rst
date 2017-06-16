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



Specifying Defines
------------------

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
         -D IM_STRING="Hello"

Retrieval:

.. code-block:: python

    import pake

    pk = pake.init()

    im_true = pk.get_define('IM_TRUE')

    im_true_too = pk.get_define('IM_TRUE_TOO')

    im_none = pk.get_define('IM_NONE')

    no_value = pk.get_define('NO_VALUE')

    im_string = pk.get_define('IM_STRING')


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


You can pass complex python types such as dictionaries, sets, tuples etc.. as a define value, and pake
will recognize and fully deserialize them into the correct type.

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


Read Defines From STDIN
-----------------------

The **--stdin-defines** option allows you to pipe defines into pake in the form of a python dictionary.

Any defines that are set this way can be overwritten by defines set on the command line using **-D/--define**

The dictionary that you pipe in is parsed into a python literal using the built in :py:mod:`ast` module,
so you can use complex types such as sets, tuples, dictionaries ect.. as the value for your defines.

Example:

.. code-block:: bash

    # Pipe in two defines, MY_DEFINE=True and MY_DEFINE_2=42

    echo "{'MY_DEFINE': True, 'MY_DEFINE_2': 42}" | pake --stdin-defines


    # Overwrite the value of MY_DEFINE_2 that was piped in, using the -D/--define option
    # it will have a value of False instead of 42

    echo "{'MY_DEFINE': True, 'MY_DEFINE_2': 42}" | pake --stdin-defines -D MY_DEFINE_2=False


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

