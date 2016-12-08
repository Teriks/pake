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
    with the target parameter set to the :py:class:`pake.make.Target`
    instance that gets passed into a target will cause it to print information about
    the file operations it is preforming to the targets output, unless it is specified
    that the function be silent via the silent parameter."""

    def __init__(self, target=None):
        """Build the FileHelper object around the :py:class:`pake.make.Target` instance
        that gets passed into a pake target, or None.

        :param target: A :py:class:`pake.make.Target` instance or None, if target is is set
                       then information about the file operations that occur using this
                       FileHelper instance will be printed to the targets output, unless
                       the 'silent' parameter is set to True in the function being called.
        """
        if type(target) is not pake.make.Target:
            raise ValueError("target was not a pake.make.Target object.")

        self._target = target

    def makedirs(self, path, silent=False, exist_ok=True):
        """Create a directory tree if it does not exist, if the directory tree exists already this function does nothing.

        :param exist_ok: If False, an OSError will be thrown if any directory
                         in the given path already exists.

        :param silent: If True, don't print information to the targets output.

        :raises OSError: Raised for all directory creation errors aside from errno.EEXIST.
        :param path: The directory path/tree."""

        if not silent and self._target is not None:
            self._target.print('Created Directory(s): "{}"'.format(path))

        try:
            os.makedirs(path)
        except OSError as exception:
            if exception.args[0] != errno.EEXIST:
                raise

    def touch(self,file_name, mode=0o666, exist_ok=True, silent=False):
        """Create a file at this given path. If mode is given, it is combined with the process’ umask value to determine the file mode and access flags.
        If the file already exists, the function succeeds if exist_ok is true (and its modification time is updated to the current time),
        otherwise FileExistsError is raised.

        :raises FileExistsError: Raised if exist_ok is False and the file already exists.

        :param silent: If True, don't print information to the targets output.

        :param file_name: The file name.
        :param mode: The umask.
        :param exist_ok: whether or not it is okay for the file to exist already.
        """
        if not silent and self._target is not None:
            self._target.print('Touch file: "{}"'.format(file_name))
        pathlib.Path(file_name).touch(mode=mode, exist_ok=exist_ok)

    def copytree(self, src, dest, symlinks=False, ignore=False, silent=False):
        """Copy an entire directory tree recursively to a destination.

        :raises FileNotFoundError: If the given source path is not found.

        :param src: The source directory tree.
        :param dest: The destination path.
        :param symlinks: If True, try to copy symlinks.
        :param ignore: If True, ignore errors while copying files and directories.
        :param silent: If True, Don't print info the the targets output.
        """
        if not silent and self._target is not None:
            self._target.print('Copy Tree: "{}" -> "{}"'
                               .format(src, dest))
        shutil.copytree(src, dest, symlinks=symlinks, ignore=ignore)

    def move(self, src, dest, silent=False):
        """Move a file to a new location.

        :raises FileNotFoundError: If the given source file is not found.

        :param src: The file.
        :param dest: The destination to move the file to.
        :param silent: If True, don't print information to the targets output.
        """

        if not silent and self._target is not None:
            self._target.print('Move Files: "{}" -> "{}"'
                               .format(src, dest))
        shutil.move(src, dest)

    def copy(self, src, dest, copy_metadata=False, silent=False):
        """Copy a file to a destination.

        :raises FileNotFoundError: If the given source file is not found.
        :param src: The file.
        :param dest: The destination path.
        :param copy_metadata: If True, file metadata like creation time will be copied to the new file.
        :param silent: If True, Don't print information to the targets output.
        """

        if copy_metadata:
            if not silent and self._target is not None:
                self._target.print('Copy File With Metadata: "{}" -> "{}"'
                                   .format(src, dest))
            shutil.copy2(src, dest)
        else:
            if not silent and self._target is not None:
                self._target.print('Copy File: "{}" -> "{}"'
                                   .format(src, dest))
            shutil.copy(src, dest)

    def remove(self, path, silent=False, must_exist=False):
        """Remove a file from disk if it exists, otherwise do nothing.

        :raise FileNotFoundError: If must_exist is True, and the file does not exist.
        :param must_exist: If set to True, a FileNotFoundError will be raised if the file does not exist.
        :param path: The path of the file to remove.
        :param silent: If True, don't print information to the targets output.
        """
        if not silent and self._target is not None:
            self._target.print('Remove: "{}"'.format(path))

        try:
            os.remove(path)
        except FileNotFoundError:
            if must_exist:
                raise

    def glob_remove(self, glob_pattern, silent=False):
        """Remove files using a glob pattern, this makes use of pythons built in glob module.
        :param silent: If True, don't print information to the targets output.

        :param glob_pattern: The glob pattern to use to search for files to remove.

        :raises OSError: Raised if the file is in use (On Windows), or if there is another problem deleting one of the files.
        """
        if not silent and self._target is not None:
            self._target.print('Glob Remove Files: "{}"'.format(glob_pattern))
        for i in (f for f in glob.iglob(glob_pattern) if os.path.isfile(f)):
            os.remove(i)

    def glob_remove_dirs(self, glob_pattern, silent=False):
        """Remove directories using a glob pattern, this makes use of pythons built in glob module.

        This function will remove non empty directories.

        :param glob_pattern: The glob pattern to use to search for directories to remove.

        :param silent: If True, don't print information to the targets output.

        :raises OSError: Raised if there is a problem deleting one of the directories.
        """
        if not silent and self._target is not None:
            self._target.print('Glob Remove Directories: "{}"'.format(glob_pattern))
        for i in (d for d in glob.iglob(glob_pattern) if os.path.isdir(d)):
            shutil.rmtree(i, ignore_errors=True)

    def removedirs(self, path, silent=False, must_exist=False):
        """Remove a directory tree if it exist, if the directory tree does not exists this function does nothing.

        This function will remove non empty directories.

        :raises FileNotFoundError: Raised if must_exist is True and the given path does not exist.

        :param must_exist: If True, a FileNotFoundError will be raised if the directory
                           does not exist.

        :param silent: If True, don't print information to the targets output.

        :param path: The directory path/tree."""
        if not silent and self._target is not None:
            self._target.print('Remove Directory(s): "{}"'.format(path))
        try:
            shutil.rmtree(path)
        except FileNotFoundError:
            if must_exist:
                raise
