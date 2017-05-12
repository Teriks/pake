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

import os.path
import subprocess
import sys

import os

import pake.process
import pake.program
import pake.util

__all__ = ['export', 'subpake']

_exports = dict()


def export(name, value):
    """
    Exports a define that can be retrieved in subpake scripts via :py:func:`~pake.Pake.get_define`.
    
    :param name: The name of the define.
    :param value: The value of the define.
    """
    _exports[name] = value


def subpake(*args, stdout=None, silent=False, exit_on_error=True):
    """
    Execute a pakefile.py script, changing directories if necessary.
    
    This function should not be used inside tasks, use: :py:meth:`pake.TaskContext.subpake` instead.
    A :py:meth:`pake.TaskContext` instance is passed into the single parameter of each task, usually named **ctx**.
    
    :py:meth:`pake.subpake` allows similar syntax to :py:meth:`pake.TaskContext.call`
    for it's **\*args** parameter.
    
    Subpake scripts do not inherit the **--jobs** argument from the parent script, if you want
    to run them with multithreading enabled you need to pass your own **--jobs** argument manually.
    
    Example:
    
    .. code-block:: python
    
       # These are all equivalent
    
       pake.subpake('dir/pakefile.py', 'task_a', '-C', 'some_dir')
    
       pake.subpake(['dir/pakefile.py', 'task_a', '-C', 'some_dir'])
       
       # note the nested iterable containing string arguments
       
       pake.subpake(['dir/pakefile.py', 'task_a', ['-C', 'some_dir']])
       
       pake.subpake('dir/pakefile.py task_a -C some_dir')
    
    
    :raises: :py:class:`ValueError` if no command + optional arguments are provided.
    :raises: :py:class:`FileNotFoundError` if the first argument (the pakefile) is not found.
    :raises: :py:class:`pake.SubprocessException` if the called pakefile script encounters an error and **exit_on_error** is **False**.
    
    :param args: The script, and additional arguments to pass to the script
    :param stdout: The stream to write all of the scripts output to. (defaults to pake.conf.stdout)
    :param silent: Whether or not to silence all output.
    
    :param exit_on_error: Whether or not to print to **pake.conf.stderr** and immediately \
                          **exit(1)** if the pakefile script encounters an error.
    """

    args = pake.util.handle_shell_args(args)

    if len(args) < 1:
        raise ValueError('Not enough arguments provided, '
                         'must at least provide a pakefile.py script path as the first argument.')

    script = args.pop(0)

    if not os.path.isfile(script):
        raise FileNotFoundError('pakefile: "{}" does not exist.'.format(script))

    stdout = stdout if stdout is not None else pake.conf.stdout

    script_dir = os.path.dirname(os.path.abspath(script))

    try:
        depth = pake.program.get_subpake_depth() + 1
    except pake.program.PakeUninitializedException:
        depth = 0

    extra_args = []
    for key, value in _exports.items():
        extra_args += ['-D', key + '=' + str(value)]

    extra_args += ['--s_depth', str(depth)]

    if os.getcwd() != script_dir:
        extra_args += ['--directory', script_dir]

    args = [sys.executable, script] + extra_args + list(str(i) for i in args)

    try:
        output = subprocess.check_output(args,
                                         stderr=subprocess.STDOUT)
        if not silent:
            stdout.flush()
            stdout.write(output.decode())

    except subprocess.CalledProcessError as err:
        ex = pake.process.SubprocessException(cmd=args,
                                              returncode=err.returncode,
                                              output=err.output,
                                              message='An exceptional condition occurred '
                                                      'inside a pakefile ran by subpake.')
        if exit_on_error:
            print(str(ex), file=pake.conf.stderr)
            exit(1)
        else:
            raise ex
