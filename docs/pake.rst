pake package
============

Module contents
---------------

.. automodule:: pake
    :members:
    :undoc-members:
    :show-inheritance:


These objects/functions are imported from pake's submodules
into the pake module, and are directly accessible from the pake namespace.

For example, pake is initialized with **pake.init()**, which is actually
a call to :py:meth:`pake.program.init` in the :py:mod:`pake.program` module.

**pake.init()** returns a :py:class:`pake.make.Make` instance which you register your
targets to via the :py:meth:`pake.make.Make.target` decorator, you then run :py:meth:`pake.program.run`
(**pake.run()**) on that instance to start executing pake targets.


Module Imported Classes:

* :py:class:`pake.make.Make`

Module Imported Exceptions:

* :py:class:`pake.make.TargetRedefinedException`
* :py:class:`pake.make.UndefinedTargetException`
* :py:class:`pake.make.TargetInputNotFoundException`
* :py:class:`pake.make.TargetAggregateException`
* :py:class:`pake.program.PakeUninitializedException`
* :py:class:`pake.graph.CyclicDependencyException`
* :py:class:`pake.submake.SubMakeException`
* :py:class:`pake.exception.PakeException`

Module Imported Methods:

* :py:meth:`pake.program.init`
* :py:meth:`pake.program.run`
* :py:meth:`pake.program.get_submake_depth`
* :py:meth:`pake.submake.export`
* :py:meth:`pake.submake.un_export`
* :py:meth:`pake.fileutil.touch`
* :py:meth:`pake.fileutil.ensure_path_exists`


Submodules
----------

pake.program module
-------------------

.. automodule:: pake.program
    :members:
    :undoc-members:
    :show-inheritance:

pake.make module
----------------

.. automodule:: pake.make
    :members:
    :undoc-members:
    :show-inheritance:

pake.console module
-------------------

.. automodule:: pake.console
    :members:
    :undoc-members:
    :show-inheritance:
    :exclude-members: print_error, print_warning

    .. autofunction:: pake.console.print_error(*objects, sep=' ', end='\n', file=sys.stdout)
    .. autofunction:: pake.console.print_warning(*objects, sep=' ', end='\n', file=sys.stdout)

pake.exception module
---------------------

.. automodule:: pake.exception
    :members:
    :undoc-members:
    :show-inheritance:

pake.fileutil module
--------------------

.. automodule:: pake.fileutil
    :members:
    :undoc-members:
    :show-inheritance:

pake.graph module
-----------------

.. automodule:: pake.graph
    :members:
    :undoc-members:
    :show-inheritance:

pake.submake module
-------------------

.. automodule:: pake.submake
    :members:
    :undoc-members:
    :show-inheritance:
    :exclude-members: run_script

    .. autofunction:: pake.submake.run_script(script_path, *args, stdout=sys.stdout, stdout_collect=True, print_execute_header=True, execute_header='***** Executing Script "{}"\\n')

pake.util module
----------------

.. automodule:: pake.util
    :members:
    :undoc-members:
    :show-inheritance:
