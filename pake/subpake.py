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

import codecs
import os.path
import shutil
import subprocess
import sys

import os
import tempfile

import pake
import pake.process
import pake.program
import pake.util
import pake.returncodes as returncodes
import pake.conf

__all__ = ['export', 'subpake', 'SubpakeException', 'EXPORTS']

EXPORTS = dict()
"""
A dictionary object containing all current exports by name,
you are free to modify this dictionary directly.

See: :py:meth:`pake.export`, :py:meth:`pake.subpake` and :py:meth:`pake.TaskContext.subpake`.

Be careful and make sure it remains a dictionary object.

Export values must be able to **repr()** into parsable python literals.
"""


class SubpakeException(pake.process.StreamingSubprocessException):
    """
    Raised upon encountering a non-zero return code from a subpake invocation.

    This exception is raised from both :py:meth:`pake.subpake` and :py:meth:`pake.TaskContext.subpake`.

    .. py:attribute:: cmd

        Executed subpake command in list form.

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

        :param output_stream: (Optional) A file like object containing the process output, at **seek(0)**.
                               By providing this parameter instead of **output**, you give this object permission
                               to close the stream when it is garbage collected or when :py:meth:`pake.SubpakeException.write_info` is called.

        :param message: Optional exception message.
        """
        super().__init__(cmd=cmd,
                         returncode=returncode,
                         output=output,
                         output_stream=output_stream,
                         message=message)


def export(name, value):  # pragma: no cover
    """
    Exports a define that can be retrieved in subpake scripts via :py:func:`pake.Pake.get_define`.

    This function can redefine the value of an existing export as well.

    The :py:attr:`pake.EXPORTS` dictionary can also be manipulated directly.

    Export values must be able to **repr()** into parsable python literals.
    
    :param name: The name of the define.
    :param value: The value of the define.
    """

    EXPORTS[name] = value


def subpake(*args,
            stdout=None,
            silent=False,
            ignore_errors=False,
            exit_on_error=True,
            readline=True,
            collect_output=False,
            collect_output_lock=None):
    """
    Execute a ``pakefile.py`` script, changing directories if necessary.
    
    This function should not be used inside tasks, use: :py:meth:`pake.TaskContext.subpake` instead.
    A :py:meth:`pake.TaskContext` instance is passed into the single parameter of each task, usually named **ctx**.

    :py:meth:`pake.subpake` allows similar syntax to :py:meth:`pake.TaskContext.call` for its **\*args** parameter.
    
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
    

    :param args: The script, and additional arguments to pass to the script.
                 You may pass the command words as a single iterable, a string, or as
                 variadic arguments.

    :param stdout: The file output to write all of the pakefile's output to. (defaults to :py:attr:`pake.conf.stdout`)
                   The pakefile's **stderr** will be redirected to its **stdout**, so the passed file object will
                   receive all output from the pakefile including error messages.

    :param silent: Whether or not to silence all output from the subpake script.

    :param ignore_errors: If this is **True**, this function will never call **exit** or throw
                          :py:exc:`pake.SubpakeException` if the executed pakefile returns with a
                          non-zero exit code.  It will instead return the exit code from the
                          subprocess to the caller.
    
    :param exit_on_error: Whether or not to print to :py:attr:`pake.conf.stderr` and immediately
                          call **exit** if the pakefile script encounters an error.  The value
                          of this parameter will be disregarded when **ignore_errors=True**.

    :param readline: Whether or not to use **readline** for reading process output when **ignore_errors**
                     and **silent** are **False**,  this is necessary for live output in that case. When live
                     output to a terminal is not required, such as when writing to a file on disk, setting
                     this parameter to **False** results in more efficient writes. This parameter defaults to **True**

    :param collect_output: Whether or not to collect all subpake output to a temporary file
                           and then write it incrementally to the **stdout** parameter when
                           the process finishes.  This can help prevent crashes when dealing with lots of output.
                           When you pass **True** to this parameter, the **readline** parameter is ignored.
                           See: :ref:`Output synchronization with ctx.call & ctx.subpake`

    :param collect_output_lock: If you provide a lockable object such as :py:class:`threading.Lock` or
                                :py:class:`threading.RLock`, The subpake function will try to acquire the lock before
                                incrementally writing to the **stdout** parameter when **collect_output=True**.
                                The lock you pass is only required to implement a context manager and be usable
                                in a **with** statement, no methods are called on the lock. :py:meth:`pake.TaskContext.subpake`
                                will pass :py:meth:`pake.TaskContext.io_lock` for you if **collect_output=True**.

    :raises: :py:exc:`ValueError` if no command + optional command arguments are provided.
    :raises: :py:exc:`FileNotFoundError` if the first argument *(the pakefile)* is not found.
    :raises: :py:exc:`pake.SubpakeException` if the called pakefile script encounters an error
             and the following is true: **exit_on_error=False** and **ignore_errors=False**.

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

    extra_args = ['--_subpake_depth', str(depth), '--stdin-defines']

    if os.getcwd() != script_dir:
        extra_args += ['--directory', script_dir]

    args = [sys.executable, script] + extra_args + list(str(i) for i in args)

    if ignore_errors:
        return _subpake_ignore_errors(
            args=args,
            stdout=stdout,
            silent=silent,
            collect_output=collect_output,
            collect_output_lock=collect_output_lock)

    return _subpake_with_errors(args=args,
                                stdout=stdout,
                                silent=silent,
                                exit_on_error=exit_on_error,
                                readline=readline,
                                collect_output=collect_output,
                                collect_output_lock=collect_output_lock)


def _subpake_ignore_errors(args, stdout, silent, collect_output, collect_output_lock):
    if silent:
        p_stdout = subprocess.DEVNULL
    elif collect_output:
        p_stdout = tempfile.TemporaryFile(mode='w+', newline='\n')
    else:
        p_stdout = stdout
    try:
        with subprocess.Popen(args,
                              stdout=p_stdout,
                              stderr=subprocess.STDOUT,
                              stdin=subprocess.PIPE,
                              universal_newlines=True) as process:

            process.stdin.write(repr(EXPORTS))
            process.stdin.flush()
            process.stdin.close()

            try:
                return process.wait()
            except:  # pragma: no cover
                process.kill()
                process.wait()
                raise
    finally:
        if collect_output and not silent:
            if collect_output_lock:
                with collect_output_lock:
                    shutil.copyfileobj(p_stdout, stdout)
            else:
                shutil.copyfileobj(p_stdout, stdout)
            p_stdout.close()


def _subpake_with_errors(args, stdout, silent, exit_on_error, readline, collect_output, collect_output_lock):
    with subprocess.Popen(args,
                          stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT,
                          stdin=subprocess.PIPE,
                          universal_newlines=True) as process:

        process.stdin.write(repr(EXPORTS))
        process.stdin.flush()
        process.stdin.close()

        output_copy_buffer = tempfile.TemporaryFile(mode='w+', newline='\n')

        def do_collect_output(seek0_before, seek0_after):
            if seek0_before:
                output_copy_buffer.seek(0)

            if collect_output and not silent:
                if collect_output_lock:
                    with collect_output_lock:
                        shutil.copyfileobj(output_copy_buffer, stdout)
                else:
                    shutil.copyfileobj(output_copy_buffer, stdout)

                if seek0_after:
                    output_copy_buffer.seek(0)

        try:
            if not silent:
                pake.util.copyfileobj_tee(process.stdout, [stdout, output_copy_buffer], readline=readline)
            else:  # pragma: no cover
                # Only need to copy to the output_copy_buffer, for error reporting
                # when silent = True
                shutil.copyfileobj(process.stdout, output_copy_buffer)

        except:  # pragma: no cover
            do_collect_output(seek0_before=True, seek0_after=False)
            output_copy_buffer.close()
            raise
        finally:
            process.stdout.close()

        try:
            exitcode = process.wait()
        except:  # pragma: no cover
            do_collect_output(seek0_before=True, seek0_after=False)
            output_copy_buffer.close()
            process.kill()
            process.wait()
            raise

        if exitcode:
            output_copy_buffer.seek(0)
            do_collect_output(seek0_before=False, seek0_after=True)

            # Giving up responsibility to close output_copy_buffer here
            ex = SubpakeException(cmd=args,
                                  returncode=exitcode,
                                  output_stream=output_copy_buffer,
                                  message='A pakefile invoked by pake.subpake exited with a non-zero return code.')

            if exit_on_error:
                ex.write_info(file=pake.conf.stderr)
                exit(returncodes.SUBPAKE_EXCEPTION)
            else:
                raise ex

        do_collect_output(seek0_before=True, seek0_after=False)
        output_copy_buffer.close()
        return exitcode
