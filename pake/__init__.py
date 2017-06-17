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

"""

.. py:attribute:: EXPORTS

A dictionary object containing all current exports,
you are free to modify this dictionary directly.

See: :py:meth:`pake.export` and :py:meth:`pake.subpake`.

Be careful and make sure it remains a dictionary object.

"""

__author__ = 'Teriks'
__copyright__ = 'Copyright (c) 2016 Teriks'
__license__ = 'Three Clause BSD'
__version__ = '0.14.0.0a1'

# __version__ and friends needs to be above the imports, the
# metadata above may be used elsewhere by the modules that follow

from .filehelper import FileHelper

from .graph import CyclicGraphException

from .pake import \
    pattern, \
    glob, \
    Pake, \
    TaskContext, \
    MultitaskContext, \
    TaskGraph, \
    UndefinedTaskException, \
    RedefinedTaskException, \
    TaskException, \
    TaskExitException, \
    InputNotFoundException, \
    MissingOutputsException

from .program import \
    run, \
    init, \
    is_init, \
    terminate, \
    PakeUninitializedException, \
    get_subpake_depth, \
    get_max_jobs, \
    get_init_file, \
    get_init_dir, \
    TerminateException, \
    de_init

from .pake import TaskSubprocessException
from .subpake import subpake, export, SubpakeException, EXPORTS

__all__ = [
    'init',
    'de_init',
    'is_init',
    'run',
    'terminate',
    'get_subpake_depth',
    'get_max_jobs',
    'get_init_file',
    'get_init_dir',
    'export',
    'EXPORTS',
    'subpake',
    'Pake',
    'TaskContext',
    'MultitaskContext',
    'TaskGraph',
    'pattern',
    'glob',
    'FileHelper',
    'TaskException',
    'TaskExitException',
    'TaskSubprocessException',
    'InputNotFoundException',
    'MissingOutputsException',
    'UndefinedTaskException',
    'RedefinedTaskException',
    'PakeUninitializedException',
    'CyclicGraphException',
    'SubpakeException',
    'TerminateException',
]
