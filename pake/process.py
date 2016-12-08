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


import subprocess
import shlex
import pake.exception


class ExecuteProcessError(pake.exception.PakeException):
    """Raised when a process executed by :py:meth:`pake.process.execute` returns with a non zero status code."""

    def __init__(self, return_code, args, output):
        self._return_code = return_code
        self._args = args
        self._output = output

    @property
    def return_code(self):
        """The process return code."""
        return self._return_code

    @property
    def args(self):
        """The process arguments, this includes the program."""
        return self._args

    @property
    def output(self):
        """The program output."""
        return self.output


def execute(args, ignore_stderr=False, ignore_returncode=False):
    """Execute a system command, yield stdout and stderr as an iterator, stderr is redirected to stdout by default.
    The command is not passed directly to the shell, so you may not use any shell specific syntax like subshells, redirection, pipes ect..

    :param ignore_returncode: If set to True, non zero exit codes will be ignored.
    :param ignore_stderr: If set to True, stderr will be redirected to DEVNULL instead of stdout.

    :param args: A list comprising the command and it's arguments, if you pass something other than
                 a list it will be stringified and tokenized into program + arguments using the shlex module.

    :raise pake.process.ExecuteProcessError: If the executed process completes with a non 0 return code.

    :type args: list or str
    :return: An iterator over the programs lines of output.
    """

    if type(args) is not list:
        args = shlex.split(args)

    p_open = subprocess.Popen(args,
                              stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT if not ignore_stderr else subprocess.DEVNULL,
                              universal_newlines=True)

    stdout = []
    for stdout_line in p_open.stdout:
        if not ignore_returncode:
            stdout.append(stdout_line)
        yield stdout_line

    p_open.stdout.close()
    return_code = p_open.wait()
    if not ignore_returncode and return_code:
        output = ''.join(stdout)
        raise ExecuteProcessError(return_code, args, output=output)