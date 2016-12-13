# Copyright (c) 2016, Teriks
# All rights reserved.
#
# pake is distributed under the following BSD 3-Clause License
#
# Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
#
# 3. Neither the name of the copyright holder nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
# ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import errno
import os
import pathlib
import pake.make
import shutil
import glob


class FileHelper:
    """A helper class for dealing with common file operations
    inside and outside of pake targets.  Instantiating this class
    with the target parameter set to a :py:class:`pake.make.Target`
    instance will cause it to print information about file system operations
    that it preforms.  Each available file system functions notice message
    can be silenced using the **silent** parameter of the function.
    """

    def __init__(self, target=None):
        """Build the FileHelper object around the :py:class:`pake.make.Target` instance
        that gets passed into a pake target, or None.

        :param target: A :py:class:`pake.make.Target` instance or None.  If **target** is set
                       then information about the file operations that occur using this
                       FileHelper instance will be printed to the targets output, unless
                       the 'silent' parameter is set to True in the function being called.
        """
        if type(target) is not pake.make.Target:
            raise ValueError("target was not a pake.make.Target object.")

        self._target = target

    @property
    def target(self):
        return self._target

    def makedirs(self, path, silent=False, exist_ok=True):
        """Create a directory tree if it does not exist, if the directory tree exists already this function does nothing.

        This uses :py:meth:`os.makedirs`.

        :param path: The directory path/tree.

        :param silent: If True, don't print information to the targets output.

        :param exist_ok: If False, an OSError will be thrown if any directory
                         in the given path already exists.

        :raises OSError: Raised for all directory creation errors aside from **errno.EEXIST
        """

        if not silent and self._target is not None:
            self._target.print('Created Directory(s): "{}"'.format(path))

        try:
            os.makedirs(path)
        except OSError as exception:
            if not exist_ok and exception.args[0] != errno.EEXIST:
                raise

    def touch(self, file_name, mode=0o666, exist_ok=True, silent=False):
        """Create a file at this given path. If mode is given, it is combined with the process’ umask value to determine
        the file mode and access flags.  If the file already exists, the function succeeds if exist_ok is true
        (and its modification time is updated to the current time), otherwise :py:class:`FileExistsError` is raised.

        This uses :py:meth:`pathlib.Path.touch`.

        :raises FileExistsError: Raised if exist_ok is False and the file already exists.

        :param file_name: The file name.
        :param mode: The umask.
        :param exist_ok: whether or not it is okay for the file to exist already.
        :param silent: If True, don't print information to the targets output.
        """
        if not silent and self._target is not None:
            self._target.print('Touched File: "{}"'.format(file_name))
        pathlib.Path(file_name).touch(mode=mode, exist_ok=exist_ok)

    def copytree(self, src, dst, symlinks=False, ignore=None, copy_function=shutil.copy2, ignore_dangling_symlinks=False, silent=False):
        """copytree(self, src, dst, symlinks=False, ignore=None, copy_function=shutil.copy2, ignore_dangling_symlinks=False, silent=False)
        Recursively copy a directory tree,  See :py:meth:`shutil.copytree`.

        The destination directory must not already exist.
        If exception(s) occur, an Error is raised with a list of reasons.

        If the optional symlinks flag is true, symbolic links in the
        source tree result in symbolic links in the destination tree; if
        it is false, the contents of the files pointed to by symbolic
        links are copied. If the file pointed by the symlink doesn't
        exist, an exception will be added in the list of errors raised in
        an Error exception at the end of the copy process.

        You can set the optional ignore_dangling_symlinks flag to true if you
        want to silence this exception. Notice that this has no effect on
        platforms that don't support :py:meth:`os.symlink`.

        The optional ignore argument is a callable. If given, it
        is called with the `src` parameter, which is the directory
        being visited by :py:meth:`shutil.copytree`, and `names` which is the list of
        `src` contents, as returned by :py:meth:`os.listdir`:

        callable(src, names) -> ignored_names

        Since :py:meth:`shutil.copytree` is called recursively, the callable will be
        called once for each directory that is copied. It returns a
        list of names relative to the `src` directory that should
        not be copied.

        The optional copy_function argument is a callable that will be used
        to copy each file. It will be called with the source path and the
        destination path as arguments. By default, :py:meth:`shutil.copy2` is used, but any
        function that supports the same signature (like :py:meth:`shutil.copy`) can be used.



        :raises shutil.Error: If exception(s) occur, an Error is raised with a list of reasons.

        :param src: The source directory tree.
        :param dst: The destination path.
        :param symlinks: If True, try to copy symlinks.
        :param ignore: If True, ignore errors while copying files and directories.

        :param copy_function: The copy function, if not specified :py:meth:`shutil.copy2` is used.

        :param ignore_dangling_symlinks: If True, don't throw an exception when the file pointed to
                                         by a symlink does not exist.

        :param silent: If True, Don't print info the the targets output.
        """
        if not silent and self._target is not None:
            self._target.print('Copied Tree: "{}" -> "{}"'
                               .format(src, dst))

        shutil.copytree(src, dst,
                        symlinks=symlinks,
                        ignore=ignore,
                        copy_function=copy_function,
                        ignore_dangling_symlinks=ignore_dangling_symlinks)

    def move(self, src, dest, copy_function=shutil.copy2, silent=False):
        """move(self, src, dest, copy_function=shutil.copy2, silent=False)

        Recursively move a file or directory to another location.  (See shutil.move)
        This is similar to the Unix "mv" command. Return the file or directory's
        destination.

        If the destination is a directory or a symlink to a directory, the source
        is moved inside the directory. The destination path must not already
        exist.

        If the destination already exists but is not a directory, it may be
        overwritten depending on :py:meth:`os.rename` semantics.

        If the destination is on our current filesystem, then :py:meth:`os.rename` is used.
        Otherwise, src is copied to the destination and then removed. Symlinks are
        recreated under the new name if :py:meth:`os.rename` fails because of cross
        filesystem renames.

        The optional `copy_function` argument is a callable that will be used
        to copy the source or it will be delegated to :py:meth:`shutil.copytree`.
        By default, :py:meth:`shutil.copy2` is used, but any function that supports the same
        signature (like :py:meth:`shutil.copy`) can be used.

        :raises shutil.Error: If the destination already exists, or if src is moved into itself.

        :param src: The file.
        :param dest: The destination to move the file to.
        :param copy_function: The copy function to use for copying individual files.
        :param silent: If True, don't print information to the targets output.
        """

        if not silent and self._target is not None:
            self._target.print('Moved File: "{}" -> "{}"'
                               .format(src, dest))
        shutil.move(src, dest, copy_function=copy_function)

    def copy(self, src, dest, copy_metadata=False, silent=False):
        """Copy a file to a destination.

        See :py:meth:`shutil.copy` and :py:meth:`shutil.copy2` (when copy_metadata is True)

        :param src: The file.
        :param dest: The destination path.
        :param copy_metadata: If True, file metadata like creation time will be copied to the new file.
        :param silent: If True, Don't print information to the targets output.
        """

        if copy_metadata:
            if not silent and self._target is not None:
                self._target.print('Copied File With Metadata: "{}" -> "{}"'
                                   .format(src, dest))
            shutil.copy2(src, dest)
        else:
            if not silent and self._target is not None:
                self._target.print('Copied File: "{}" -> "{}"'
                                   .format(src, dest))
            shutil.copy(src, dest)

    def remove(self, path, silent=False, must_exist=False):
        """Remove a file from disk if it exists, otherwise do nothing,  uses :py:meth:`os.remove`.

        :raise FileNotFoundError: If must_exist is True, and the file does not exist.
        :raise OSError: If the path is a directory.

        :param path: The path of the file to remove.
        :param silent: If True, don't print information to the targets output.
        :param must_exist: If set to True, a FileNotFoundError will be raised if the file does not exist.
        """
        if not silent and self._target is not None:
            self._target.print('Removed File: "{}"'.format(path))

        try:
            os.remove(path)
        except FileNotFoundError:
            if must_exist:
                raise

    def glob_remove(self, glob_pattern, silent=False):
        """Remove files using a glob pattern, this makes use of pythons built in glob module.

        Files are removed using :py:meth:`os.remove`.

        :param glob_pattern: The glob pattern to use to search for files to remove.

        :param silent: If True, don't print information to the targets output.

        :raises OSError: Raised if a file is in use (On Windows), or if there is another problem deleting one of the files.
        """
        if not silent and self._target is not None:
            self._target.print('Glob Removed Files: "{}"'.format(glob_pattern))
        for i in (f for f in glob.iglob(glob_pattern) if os.path.isfile(f)):
            os.remove(i)

    def glob_remove_dirs(self, glob_pattern, silent=False):
        """Remove directories using a glob pattern, this makes use of pythons built in glob module.

        This uses :py:meth:`shutil.rmtree` to remove directories.

        This function will remove non empty directories.

        :param glob_pattern: The glob pattern to use to search for directories to remove.

        :param silent: If True, don't print information to the targets output.
        """
        if not silent and self._target is not None:
            self._target.print('Glob Removed Directories: "{}"'.format(glob_pattern))
        for i in (d for d in glob.iglob(glob_pattern) if os.path.isdir(d)):
            shutil.rmtree(i, ignore_errors=True)

    def rmtree(self, path, silent=False, must_exist=False):
        """Remove a directory tree if it exist, if the directory tree does not exists this function does nothing.

        This uses :py:meth:`shutil.rmtree`.

        This function will remove non empty directories.

        :raises FileNotFoundError: Raised if must_exist is True and the given path does not exist.

        :param path: The directory path/tree.

        :param silent: If True, don't print information to the targets output.

        :param must_exist: If True, a FileNotFoundError will be raised if the directory
                           does not exist
        """
        if not silent and self._target is not None:
            self._target.print('Removed Directory(s): "{}"'.format(path))
        try:
            shutil.rmtree(path)
        except FileNotFoundError:
            if must_exist:
                raise
