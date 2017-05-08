# Copyright (c) 2017, Teriks
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
import inspect
import pathlib
import shlex

import os
from collections import namedtuple

import pake.conf


def touch(file_name, mode=0o666, exist_ok=True):
    """
    Create a file at this given path. 
    If mode is given, it is combined with the process’ umask value to determine the file mode and access flags.
    If the file already exists, the function succeeds if exist_ok is true (and its modification time is updated to the current time), otherwise *FileExistsError* is raised.

    
    :param file_name: The file name.
    :param mode: The mode.
    :param exist_ok: Whether or not it is okay for the file to exist when touched, if not a *FileExistsError* is thrown.
    :return: 
    """
    pathlib.Path(file_name).touch(mode=mode, exist_ok=exist_ok)


def is_iterable(obj):
    """
    Test if an object is iterable.
    
    :param obj: The object to test.
    :return: True if the object is iterable, False otherwise.
    """
    try:
        _ = iter(obj)
        return True
    except:
        return False


def is_iterable_not_str(obj):
    """
    Test if an object is iterable, and not a string.
    
    :param obj: The object to test.
    :return: True if the object is an iterable non string, False otherwise.
    """

    return type(obj) is not str and is_iterable(obj)


def str_is_float(s):
    """Test if a string can be parsed into a float.
    
    :returns: True or False
    :rtype: bool
    """

    try:
        _ = float(s)
        return True
    except ValueError:
        return False


def str_is_int(s):
    """Test if a string can be parsed into an integer.
    
    :returns: True or False
    :rtype: bool
    """

    try:
        _ = int(s)
        return True
    except ValueError:
        return False


def get_task_arg_name(val):
    """Get the name of task reference that may be either a function or a
    string referencing a function name.  Mostly for internal usage.
    
    If you pass a function, **fun.__name__** is returned.  Otherwise **str(val)** is returned.
    
    :param val: Argument value
    :return: The name of the passed function object, or a stringified version of whatever object was passed in.
    """
    if inspect.isfunction(val):
        return val.__name__
    else:
        return str(val)


def flatten_non_str(iterable):
    """Flatten a nested iterable without affecting strings.
    
    Example:
    
    .. code-block:: python
       
       val = list(flatten_non_str(['this', ['is', ['an'], 'example']]))
       
       # val == ['this', 'is', 'an', 'example']
    
    :returns: A generator that iterates over the flattened iterable.
    
    """

    for x in iterable:
        if is_iterable_not_str(x):
            for y in flatten_non_str(x):
                yield y
        else:
            yield x


def handle_shell_args(args):
    """Handles parsing the **\*args** parameter of :py:meth:`pake.TaskContext.call` and :py:meth:`pake.subpake`.
    
    It allows shell arguments to be passed as a list object, variadic parameters, or a single string.
    
    :returns: A list of shell argument strings.
    """

    if len(args) == 1:
        if is_iterable_not_str(args[0]):
            args = [str(i) for i in flatten_non_str(args[0])]
        elif type(args[0]) is str:
            args = shlex.split(args[0], posix=not os.name == 'nt')
    else:
        args = [str(i) for i in flatten_non_str(args)]

    return args


class CallerDetail(namedtuple('CallerDetail', ['filename', 'function_name', 'line_number'])):
    """
    .. py:attribute:: filename
    
        Source file name.
        
    .. py:attribute:: function_name
    
        Function call name.
    
    .. py:attribute:: line_number
    
        Line number of function call.
    """
    pass


def get_pakefile_caller_detail():
    """Get the full pakefile path, called function name and function call line number of the first
    function call in the current call tree which exists inside of a pakefile.
       
    This function traverses up the stack frame looking for the first occurrence of
    a source file with the same path that :py:meth:`pake.conf.get_init_file` returns.
       
    If a pakefile is not found in the call tree, this function returns **None**.
       
    :returns: A named tuple: :py:class:`pake.util.CallerDetail` or **None**.
    """

    last = None

    cur_frame = inspect.currentframe()

    init_file = pake.conf.get_init_file()
    init_dir = pake.conf.get_init_dir()

    if init_file is None:
        return None

    try:
        for frame_detail in inspect.getouterframes(cur_frame):

            # In newer versions of python, this is a namedtuple.
            # This should be compatible if it is just a normal tuple instead.

            frame, filename, line_number, function_name, lines, index = frame_detail

            frame_file = os.path.normpath(os.path.join(init_dir, filename))

            if init_file == frame_file:
                return CallerDetail(
                    filename=frame_file,
                    function_name=last[3],
                    line_number=line_number)

            last = frame_detail

        return None

    finally:
        del cur_frame
