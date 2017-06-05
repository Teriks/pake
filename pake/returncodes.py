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

.. data:: PAKEFILE_NOT_FOUND

    1. Pakefile not found in directory, or specified pakefile does not exist.

.. data:: BAD_ARGUMENTS

    2. Bad combination of command line arguments.

.. data:: NO_TASKS_DEFINED

    3. No tasks defined in pakefile.
    
.. data:: NO_TASKS_SPECIFIED

    4. No tasks specified to run, no default tasks exist.
    
.. data:: TASK_INPUT_NOT_FOUND

    5. A task's input file is missing.
    
.. data:: TASK_OUTPUT_MISSING

    6. A task declares input files but no output files.
    
.. data:: UNDEFINED_TASK

    7. An undefined task was referenced.
    
.. data:: CYCLIC_DEPENDENCY

    8. A cyclic dependency was detected.
    
.. data:: TASK_EXCEPTION

    9. An unhandled exception occurred inside a task.
"""


PAKEFILE_NOT_FOUND = 1
BAD_ARGUMENTS = 2
NO_TASKS_DEFINED = 3
NO_TASKS_SPECIFIED = 4
TASK_INPUT_NOT_FOUND = 5
TASK_OUTPUT_MISSING = 6
UNDEFINED_TASK = 7
CYCLIC_DEPENDENCY = 8
TASK_EXCEPTION = 9
