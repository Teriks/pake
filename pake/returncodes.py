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

    0. Pake ran/exited successfully.

.. data:: ERROR

    1. Generic error, good for use with :py:meth:`pake.terminate` (or **exit()** inside tasks)

.. data:: PAKEFILE_NOT_FOUND

    2. Pakefile not found in directory, or specified pakefile does not exist.

.. data:: BAD_ARGUMENTS

    3. Bad combination of command line arguments, or bad arguments in general.

.. data:: BAD_DEFINE_VALUE

    4. Syntax error while parsing a define value from the **-D/--define** option.

.. data:: NO_TASKS_DEFINED

    5. No tasks defined in pakefile.
    
.. data:: NO_TASKS_SPECIFIED

    6. No tasks specified to run, no default tasks exist.
    
.. data:: TASK_INPUT_NOT_FOUND

    7. One of task's input files/directories is missing.
    
.. data:: TASK_OUTPUT_MISSING

    8. A task declares input files/directories but no output files/directories.
    
.. data:: UNDEFINED_TASK

    9. An undefined task was referenced.
    
.. data:: CYCLIC_DEPENDENCY

    10. A cyclic dependency was detected.

.. data:: TASK_SUBPROCESS_EXCEPTION

    11. An unhandled :py:class:`pake.SubprocessException` was raised inside a task.
    
.. data:: SUBPAKE_EXCEPTION

    12. An exceptional condition occurred running a subpake script.
    

    Or if a pakefile invoked with :py:meth:`pake.subpake` returns non zero and the subpake parameter  **exit_on_error** is set to **True**.

.. data:: TASK_EXCEPTION

    13. An unhandled exception occurred inside a task.

.. data:: STDIN_DEFINES_SYNTAX_ERROR

    14. A syntax error was encountered parsing the defines dictionary passed into
        **stdin** while using the **--stdin-defines** option.

"""

SUCCESS = 0
ERROR = 1
PAKEFILE_NOT_FOUND = 2
BAD_ARGUMENTS = 3
BAD_DEFINE_VALUE = 4
NO_TASKS_DEFINED = 5
NO_TASKS_SPECIFIED = 6
TASK_INPUT_NOT_FOUND = 7
TASK_OUTPUT_MISSING = 8
UNDEFINED_TASK = 9
CYCLIC_DEPENDENCY = 10
TASK_SUBPROCESS_EXCEPTION = 11
SUBPAKE_EXCEPTION = 12
TASK_EXCEPTION = 13
STDIN_DEFINES_SYNTAX_ERROR = 14

