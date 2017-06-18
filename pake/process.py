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
Methods for spawning processes.

.. data:: DEVNULL

    Analog for :py:attr:`subprocess.DEVNULL`

.. data:: STDOUT

    Analog for :py:attr:`subprocess.STDOUT`

.. data:: PIPE

    Analog for :py:attr:`subprocess.PIPE`
"""

import os
import shutil
import signal
import subprocess

import pake
import pake.util

__all__ = [
    'ProcessException',
    'StreamingSubprocessException',
    'CalledProcessException',
    'TimeoutExpired',
    'call',
    'check_call',
    'check_output']


class ProcessException(Exception):
    """Base class for process exceptions."""

    def __init__(self, message):
        super().__init__(message)


class StreamingSubprocessException(ProcessException):
    """
    A base class for sub-process exceptions which need to be able to handle reporting huge
    amounts of process output when a process fails.

    This exception is used as a base class for process exceptions thrown from :py:meth:`pake.subpake`, and the
    process spawning methods in the :py:class:`pake.TaskContext` object.

    .. py:attribute:: cmd
    
        Executed command in list form.
        
    .. py:attribute:: returncode
    
        Process returncode.
        
    .. py:attribute:: message
    
        Optional message from the raising function, may be **None**
        
    .. py:attribute:: filename
    
        Filename describing the file from which the process call was initiated. (might be None)
        
    .. py:attribute:: function_name
    
        Function name describing the function which initiated the process call. (might be None)
        
    .. py:attribute:: line_number
    
        Line Number describing the line where the process call was initiated. (might be None)
    """

    def __init__(self, cmd, returncode,
                 output=None,
                 output_stream=None,
                 message=None):
        """
        :param cmd: Command in list form.
        :param returncode: The command's returncode.

        :param output: (Optional) All output from the command as bytes.

        :param output_stream: (Optional) A file like object containing the process output, at seek(0).
                               By providing this parameter instead of **output**, you give this object permission
                               to close the stream when it is garbage collected or when :py:meth:`pake.StreamingSubprocessException.write_info`
                               is called.  The passed stream should be a text mode stream.

        :param message: Optional exception message.
        """

        super().__init__(message)

        self._output = None
        self._output_stream = None

        if not cmd:
            raise ValueError('cmd list must not be None or empty.')

        if output and type(output) is not bytes:
            raise ValueError("output parameter must be of type 'bytes'")

        if output is not None and output_stream is not None:
            raise ValueError('output and output_stream parameters cannot be used together.')

        c_detail = pake.util.get_pakefile_caller_detail()

        self.message = message
        self.returncode = returncode
        self.cmd = list(cmd)

        self._output = output
        self._output_stream = output_stream

        if c_detail:  # pragma: no cover
            self.filename = c_detail.filename
            self.line_number = c_detail.line_number
            self.function_name = c_detail.function_name
        else:  # pragma: no cover
            self.filename = None
            self.line_number = None
            self.function_name = None

    def __del__(self):
        if self._output_stream is not None:
            self._output_stream.close()
            self._output_stream = None

    @property
    def output(self):  # pragma: no cover
        """
        All output of the process (including **stderr**) as a bytes object
        if it is available, otherwise this property is **None**.
        
        """
        return self._output

    @property
    def output_stream(self):  # pragma: no cover
        """
        All output of the process (including **stderr**) as a file 
        object at **seek(0)** if it is available, otherwise this property is **None**.
        
        If this property is not **None** and you call :py:meth:`pake.TaskSubprocessException.write_info`,
        this property will become **None** because that method reads the stream and disposes of it.
        
        The stream will be a text mode stream.
        
        """
        return self._output_stream

    def write_info(self, file):
        """Writes information about the subprocess exception to a file like object.

        This is necessary over implementing in __str__, because the process output might be 
        drawn from another file to prevent issues with huge amounts of process output.
        
        Calling this method will cause :py:attr:`pake.TaskSubprocessException.output_stream` to
        become **None** if it already isn't.
        
        :param file: The text mode file object to write the information to.
        """

        class_name = pake.util.qualified_name(self)

        template = []
        if self.filename:
            template.append('filename="{}"'.format(self.filename))
        if self.function_name:
            template.append('function_name="{}"'.format(self.function_name))
        if self.line_number:
            template.append('line_number={}'.format(self.line_number))

        if len(template):
            file.write('{myname}({sep}\t{template}{sep}){sep}{sep}'.
                       format(myname=class_name, template=(',' + os.linesep + '\t').join(template), sep=os.linesep))
        else:
            file.write('{myname}(){sep}{sep}'.format(myname=class_name, sep=os.linesep))

        if self.message:
            # noinspection PyTypeChecker
            # os.linesep is a string, * 2 duplicates it twice
            file.write('Message: ' + self.message + (os.linesep * 2))

        file.write('The following command exited with return code: {code}{sep}{sep}{cmd}' \
                   .format(code=self.returncode, sep=os.linesep, cmd=' '.join(self.cmd)))

        if self._output or self._output_stream:
            file.write("{sep}{sep}Command Output: {{{sep}{sep}".format(sep=os.linesep))

            if self._output_stream:
                try:
                    shutil.copyfileobj(self._output_stream, file)
                finally:
                    try:
                        self._output_stream.close()
                    finally:
                        self._output_stream = None
            else:
                file.write(self._output.decode())

            file.write("{sep}{sep}}}{sep}".format(sep=os.linesep))


class TimeoutExpired(ProcessException):
    """This exception is raised when the timeout expires while waiting for a child process.
    
    This exception is only raised by process spawning methods in the :py:mod:`pake.process` module.

    .. py:attribute:: cmd

        Executed command

    .. py:attribute:: timeout

        Timeout in seconds.

    .. py:attribute:: output

        Output of the child process if it was captured by :py:meth:`pake.process.check_output`. Otherwise, None.

    .. py:attribute:: stdout

        Alias for output, for symmetry with stderr.

    .. py:attribute:: stderr

        Stderr output of the child process if it was captured by :py:meth:`pake.process.check_output`. Otherwise, None.

    .. py:attribute:: filename

        Filename describing the file from which the process call was initiated. (might be None)

    .. py:attribute:: function_name

        Function name describing the function which initiated the process call. (might be None)

    .. py:attribute:: line_number

        Line Number describing the line where the process call was initiated. (might be None)
    """

    def __init__(self, cmd, timeout, output=None, stderr=None):
        self.cmd = cmd
        self.timeout = timeout
        self.output = output
        self.stderr = stderr

        c_detail = pake.util.get_pakefile_caller_detail()

        if c_detail:  # pragma: no cover
            self.filename = c_detail.filename
            self.line_number = c_detail.line_number
            self.function_name = c_detail.function_name
        else:  # pragma: no cover
            self.filename = None
            self.line_number = None
            self.function_name = None

    def __str__(self):
        class_name = pake.util.qualified_name(self)

        out_str = ''

        template = []
        if self.filename:  # pragma: no cover
            template.append('filename="{}"'.format(self.filename))
        if self.function_name:  # pragma: no cover
            template.append('function_name="{}"'.format(self.function_name))
        if self.line_number:  # pragma: no cover
            template.append('line_number={}'.format(self.line_number))

        if len(template):  # pragma: no cover
            out_str += ('{myname}({sep}\t{template}{sep}){sep}{sep}'.
                        format(myname=class_name, template=(',' + os.linesep + '\t').join(template), sep=os.linesep))
        else:
            out_str += ('{myname}(){sep}{sep}'.format(myname=class_name, sep=os.linesep))

        out_str += "Command {} timed out after {} seconds".format(self.cmd, self.timeout)

        return out_str

    @property
    def stdout(self):  # pragma: no cover
        return self.output

    @stdout.setter
    def stdout(self, value):  # pragma: no cover
        self.output = value


class CalledProcessException(ProcessException):
    """Raised when :py:meth:`pake.process.check_call` or :py:meth:`pake.process.check_output` and the process returns a non-zero exit status.
    
    This exception is only raised by process spawning methods in the :py:mod:`pake.process` module.

    .. py:attribute:: cmd

        Executed command

    .. py:attribute:: timeout

        Timeout in seconds.

    .. py:attribute:: output

        Output of the child process if it was captured by :py:meth:`pake.process.check_output`. Otherwise, None.

    .. py:attribute:: stdout

        Alias for output, for symmetry with stderr.

    .. py:attribute:: stderr

        Stderr output of the child process if it was captured by :py:meth:`pake.process.check_output`. Otherwise, None.

    .. py:attribute:: filename

        Filename describing the file from which the process call was initiated. (might be None)

    .. py:attribute:: function_name

        Function name describing the function which initiated the process call. (might be None)

    .. py:attribute:: line_number

        Line Number describing the line where the process call was initiated. (might be None)

    """

    def __init__(self, cmd, returncode, output=None, stderr=None):
        self.returncode = returncode
        self.cmd = cmd
        self.output = output
        self.stderr = stderr

        c_detail = pake.util.get_pakefile_caller_detail()

        if c_detail:  # pragma: no cover
            self.filename = c_detail.filename
            self.line_number = c_detail.line_number
            self.function_name = c_detail.function_name
        else:  # pragma: no cover
            self.filename = None
            self.line_number = None
            self.function_name = None

    def __str__(self):
        class_name = pake.util.qualified_name(self)

        out_str = ''

        template = []
        if self.filename:  # pragma: no cover
            template.append('filename="{}"'.format(self.filename))
        if self.function_name:  # pragma: no cover
            template.append('function_name="{}"'.format(self.function_name))
        if self.line_number:  # pragma: no cover
            template.append('line_number={}'.format(self.line_number))

        if len(template):  # pragma: no cover
            out_str += ('{myname}({sep}\t{template}{sep}){sep}{sep}'.
                        format(myname=class_name, template=(',' + os.linesep + '\t').join(template), sep=os.linesep))
        else:
            out_str += ('{myname}(){sep}{sep}'.format(myname=class_name, sep=os.linesep))

        if self.returncode and self.returncode < 0:  # pragma: no cover
            # subprocess module uses this same logic
            try:
                out_str += "Command '{}' died with {}.".format(self.cmd, signal.Signals(-self.returncode))
            except ValueError:
                out_str += "Command '{}' died with unknown signal {}.".format(self.cmd, -self.returncode)
        else:
            out_str += "Command '{}' returned non-zero exit status {}.".format(self.cmd, self.returncode)

        return out_str

    @property
    def stdout(self):  # pragma: no cover
        return self.output

    @stdout.setter
    def stdout(self, value):  # pragma: no cover
        self.output = value


DEVNULL = subprocess.DEVNULL
PIPE = subprocess.PIPE
STDOUT = subprocess.STDOUT


def call(*args, stdin=None, stdout=None, stderr=None, shell=False, timeout=None, **kwargs):
    """Wrapper around :py:meth:`subprocess.call` which allows the same **\*args** call syntax as :py:meth:`pake.TaskContext.call` and friends.

    :param args: Executable and arguments.
    :param stdin: Stdin to feed to the process.
    :param stdout: File to write stdout to.
    :param stderr: File to write stderr to.
    :param shell: Execute in shell mode.
    :param timeout: Program execution timeout value in seconds.

    :raises: :py:exc:`pake.process.TimeoutExpired` If the process does not exit before timeout is up.
    """
    args = pake.util.handle_shell_args(args)
    try:
        return subprocess.call(args, stdin=stdin, stdout=stdout, stderr=stderr, shell=shell, timeout=timeout, **kwargs)
    except subprocess.TimeoutExpired as err:
        raise TimeoutExpired(err.args, err.timeout, err.stdout, err.stdout)


def check_call(*args, stdin=None, stdout=None, stderr=None, shell=False, timeout=None, **kwargs):
    """Wrapper around :py:meth:`subprocess.check_call` which allows the same **\*args** call syntax as :py:meth:`pake.TaskContext.call` and friends.

    :param args: Executable and arguments.
    :param stdin: Stdin to feed to the process.
    :param stdout: File to write stdout to.
    :param stderr: File to write stderr to.
    :param shell: Execute in shell mode.
    :param timeout: Program execution timeout value in seconds.

    :raises: :py:exc:`pake.process.CalledProcessException` If the process exits with a non zero return code.
    :raises: :py:exc:`pake.process.TimeoutExpired` If the process does not exit before timeout is up.
    """
    args = pake.util.handle_shell_args(args)
    try:
        return subprocess.check_call(args, stdin=stdin, stdout=stdout, stderr=stderr, shell=shell, timeout=timeout,
                                     **kwargs)
    except subprocess.TimeoutExpired as err:
        raise TimeoutExpired(err.args, err.timeout, err.stdout, err.stdout)
    except subprocess.CalledProcessError as err:
        raise CalledProcessException(args, err.returncode, output=err.output, stderr=err.stdout)


def check_output(*args, stdin=None, stderr=None, shell=False, timeout=None, **kwargs):
    """Wrapper around :py:meth:`subprocess.check_output` which allows the same **\*args** call syntax as :py:meth:`pake.TaskContext.call` and friends.

    :param args: Executable and arguments.
    :param stdin: Stdin to feed to the process.
    :param stderr: File to write stderr to.
    :param shell: Execute in shell mode.
    :param timeout: Program execution timeout value in seconds.

    :raises: :py:exc:`pake.process.CalledProcessException` If the process exits with a non zero return code.
    :raises: :py:exc:`pake.process.TimeoutExpired` If the process does not exit before timeout is up.
    """
    args = pake.util.handle_shell_args(args)
    try:
        return subprocess.check_output(args, stdin=stdin, stderr=stderr, shell=shell, timeout=timeout, **kwargs)
    except subprocess.TimeoutExpired as err:
        raise TimeoutExpired(err.args, err.timeout, err.stdout, err.stdout)
    except subprocess.CalledProcessError as err:
        raise CalledProcessException(args, err.returncode, output=err.output, stderr=err.stdout)
