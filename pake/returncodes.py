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
Pake return codes.

.. data:: SUCCESS

    0. Pake ran successfully.

.. data:: PAKEFILE_NOT_FOUND

    1. Pakefile not found in directory, or specified pakefile does not exist.

.. data:: BAD_ARGUMENTS

    2. Bad combination of command line arguments.

.. data:: BAD_DEFINE_VALUE

    3. Syntax error while parsing a define value from the -D/--define option.

.. data:: NO_TASKS_DEFINED

    4. No tasks defined in pakefile.
    
.. data:: NO_TASKS_SPECIFIED

    5. No tasks specified to run, no default tasks exist.
    
.. data:: TASK_INPUT_NOT_FOUND

    6. One of task's input files/directories is missing.
    
.. data:: TASK_OUTPUT_MISSING

    7. A task declares input files/directories but no output files/directories.
    
.. data:: UNDEFINED_TASK

    8. An undefined task was referenced.
    
.. data:: CYCLIC_DEPENDENCY

    9. A cyclic dependency was detected.

.. data:: TASK_SUBPROCESS_EXCEPTION

    10. An unhandled :py:class:`pake.SubprocessException` was raised inside a task.
    
.. data:: SUBPAKE_EXCEPTION

    11. An exceptional condition occurred running a subpake script.
    
    Occurs if :py:meth:`pake.TaskContext.subpake` encounters a :py:class:`pake.SubprocessException` inside a task.

    Or if a pakefile invoked with :py:meth:`pake.subpake` returns non zero and the subpake parameter  **exit_on_error** is set to **True**.

.. data:: TASK_EXCEPTION

    12. An unhandled exception occurred inside a task.
"""

SUCCESS = 0
PAKEFILE_NOT_FOUND = 1
BAD_ARGUMENTS = 2
BAD_DEFINE_VALUE = 3
NO_TASKS_DEFINED = 4
NO_TASKS_SPECIFIED = 5
TASK_INPUT_NOT_FOUND = 6
TASK_OUTPUT_MISSING = 7
UNDEFINED_TASK = 8
CYCLIC_DEPENDENCY = 9
TASK_SUBPROCESS_EXCEPTION = 10
SUBPAKE_EXCEPTION = 11
TASK_EXCEPTION = 12

