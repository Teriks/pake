.. |br| raw:: html

   <br />

.. pake documentation master file, created by
   sphinx-quickstart on Fri Dec  2 08:17:16 2016.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to pake's documentation!
================================

pake is a make-like python build utility where tasks, dependencies and build commands
can be expressed entirely in python, similar to ruby rake.

pake supports automatic file/directory change detection when dealing with
task inputs and outputs, and also parallel builds.

pake requires python3.5+


Installing
----------

Note: pake is Alpha and likely to change some.

.. code-block:: bash

    sudo pip3 install python-pake


Module Doc
----------

.. toctree::
   :maxdepth: 4

   pake


Guides / Help
-------------

.. toctree::
   :maxdepth: 4

   Running Pake <runningpake>
   Writing Basic Tasks <basictasks>
   Exiting Pakefiles Before pake.run <exitingpakefiles>
   Adding Tasks Programmatically <programmaticlyaddtasks>
   Exceptions Inside Tasks <taskexceptions>
   Parallelism Inside Tasks <multitasking>
   Manipulating Files / Dirs With FileHelper <filehelper>
   Running Commands / Subprocess's <subprocess>
   Running Sub Pakefiles <subpake>


Module Index
------------

* :ref:`modindex`







