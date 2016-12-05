pake package
============

Submodules
----------

pake.console module
-------------------

.. automodule:: pake.console
    :members:
    :undoc-members:
    :show-inheritance:

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

pake.make module
----------------

.. automodule:: pake.make
    :members:
    :undoc-members:
    :show-inheritance:

pake.program module
-------------------

.. automodule:: pake.program
    :members:
    :undoc-members:
    :show-inheritance:

pake.submake module
-------------------

.. automodule:: pake.submake
    :members:
    :undoc-members:
    :show-inheritance:

pake.util module
----------------

.. automodule:: pake.util
    :members:
    :undoc-members:
    :show-inheritance:


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
	
Module Imported Methods:

* :py:meth:`pake.program.init`
* :py:meth:`pake.program.run`
* :py:meth:`pake.submake.export`
* :py:meth:`pake.submake.un_export`
* :py:meth:`pake.submake.run_script`
* :py:meth:`pake.fileutil.touch`
* :py:meth:`pake.fileutil.ensure_path_exists`
* :py:meth:`pake.console.print_error`
* :py:meth:`pake.console.print_warning`
