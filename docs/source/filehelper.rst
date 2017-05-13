Manipulating Files / Dirs With FileHelper
=========================================

:py:class:`pake.FileHelper` contains several useful filesystem manipulation
methods that are common in software builds.  Operations include creating full
directory trees, glob removal of files and directories, file touch etc..

The :py:class:`pake.FileHelper` class takes a single optional argument named **task_ctx**.

If you pass it a :py:class:`pake.TaskContext` instance from your tasks single argument, it will
print information about file system operations to the tasks IO queue as they are being performed.

Each method can turn off this printing by using a **silent** option argument that is common
to all class methods.

If you construct :py:class:`pake.FileHelper` without an argument, all operations will occur
silently.


File / Folder Creation Methods:

.. code-block:: python


   @pk.task
   def my_build(ctx):

       fh = pake.FileHelper(ctx)

       # Create a directory or an entire directory tree

       fh.makedirs('dist/bin')

       # Touch a file

       fh.touch('somefile.txt')

Output:

.. code-block:: none

   ===== Executing Task: "my_build"
   Created Directory(s): "dist/bin"
   Touched File: "somefile.txt"


File Copy / Move Methods:

.. code-block:: python


   @pk.task
   def my_build(ctx):

       fh = pake.FileHelper(ctx)

       # Recursively copy and entire directory tree
       # In this case, 'bin' will be copied as a subfolder
       # into 'dist'.

       fh.copytree('bin', 'dist/bin')

       # Copy a file to a directory without
       # renaming it.

       fh.copy('LICENCE.txt', 'dist')

       # Copy with rename

       fh.copy('LICENCE.txt', 'dist/licence.txt')


       # Move a file to a directory without
       # renaming it.

       fh.move('README.txt', 'dist')

       # Move with rename

       fh.move('README.rtf', 'dist/readme.rtf')

Output:

.. code-block:: none

   ===== Executing Task: "my_build"
   Copied Tree: "bin" -> "dist/bin"
   Copied File: "LICENCE.txt" -> "dist"
   Copied File: "LICENCE.txt" -> "dist/licence.txt"
   Moved File: "README.txt" -> "dist"
   Moved File: "README.rtf" -> "dist/readme.rtf"


File Removal / Clean Related Methods:

.. code-block:: python

   @pk.task
   def my_clean(ctx):

       fh = pake.FileHelper(ctx)


       # Glob delete all files under the 'obj' directory

       fh.glob_remove('obj/*.o')


       # Delete all sub directories of 'stuff'

       fh.glob_remove_dirs('stuff/*')


       # Remove a directory tree, does nothing if 'build_dir'
       # does not exist.  Unless the must_exist argument is
       # set to True.

       fh.rmtree('build_dir')


       # Remove a file, does nothing if 'main.exe' does not
       # exist.  Unless the must_exist argument is set to True

       fh.remove('main.exe')

Output:

.. code-block:: none

   ===== Executing Task: "my_clean"
   Glob Removed Files: "obj/*.o"
   Glob Removed Directories: "stuff/*"
   Removed Directory(s): "build_dir"
   Removed File: "main.exe"