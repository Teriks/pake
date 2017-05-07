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

from pake.util import handle_shell_args

import os

from .program import get_subpake_depth, get_max_jobs, PakeUninitializedException

_exports = dict()


def export(name, value):
    """
    Exports a define that can be retrieved in subpake scripts via :py:func:`~pake.Pake.get_define`.
    
    :param name: The name of the define.
    :param value: The value of the define.
    """
    _exports[name] = value


def subpake(script, *args, stdout=None, silent=False):
    """
    Execute a pakefile.py script, changing directories if necessary.
    
    :py:meth:`pake.subpake` allows similar syntax to :py:meth:`pake.TaskContext.call`
    for it's **\*args** parameter.
    
    Example:
    
    .. code-block:: python
    
       # These are all equivalent
    
       pake.subpake('dir/pakefile', 'task_a', '-C', 'some_dir')
    
       pake.subpake('dir/pakefile', ['task_a', '-C', 'some_dir'])
       
       pake.subpake('dir/pakefile', 'task_a -C some_dir')
    
    
    :param script: The path to the pakefile.py script
    :param args: Additional arguments to pass to the script
    :param stdout: The stream to write all of the scripts output to. (defaults to sys.stdout)
    :param silent: Whether or not to silence all output.
    """

    args = handle_shell_args(args)

    stdout = stdout if stdout is not None else sys.stdout

    script_dir = os.path.dirname(os.path.abspath(script))

    try:
        depth = get_subpake_depth() + 1
        jobs = get_max_jobs()
    except PakeUninitializedException:
        depth = 0
        jobs = 1

    extra_args = []
    for key, value in _exports.items():
        extra_args += ['-D', key + '=' + str(value)]

    extra_args += ['--s_depth', str(depth), '--jobs', str(jobs)]

    if os.getcwd() != script_dir:
        extra_args += ['--directory', script_dir]

    if silent:
        stdout = subprocess.DEVNULL
    else:
        stdout.flush()

    return subprocess.check_call([sys.executable, script] + extra_args +
                                 list(str(i) for i in args),
                                 stdout=stdout, stderr=subprocess.STDOUT)
