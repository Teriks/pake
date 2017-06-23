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
import shutil
import subprocess
import tempfile
import threading
import traceback
from functools import wraps
from glob import iglob as glob_iglob
from contextlib import contextmanager

import os

import pake
import pake.conf
import pake.graph
import pake.process
import pake.util
import pake.returncodes

from concurrent.futures import \
    ThreadPoolExecutor, \
    wait as futures_wait, \
    Executor, Future

from os import path

from pake.process import StreamingSubprocessException

__all__ = ['pattern',
           'glob',
           'Pake',
           'TaskContext',
           'MultitaskContext',
           'TaskGraph',
           'UndefinedTaskException',
           'RedefinedTaskException',
           'TaskException',
           'TaskExitException',
           'InputNotFoundException',
           'MissingOutputsException',
           'AggregateException']


class TaskException(Exception):
    """
    Raised by :py:meth:`pake.Pake.run` if an exception is encountered running/visiting a task.
    
    .. py:attribute:: exception
    
        The exception raised.
        
    .. py:attribute:: task_name
    
        The name of the task which the exception was raised in.
        
    .. py:attribute:: exception_name
    
        The fully qualified name of the exception object.
    """

    def __init__(self, task_name, exception):
        """
        :param task_name: The name of the task that raised the exception.
        :param exception: Reference to the exception object that raised.
        """

        self.exception_name = pake.util.qualified_name(exception)

        super().__init__('Exception "{exc}" was raised within task "{task}".'
                         .format(exc=self.exception_name, task=task_name))

        self.exception = exception

    def print_traceback(self, file=None):
        """
        Print the traceback of the exception that was raised inside the task to a file object.
        
        :param file: The file object to print to.  Default value is :py:attr:`pake.conf.stderr` if **None** is specified.
        """

        traceback.print_exception(
            type(self.exception),
            self.exception,
            self.exception.__traceback__,
            file=pake.conf.stderr if file is None else file)


class TaskExitException(Exception):
    """
    Raised when :py:exc:`SystemExit` or an exception derived from it is thrown inside a task.

    This is raised from :py:meth:`pake.Pake.run` when **exit()**, :py:meth:`pake.terminate`,
    or :py:meth:`pake.Pake.terminate` is called inside of a task.
    
    .. py:attribute:: task_name
       
       The name of the task in which **exit** was called.

    .. py:attribute:: exception
       
       Reference to the :py:exc:`SystemExit` exception which caused this exception to be raised.

    """

    def __init__(self, task_name, exception):
        """
        
        :param task_name: The name of the task that raised the :py:exc:`SystemExit` exception.
        :param exception: Reference to the :py:exc:`SystemExit` or derived exception raised inside the task.
        """
        super().__init__('Exit exception "{cls}" with return-code({code}) was raised in task "{task}".'
                         .format(cls=pake.util.qualified_name(exception),
                                 code=exception.code,
                                 task=task_name))

        self.task_name = task_name
        self.exception = exception

    @property
    def return_code(self):
        """The return code passed to **exit()** inside the task."""
        return self.exception.code

    def print_traceback(self, file=None):
        """
        Print the traceback of the :py:exc:`SystemExit` exception that was raised inside the task to a file object.
        
        :param file: The file object to print to.  Default value is :py:attr:`pake.conf.stderr` if **None** is specified.
        """

        traceback.print_exception(
            type(self.exception),
            self.exception,
            self.exception.__traceback__,
            file=pake.conf.stderr if file is None else file)


class MissingOutputsException(Exception):
    """
    Raised by :py:meth:`pake.Pake.run` and :py:meth:`pake.Pake.dry_run` if a task declares input files without
    specifying any output files/directories.
    """

    def __init__(self, task_name):
        super().__init__(
            'Error: Task "{}" defines inputs with no outputs, this is not allowed.'.format(task_name)
        )


class InputNotFoundException(Exception):
    """
    Raised by :py:meth:`pake.Pake.run` and :py:meth:`pake.Pake.dry_run` if a task with inputs
    declared cannot find an input file/directory on disk.
    """

    def __init__(self, task_name, output_name):
        super().__init__(
            'Error: Could not find input file/directory "{}" used by task "{}".'.format(output_name, task_name)
        )


class UndefinedTaskException(Exception):
    """Raised on attempted lookup/usage of an unregistered task function or task name.
    
    .. py:attribute:: task_name
    
        The name of the referenced task.
    """

    def __init__(self, task_name):
        super().__init__('Error: Task "{}" is undefined.'.format(task_name))
        self.task_name = task_name


class RedefinedTaskException(Exception):
    """Raised on registering a duplicate task.
    
    .. py:attribute:: task_name
    
        The name of the redefined task.
    """

    def __init__(self, task_name):
        super().__init__('Error: Task "{}" has already been defined.'
                         .format(task_name))
        self.task_name = task_name


def _handle_task_exception(ctx, exception):
    if isinstance(exception, SystemExit):
        # Handle exit() within tasks in a more specific manner
        raise TaskExitException(ctx.name, exception)

    if isinstance(exception, InputNotFoundException) or isinstance(exception, MissingOutputsException):
        # These are raised inside the task when
        # the task runs and does file detection, they provides information
        # which includes the task name the exception occurred in as well
        # as the name of the file that was missing.  These are handled by pake.run(...) (the library method)
        # which displays the error to the user, these exceptions will come directly out of
        # Pake.run(...) (the object method) as they are.
        raise exception

    raise TaskException(ctx.name, exception)


def _wait_futures_and_raise(futures):
    futures_wait(futures)
    for i in futures:
        err = i.exception()
        if err:
            raise err


class TaskContext:
    """Contextual object passed to each task.
    
    .. py:attribute:: inputs
    
        All file inputs, or an empty list.  
        
       **Note:** 
       
       Not available outside of a task, may only be used while a task is executing.
        
    .. py:attribute:: outputs
    
        All file outputs, or an empty list.
        
       **Note:** 
       
       Not available outside of a task, may only be used while a task is executing.
       
    .. py:attribute:: outdated_inputs
    
        All changed file inputs (or inputs who's corresponding output is missing), or an empty list.
        
       **Note:** 
       
       Not available outside of a task, may only be used while a task is executing.
        
    .. py:attribute:: oudated_outputs
    
        All out of date file outputs, or an empty list
        
       **Note:** 
       
       Not available outside of a task, may only be used while a task is executing.
    """

    def __init__(self, pake_obj, node):
        """
        :param pake_obj: Instance of :py:class:`pake.Pake`.
        :param node: Instance of :py:class:`pake.TaskGraph`.
        """

        self._pake = pake_obj
        self._node = node
        self._future = None
        self._io = None
        self._io_lock = threading.RLock()
        self.inputs = []
        self.outputs = []
        self.outdated_inputs = []
        self.outdated_outputs = []

    @property
    def io_lock(self):
        """
        A contextual lock for acquiring exclusive access to :py:attr:`pake.TaskContext.io`.

        This context manager acquires an internal lock for :py:attr:`pake.Pake.stdout`
        that exists on the :py:class:`pake.Pake` object when :py:attr:`pake.Pake.max_jobs` is **1**.

        Otherwise, it will acquire a lock for :py:attr:`pake.TaskContext.io` that
        exists inside of the task context, since the task will be buffering output
        to an individual temporary file when :py:attr:`pake.Pake.max_jobs` is greater
        than **1**.

        If :py:attr:`pake.Pake.sync_output` is **False**, the context manager
        returned by this property will not attempt to acquire any lock.

        :return: A context manager object that can be used in a **with** statement.
        """

        if self.pake.max_jobs > 1:
            # Lock the task IO queue, since that
            # is what is being written to
            output_lock = self._io_lock
        else:
            # Lock the pake instances stdout, since
            # we are writing directly to it if
            # multiple jobs are not running
            output_lock = self.pake._stdout_lock

        @contextmanager
        def context():
            if self.pake.sync_output:
                with output_lock:
                    yield
            else:
                yield

        return context()

    def multitask(self, aggregate_exceptions=False):
        """
        Returns a contextual object for submitting work to pake's current thread pool.

        .. code-block:: python

           @pk.task(i=pake.glob('src/*.c'), o=pake.pattern('obj/%.o'))
               def build_c(ctx):
                   with ctx.multitask() as mt:
                       for i, o in ctx.outdated_pairs:
                           mt.submit(ctx.call, ['gcc', '-c', i, '-o', o])


        At the end of the **with** statement, all submitted tasks are simultaneously waited on.

        The tasks will be checked in order of submission for exceptions, if an exception is
        found then the default behavior is to re-raise it on the foreground thread.

        You can specify **aggregate_exceptions=True** if you want all of the exceptions
        to be collected into a :py:class:`pake.AggregateException`, which will then be raised
        when :py:meth:`pake.MultitaskContext.shutdown` is called with **wait=True**.


        **shutdown** is called at the end of your **with** statement with the **wait**
        parameter set to **True**.


        :param aggregate_exceptions: Whether or not the returned executor should collect
                                     exceptions from all tasks that ended due to an exception,
                                     and then raise a :py:class:`pake.AggregateException` containing
                                     them upon shutdown.

        :returns: :py:class:`pake.MultitaskContext`
        """

        return MultitaskContext(self,
                                aggregate_exceptions=aggregate_exceptions)

    @property
    def outdated_pairs(self):
        """
        Short hand for: ``zip(ctx.outdated_inputs, ctx.outdated_outputs)``
           
        Returns a generator object over outdated (input, output) pairs.
       
        This is only useful when the task has the same number of inputs as it does outputs.

        Example:

        .. code-block:: python
          
           @pk.task(i=pake.glob('src/*.c'), o=pake.pattern('obj/%.o'))
           def build_c(ctx):
               for i, o in ctx.outdated_pairs:
                   ctx.call(['gcc', '-c', i, '-o', o])
                  
             
        **Note:** 
       
        Not available outside of a task, may only be used while a task is executing.

        """
        return zip(self.outdated_inputs, self.outdated_outputs)

    @property
    def func(self):
        """
        Task function reference.
        
        This function will be an internal wrapper around
        the one you specified and you should not call it.
        
        There is not currently a way to get a reference
        to your actual unwrapped task function from the
        :py:class:`pake.Pake` object or elsewhere.
        
        However since the :py:meth:`functools.wraps` decorator is used
        when wrapping your task function, metadata such as **func.__doc__** 
        will be maintained on this function reference.
        """
        return self.node.func

    @property
    def name(self):
        """The task name.

        :return: The task name, as a string.
        """
        return self._node.name

    @property
    def io(self):  # pragma: no cover
        """
        The task IO file stream, a file like object that is only open for writing during a tasks execution.
        
        Any output to be displayed for the task should be written to this file object.
        
        This file object is a text mode stream, it can be used with the built in **print** function
        and other methods that can write text data to a file like object.

        When you run pake with more than one job, this will be a reference to a temporary file unless
        :py:attr:`pake.Pake.sync_output` is **False** (It is **False** when **--no-sync-output** is used on the command line).

        The temporary file queues up task output when in use, and the task context acquires a lock
        and writes it incrementally to :py:attr:`pake.Pake.stdout` when the task finishes. This is
        done to avoid having concurrent task's writing interleaved output to :py:attr:`pake.Pake.stdout`.

        If you run pake with only 1 job or :py:attr:`pake.Pake.sync_output` is **False**, this
        property will return a direct reference to :py:attr:`pake.Pake.stdout`.
        """
        return self._io

    def print(self, *args, **kwargs):
        """Prints to the task IO file stream using the builtin print function.

        Shorthand for: ``print(..., file=ctx.io)``
        """
        kwargs.pop('file', None)

        with self.io_lock:
            print(*args, file=self._io, **kwargs)

    def subpake(self, *args, silent=False, ignore_errors=False, collect_output=False):
        """
        Run :py:func:`pake.subpake` and direct all output to the task IO file stream.

        :param args: The script, and additional arguments to pass to the script.
                     You may pass a list, or use variadic arguments.

        :param silent: If **True**, avoid printing output from the sub-pakefile to the tasks IO queue.

        :param ignore_errors: If this is **True**, this function will not throw :py:exc:`pake.SubpakeException` if
                              the executed pakefile returns with a non-zero exit code.  It will instead return the
                              exit code from the subprocess to the caller.

        :param collect_output: Whether or not to collect all subpake output to a temporary file
                               and then incrementally write it back to :py:class:`pake.TaskContext.io`
                               in a synchronized fashion, so that all command output is guaranteed to
                               come in order and not become interleaved with the output of other tasks
                               when using :py:meth:`pake.TaskContext.multitask`.
                               See: :ref:`Output synchronization with ctx.call & ctx.subpake`

        :raises: :py:exc:`ValueError` if no command + optional command arguments are provided.

        :raises: :py:exc:`FileNotFoundError` if the first argument (the pakefile) is not found.

        :raises: :py:exc:`pake.SubpakeException` if the called pakefile script encounters an
                 error and **ignore_errors=False** .

        """

        collect_output_lock = None if collect_output is False else self.io_lock

        # Suggest readline usage when running without
        # multiple jobs, for live output to the console
        # readline parameter is ignored when collect_output is True
        readline = self.pake.threadpool is None

        return pake.subpake(*args,
                            stdout=self._io, silent=silent,
                            ignore_errors=ignore_errors,
                            call_exit=False,
                            readline=readline,
                            collect_output=collect_output,
                            collect_output_lock=collect_output_lock)

    @staticmethod
    def check_call(*args, stdin=None, shell=False, ignore_errors=False):
        """
        Get the return code of an executed system command, without printing 
        any output to the tasks IO queue by default.
        
        None of the process's **stdout/stderr** will go to the task IO queue, 
        and the command that was run will not be printed either.
        
        This function raises :py:exc:`pake.TaskSubprocessException` on non-zero
        return codes by default.  
        
        You should pass pass **ignore_errors=True** if you want this method to return 
        the non-zero value, or instead catch the exception and get the return code from it.
        
        **Note:**
        
        :py:attr:`pake.TaskSubprocessException.output` and :py:attr:`pake.TaskSubprocessException.output_stream`
        will **not** be available in the exception if you handle it.
        
        :raises: :py:exc:`pake.TaskSubprocessException` if **ignore_errors** is **False**
                 and the process exits with a non-zero return code.
                 
        :raises: :py:exc:`OSError` (commonly) if a the executed command or file does not exist.
                 This exception will still be raised even if **ignore_errors** is **True**.
                 
        :raises: :py:exc:`ValueError` if no command + optional arguments are provided.
        
        :param args: Command arguments, same syntax as :py:meth:`pake.TaskContext.call`
        :param stdin: Optional file object to pipe into the called process's **stdin**.
        :param shell: Whether or not to use the system shell for execution of the command.
        :param ignore_errors: Whether to ignore non-zero return codes and return the code anyway.
        :return: Integer return code.
        """

        args = pake.util.handle_shell_args(args)

        if len(args) < 1:
            raise ValueError('Not enough arguments provided.  '
                             'Must provide at least one argument, IE. the command.')

        try:
            return subprocess.check_call(args, stdin=stdin, shell=shell,
                                         stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as err:
            if ignore_errors:
                return err.returncode
            raise TaskSubprocessException(cmd=args,
                                          returncode=err.returncode,
                                          message='An error occurred while executing a system '
                                                  'command inside a pake task.')

    @staticmethod
    def check_output(*args, stdin=None, shell=False, ignore_errors=False):
        """
        Return the output of a system command as a bytes object, without printing
        its **stdout/stderr** to the task IO queue.  The process command line that
        was run will not be printed either.
        
        The returned bytes output will include **stdout** and **stderr** combined, and 
        it can be decoded into a string by using the **decode()** method on pythons built 
        in **bytes** object.
        
        This function raises :py:exc:`pake.TaskSubprocessException` on non-zero
        return codes by default.  
        
        If you want to return possible error output from the called process's **stderr** 
        you should pass **ignore_errors=True**, or instead catch the exception and get the 
        process output from it.
        
        **Note:**
        
        :py:attr:`pake.TaskSubprocessException.output` will be available for retrieving
        the output of the process if you handle the exception, the value will be 
        all of **stdout/stderr** as a **bytes** object that must be decoded into a string.
        
        :raises: :py:exc:`pake.TaskSubprocessException` if **ignore_errors** is False
                 and the process exits with a non-zero return code.

        :raises: :py:exc:`OSError` (commonly) if a the executed command or file does not exist.
                 This exception will still be raised even if **ignore_errors** is **True**.
                 
        :raises: :py:exc:`ValueError` if no command + optional arguments are provided.
        
        :param args: Command arguments, same syntax as :py:meth:`pake.TaskContext.call`
        :param stdin: Optional file object to pipe into the called process's **stdin**.
        :param shell: Whether or not to use the system shell for execution of the command.
        :param ignore_errors: Whether to ignore non-zero return codes and return the output anyway.
        :return: Bytes object (program output data)
        """

        args = pake.util.handle_shell_args(args)

        if len(args) < 1:
            raise ValueError('Not enough arguments provided.  '
                             'Must provide at least one argument, IE. the command.')

        try:
            return subprocess.check_output(args, shell=shell, stdin=stdin, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as err:
            if ignore_errors:
                return err.output
            raise TaskSubprocessException(cmd=args,
                                          returncode=err.returncode,
                                          output=err.output,
                                          message='An error occurred while executing a system '
                                                  'command inside a pake task.')

    def call(self, *args, stdin=None, shell=False, ignore_errors=False, silent=False, print_cmd=True,
             collect_output=False):
        """
        Calls a sub process and returns its return code.
         
        all **stdout/stderr** is written to the task IO file stream.  The full command line 
        which was used to start the process is printed to the task IO queue before the 
        output of the command, unless **print_cmd=False**.
        
        
        You can prevent the process from sending its **stdout/stderr** to the task IO queue
        by specifying **silent=True**
        
        
        If a process returns a non-zero return code, this method will raise 
        :py:exc:`pake.TaskSubprocessException` by default.
        
        If you want the value of non-zero return codes to be returned then you must
        pass **ignore_errors=True** to prevent :py:exc:`pake.TaskSubprocessException` from
        being thrown, or instead catch the exception and get the return code from it.
        
        
        **Note:**
        
        :py:attr:`pake.TaskSubprocessException.output_stream` will be available for retrieving
        the output of the process (**stdout** and **stderr** combined) if you handle the exception,
        the file stream will be a text mode file object at **seek(0)**.
        

        Example:
        
        .. code-block:: python
           
           # strings are parsed using shlex.parse
           
           ctx.call('gcc -c test.c -o test.o')
           
           ctx.call('gcc -c {} -o {}'.format('test.c', 'test.o'))
           
           # pass the same command as a list
           
           ctx.call(['gcc', '-c', 'test.c', '-o', 'test.o'])
           
           # pass the same command using the variadic argument *args
           
           ctx.call('gcc', '-c', 'test.c', '-o', 'test.o')
           
           # non string iterables in command lists will be flattened, 
           # allowing for this syntax to work.  ctx.inputs and ctx.outputs
           # are both list objects, but anything that is iterable will work
           
           ctx.call(['gcc', '-c', ctx.inputs, '-o', ctx.outputs])
           
           
           # Fetch a non-zero return code without a 
           # pake.TaskSubprocessException.  ctx.check_call
           # is better used for this task.
           
           code = ctx.call('which', 'am_i_here', 
                           ignore_errors=True,  # Ignore errors (non-zero return codes)
                           print_cmd=False,   # Don't print the command line executed
                           silent=True)  # Don't print stdout/stderr to task IO
        
        :param args: The process command/executable, and additional arguments to pass
                     to the process. You may pass the command words as a single iterable,
                     a string, or as variadic arguments.

        :param stdin: Optional file object to pipe into the called process's **stdin**.
        :param shell: Whether or not to use the system shell for execution of the command.
        :param ignore_errors: Whether or not to raise a :py:exc:`pake.TaskSubprocessException` on non-zero exit codes.
        
        :param silent: Whether or not to silence **stdout/stderr** from the command.  This does keep pake
                       from printing what command line was run, see the **print_cmd** argument for that.
                       
        :param print_cmd: Whether or not to print the executed command line to the tasks output.
                          The **silent** argument will not keep pake from printing the executed command,
                          only this argument can do that.

        :param collect_output: Whether or not to collect all process output to a temporary file
                               and then incrementally write it back to :py:class:`pake.TaskContext.io`
                               in a synchronized fashion, so that all command output is guaranteed to
                               come in order and not become interleaved with the output of other tasks
                               when using :py:meth:`pake.TaskContext.multitask`.
                               See: :ref:`Output synchronization with ctx.call & ctx.subpake`
        
        :returns: The process return code.
        
        :raises: :py:exc:`pake.TaskSubprocessException` if *ignore_errors* is *False* and the process exits with a non-zero exit code.
        
        :raises: :py:exc:`OSError` (commonly) if a the executed command or file does not exist.
         This exception will still be raised even if **ignore_errors** is **True**.
         
        :raises: :py:exc:`ValueError` if no command + optional arguments are provided.
        """
        args = pake.util.handle_shell_args(args)

        if len(args) < 1:
            raise ValueError('Not enough arguments provided.  '
                             'Must provide at least one argument, IE. the command.')

        if ignore_errors:
            return self._call_ignore_errors(args=args,
                                            stdin=stdin,
                                            shell=shell,
                                            silent=silent,
                                            print_cmd=print_cmd,
                                            collect_output=collect_output)

        # Log a copy to disk, for possible error reporting later
        return self._call_with_errors(args=args,
                                      stdin=stdin,
                                      shell=shell,
                                      silent=silent,
                                      print_cmd=print_cmd,
                                      collect_output=collect_output)

    def _call_with_errors(self, args, stdin, shell, silent, print_cmd, collect_output):
        with subprocess.Popen(args,
                              stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT,
                              stdin=stdin, shell=shell,
                              universal_newlines=True) as process:

            output_copy_buffer = tempfile.TemporaryFile(mode='w+', newline='\n')

            def do_collect_output(seek0_before, seek0_after):
                if seek0_before:
                    output_copy_buffer.seek(0)

                if collect_output and not silent:
                    with self.io_lock:
                        shutil.copyfileobj(output_copy_buffer, self._io)

                    if seek0_after:
                        output_copy_buffer.seek(0)

            try:
                if not silent and not collect_output:
                    # Use readline for live output to self._io when max jobs == 1
                    # The task is on the current thread, and self._io is a direct
                    # unbuffered reference this.stdout.  Otherwise copy fix sized
                    # chunks of data until EOF

                    if print_cmd:
                        self.print(' '.join(args))

                    pake.util.copyfileobj_tee(process.stdout,
                                              [self._io, output_copy_buffer],
                                              readline=self.pake.max_jobs == 1)
                else:

                    # Only need to copy to the output_copy_buffer, for error
                    # reporting when silent = True, and incremental write
                    # when collect_output = True

                    if collect_output and print_cmd:
                        output_copy_buffer.write(' '.join(args) + '\n')
                    elif print_cmd:
                        self.print(' '.join(args))

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
                raise TaskSubprocessException(cmd=args,
                                              returncode=exitcode,
                                              output_stream=output_copy_buffer,
                                              message='A subprocess spawned by a task exited '
                                                      'with a non-zero return code.')

            do_collect_output(seek0_before=True, seek0_after=False)
            output_copy_buffer.close()
            return exitcode

    def _call_ignore_errors(self, args, stdin, shell, silent, print_cmd, collect_output):
        use_temp_file_for_collect = collect_output and not silent

        if use_temp_file_for_collect:
            p_stdout = tempfile.TemporaryFile(mode='w+', newline='\n')
            if print_cmd:
                p_stdout.write(' '.join(args) + '\n')

        else:
            if print_cmd:
                self.print(' '.join(args))
            if silent:
                p_stdout = subprocess.DEVNULL
            else:
                p_stdout = self._io

        try:
            return subprocess.call(args,
                                   stdout=p_stdout,
                                   stderr=subprocess.STDOUT,
                                   stdin=stdin,
                                   shell=shell)
        finally:
            if use_temp_file_for_collect:

                # Rewind the temp file first
                p_stdout.seek(0)

                with self.io_lock:
                    shutil.copyfileobj(p_stdout, self._io)

                p_stdout.close()

    @property
    def dependencies(self):
        """
        Immediate dependencies of this task.
        
        returns a list of :py:class:`pake.TaskContext` representing  each
        immediate dependency of this task.
        
        **Note:**
        
        This property **will** return a meaningful value outside of a task.
        """
        return list(
            self.pake.get_task_context(i.func) for i in self._node.edges
        )

    @property
    def dependency_outputs(self):
        """
        Returns a list of output files/directories which represent the outputs of
        the tasks immediate dependencies.
        
        **Note:** 
       
        Not available outside of a task, may only be used while a task is executing.
        """

        return list(
            pake.util.flatten_non_str(
                self.pake.get_task_context(i.func).outputs for i in self.dependencies
            )
        )

    def _i_io_open(self):
        if self._pake.threadpool and self.pake.sync_output:
            self._io = tempfile.TemporaryFile(mode='w+', newline='\n')
        else:
            self._io = self.pake.stdout

    def _i_io_close(self):
        if self.pake.threadpool and self.pake.sync_output:
            self._io.seek(0)
            with self.pake._stdout_lock:
                shutil.copyfileobj(self._io, self.pake.stdout)
            self._io.close()

    def _i_submit_self(self):

        futures = [self.pake.get_task_context(i.name)._future for i in self._node.edges]

        # Wait dependencies, Raise pending exceptions
        _wait_futures_and_raise(futures)

        # Submit self
        self._future = self._pake.threadpool.submit(self._node.func)

        return self._future

    @property
    def node(self):
        """The :py:class:`pake.TaskGraph` node for the task.

        """
        return self._node

    @property
    def pake(self):
        """The :py:class:`pake.Pake` instance the task is registered to.

        """
        return self._pake


class TaskGraph(pake.graph.Graph):
    """Task graph node.
    
    .. py:attribute:: func

        Task function reference.
        
        This function will be an internal wrapper around
        the one you specified and you should not call it.
        
        There is not currently a way to get a reference
        to your actual unwrapped task function from the
        :py:class:`pake.Pake` object or elsewhere.
        
        However since the :py:meth:`functools.wraps` decorator is used
        when wrapping your task function, metadata such as **func.__doc__** 
        will be maintained on this function reference.
    """

    def __init__(self, name, func):
        """
        :raises: :py:exc:`ValueError` if **name** or **func** are **None**,
                 or if **func** is not callable.
                 
        :param name: Task name.
        :param func: Task callable.
        """

        if name is None:
            raise ValueError('Name parameter must not be None.')

        if not callable(func):
            raise ValueError('Func parameter must be callable, also not None.')

        self._name = name
        self.func = func
        super(TaskGraph, self).__init__()

    def __call__(self, *args, **kwargs):
        self.func(*args, **kwargs)

    @property
    def name(self):  # pragma: no cover
        """The task name.

        :return: The task name, as a string.
        """
        return self._name

    def __str__(self):  # pragma: no cover
        """Returns :py:attr:`pake.TaskGraph.name`."""
        return self._name


def glob(expression):
    """Deferred file input glob, the glob is not executed until the task executes.

    This input generator handles recursive directory globs by default, denoted by a double asterisk.
     
    It will return directory names as well if your glob expression matches them.
       
    The syntax used is the same as the built in :py:meth:`glob.glob` from pythons :py:mod:`glob` module.
    
    Example:
           
    .. code-block:: python
    
        @pk.task(build_c, i=pake.glob('obj/*.o'), o='main')
        def build_exe(ctx):
           ctx.call('gcc', ctx.inputs, '-o', ctx.outputs)

        @pk.task(build_c, i=[pake.glob('obj_a/*.o'), pake.glob('obj_b/*.o')], o='main')
        def build_exe(ctx):
           ctx.call('gcc', ctx.inputs, '-o', ctx.outputs)


    Recursive Directory Search Example:

    .. code-block:: python

        # Find everything under 'src' that is a .c file, including
        # in sub directories of 'src' and all the way to the bottom of
        # the directory tree.

        # pake.pattern is used to put the object file for each .c file
        # next to it in the same directory.

        @pk.task(i=pake.glob('src/**/*.c'), o=pake.pattern('{dir}/%.o'))
        def build_c(ctx):
            for i, o in ctx.outdated_pairs:
                ctx.call('gcc', '-c', i, '-o', o)


    :py:meth:`pake.glob` returns a function similar to this:
    
    .. code-block:: python
    
       def input_generator():
           return glob.iglob(expression, recursive=True)


    :return: A callable function object, which returns a
             generator over the file glob results as strings.
    """

    def input_generator():
        return glob_iglob(expression, recursive=True)

    return input_generator


def pattern(file_pattern):
    """Produce a substitution pattern that can be used in place of an output file.
    
    The **%** character represents the file name, while **{dir}** and **{ext}** represent the directory of
    the input file, and the input file extension.
    
    Example:
    
    .. code-block:: python
    
        @pk.task(i=pake.glob('src/*.c'), o=pake.pattern('obj/%.o'))
        def build_c(ctx):
            for i, o in ctx.outdated_pairs:
                ctx.call('gcc', '-c', i, '-o', o)
                
        @pk.task(i=[pake.glob('src_a/*.c'), pake.glob('src_b/*.c')], o=pake.pattern('{dir}/%.o'))
        def build_c(ctx):
            for i, o in ctx.outdated_pairs:
                ctx.call('gcc', '-c', i, '-o', o)
                
                
    :py:meth:`pake.pattern` returns function similar to this:
    
    .. code-block:: python
    
       def output_generator(inputs):
           # inputs is always a flat list, and a copy
           # inputs is safe to mutate

           for inp in inputs:
               dir = os.path.dirname(inp)
               name, ext = os.path.splitext(os.path.basename(inp))
               yield file_pattern.replace('{dir}', dir).replace('%', name).replace('{ext}', ext)
    
    """

    def output_generator(inputs):
        for inp in inputs:
            dirname = os.path.dirname(inp)
            name, ext = os.path.splitext(os.path.basename(inp))
            yield file_pattern.replace('{dir}', dirname).replace('%', name).replace('{ext}', ext)

    return output_generator


class AggregateException(Exception):
    """
    Thrown upon :py:meth:`pake.MultitaskContext.shutdown` if the context had
    its :py:attr:`pake.MultitaskContext.aggregate_exceptions` setting set to **True**
    and one or more submitted tasks encountered an exception.

    See the **aggregate_exceptions** parameter of :py:meth:`pake.TaskContext.multitask`.
    """

    def __init__(self, exceptions):
        self.exceptions = exceptions

    def write_info(self, file=None):
        """
        Write information about all the encountered exceptions to a file like object.
        If you specify the file as **None**, the default is :py:attr:`pake.conf.stderr`

        :param file: A text mode file like object to write information to.
        """

        file = pake.conf.stderr if file is None else file

        print('All Aggregated Exceptions:\n', file=file)

        for idx, err in enumerate(self.exceptions):
            human_idx = idx+1

            human_idx_len = len(str(human_idx))
            section_sep_extra = '=' * human_idx_len

            if isinstance(err, pake.process.StreamingSubprocessException):

                print('Exception Number {}:\n'
                      '=================={}\n'
                      .format(human_idx, section_sep_extra), file=file)

                err.write_info(file=file)
                file.write('\n')
            else:

                print('Exception Number {}\n'
                      '=================={}:\n'
                      .format(human_idx, section_sep_extra), file=file)

                traceback.print_exception(
                    type(err),
                    err,
                    err.__traceback__,
                    file=pake.conf.stderr if file is None else file)
                file.write('\n')


class MultitaskContext(Executor):
    """Returned by :py:meth:`pake.TaskContext.multitask` (see for more details).

    This object has (for the most part) has the exact same behavior and interface as
    :py:class:`concurrent.futures.ThreadPoolExecutor` from the built in Python module
    :py:class:`concurrent.futures`.

    If you need further reference on how its member functions behave, you can also consult
    the official Python doc for that class.

    This object is meant to be used in a **with** statement.  At the end of the **with**
    statement all of your submitted work will be waited on, so you do not have to do it
    manually with :py:meth:`pake.MultitaskContext.shutdown`.

    Using a **with** statement is also exception safe.

    .. py:attribute:: aggregate_exceptions

        Whether or not the multitasking context should collect all exceptions
        that occurred inside of submitted tasks upon shutdown, and then raise
        a :py:class:`pake.AggregateException` containing them.

        This is **False** by default, the normal behaviour is to search
        the tasks in the order of submission for exceptions upon shutdown, and
        then re-raise the first exception that was encountered on the foreground thread.
    """

    def __init__(self, ctx, aggregate_exceptions=False):
        """
        :param ctx: Instance of :py:class:`pake.TaskContext`.
        """
        self._ctx = ctx
        self._threadpool = ctx.pake.threadpool
        self._pending = []
        self.aggregate_exceptions = aggregate_exceptions

    @staticmethod
    def _submit_this_thread(fn, *args, **kwargs):
        future = Future()
        if not future.set_running_or_notify_cancel():
            return future
        try:
            result = fn(*args, **kwargs)
        except BaseException as err:
            future.set_exception(err)
        else:
            future.set_result(result)
        return future

    def map(self, fn, *iterables, timeout=None, chunksize=1):
        """
        Returns an iterator equivalent to ``map(fn, iter)``.

        :param fn: A callable that will take as many arguments as there are passed iterables.
        :param timeout: The maximum number of seconds to wait. If **None**, then there is no limit on the wait time.
        :param chunksize: The size of the chunks the iterable will be broken into.

        :return: An iterator equivalent to: ``map(func, *iterables)`` but the calls may be evaluated out-of-order.
        :raises: :py:exc:`TimeoutError` If the entire result iterator could not be generated before the given timeout.
        :raises: :py:exc:`Exception` If ``fn(*args)`` raises for any values.
        """

        return super().map(fn, *iterables, timeout=timeout, chunksize=chunksize)

    def submit(self, fn, *args, **kwargs):
        """Submit a task to pakes current threadpool.
           
        If no thread pool exists, such as in the case of **--jobs 1**, then the submitted
        function is immediately executed in the current thread.

        This function has an identical call syntax to **concurrent.futures.Executor.submit**.

        Example:

        .. code-block:: python

           mt.submit(work_function, arg1, arg2, keyword_arg='arg')
        
        :returns: :py:class:`concurrent.futures.Future`

        """
        if not self._threadpool:
            future = self._submit_this_thread(fn, *args, **kwargs)
            self._pending.append(future)
        else:
            future = self._threadpool.submit(fn, *args, **kwargs)
            self._pending.append(future)

        return future

    def __enter__(self):
        return self

    def shutdown(self, wait=True):
        """Shutdown multitasking and free resources, optionally wait on all submitted tasks.
    
           It is not necessary to call this function if you are using the context in a **with** statement.

           If you specify **wait=False**, this method will not propagate any exceptions out of your submitted tasks.

           :param wait: Whether or not to wait on all submitted tasks, default is true.
        """

        if not self.aggregate_exceptions:
            if wait and len(self._pending):
                _wait_futures_and_raise(self._pending)
        elif wait:
            futures_wait(self._pending)
            exceptions = [
                e for e in (future.exception() for future in self._pending) if e is not None
            ]
            if len(exceptions):
                raise AggregateException(exceptions)

    def __exit__(self, exc_type, exc_value, tb):
        self.shutdown()


class Pake:
    """
    Pake's main instance, which should not be initialized directly.
    
    Use: :py:meth:`pake.init` to create a :py:class:`pake.Pake` object
    and initialize the pake module.
    
    .. py:attribute:: stdout
    
        The file object that task output gets written to, as well as 'changing directory/entering & leaving subpake' messages.
        If you set this, make sure that you set it to an actual file object that implements **fileno()**. :py:class:`io.StringIO`
        and pseudo file objects with no **fileno()** will not work with all of pake's subprocess spawning functions.

        This attribute can be modified directly.

    .. py:attribute:: sync_output

        Whether or not the pake instance should queue task output and write it in
        a synchronized fashion when running with more than one job.  This defaults
        to **True** unless the environmental variable ``PAKE_SYNC_OUTPUT`` is set to **0**,
        or the command line option **--output-sync False** is specified.

        If this is disabled (Set to **False**), task output may become interleaved
        and scrambled when running pake with more than one job.  Pake will run
        somewhat faster however.

        This attribute can be modified directly.

    .. py:attribute:: show_task_headers

        Whether or not pake should print **Executing Task:** headers for tasks that are
        about to execute, the default value is **True**. If you set this to **False** task
        headers will be disabled for all tasks except ones that explicitly specify **show_header=True**.
        See the **show_header** parameter of :py:meth:`pake.Pake.task` and :py:meth:`pake.Pake.add_task`,
        which allows you to disable or force enable the task header for a specific task.

        This attribute can be modified directly.
    """

    def __init__(self, stdout=None, sync_output=True, show_task_headers=True):
        """
        Create a pake object, optionally set :py:attr:`pake.Pake.stdout` for the instance.

        Use :py:meth:`pake.init` to retrieve an instance of this object, do not instantiate directly.
        
        :param stdout: The stream all task output gets written to, (defaults to :py:attr:`pake.conf.stdout`)
        :param show_task_headers: Whether or not to show **Executing Task:** headers by default.
        :param sync_output: Whether or not to synchronize task output, setting this value to **None**
                            causes the default value of **True** to be used.
        """

        self.sync_output = sync_output

        self.show_task_headers = show_task_headers

        self.stdout = stdout if stdout is not None else pake.conf.stdout

        self._stdout_lock = threading.RLock()

        self._graph = TaskGraph("_", lambda: None)

        # maps task name to TaskContext
        self._task_contexts = dict()

        # maps task functions to their task name
        self._task_func_names = dict()

        self._defines = dict()
        self._dry_run_mode = False
        self._threadpool = None
        self._is_running = False
        self._run_count_lock = threading.Lock()
        self._run_count = 0
        self._cur_max_jobs = 1

    @property
    def max_jobs(self):
        """Returns the value of the **jobs** parameter used in the last invocation of :py:meth:`pake.Pake.run`.

        This can be used inside of a task to determine if pake is running in multithreaded mode, and the
        maximum amount of threads it has been allowed to use for the current invocation.

        A **max_jobs** value of **1** indicates that pake is running all tasks in the current thread,
        anything greater than **1** means pake is sending tasks to a threadpool.

        See Also:  :py:attr:`pake.Pake.threadpool`
        """
        return self._cur_max_jobs

    @property
    def task_count(self):
        """Returns the number of registered tasks.
        
        :returns: Number of tasks registered to the :py:class:`pake.Pake` instance.
        """

        return len(self._task_contexts)

    @property
    def run_count(self):
        """Contains the number of tasks ran/visited by the last invocation of :py:meth:`pake.Pake.run` or :py:meth:`pake.Pake.dry_run`
        
        If a task did not run because change detection decided it did not need to, then it does  not count towards this total.
        This also applies when doing a dry run with :py:meth:`pake.Pake.dry_run`
        
        :returns: Number of tasks last run.
        """

        return self._run_count

    @property
    def threadpool(self):
        """Current execution thread pool.

        This will never be anything other than **None** unless pake is running, and its max job count is greater than 1.

        Pake is considered to be running when :py:attr:`pake.Pake.is_running` equals **True**.
        
        If pake is running with a job count of 1, no threadpool is used so this property will be **None**.


        """
        return self._threadpool

    def set_define(self, name, value):
        """
        Set a defined value.
        
        :param name: The name of the define.
        :param value: The value of the define.
        """
        self._defines[name] = value

    def __getitem__(self, item):
        """
        Access a define using the indexing operator []
        
        :param item: Name of the define.
        :return: The defines value, or *None*
        """
        return self.get_define(item)

    def has_define(self, name):
        """Test if a define with a given name was provided to pake.

        This is useful if **None** might be a valid value for your define,
        and you just want to know if it was actually specified on the command
        line or with **--stdin-defines**.

        :param name: The name of the define.
        :return: **True** if a define with the given name exists.
        """
        return name in self._defines

    def get_define(self, name, default=None):
        """Get a defined value.
           
        This is used to get defines off the command line, as well as retrieve
        values exported from top level pake scripts.
        
        If the define is not found, then **None** is returned by default.
        
        The indexer operator can also be used on the pake instance to fetch defines, IE:
        
        .. code-block:: python
        
            import pake
            
            pk = pake.init()
            
            value = pk['YOURDEFINE']
        
        Which also produces **None** if the define does not exist.

        See: :ref:`Specifying define values` for documentation covering how
        to specify defines on the command line, as well as what types
        of values you can use for your defines.
        
        :param name: Name of the define
        :param default: The default value to return if the define does not exist
        :return: The defines value as a python literal corresponding to the defines type.
        """
        return self._defines.get(name, default)

    @property
    def task_contexts(self):
        """
        Retrieve the task context objects for all registered tasks.
        
        :return: List of :py:class:`pake.TaskContext`.


        """
        return self._task_contexts.values()

    def terminate(self, return_code=pake.returncodes.SUCCESS):
        """Shorthand for ``pake.terminate(this, return_code=return_code)``.

        See for more details: :py:meth:`pake.terminate`

        :param return_code: Return code to exit the pakefile with.
                            The default return code is :py:attr:`pake.returncodes.SUCCESS`.
        """
        pake.terminate(self, return_code=return_code)

    @staticmethod
    def _process_i_o_params(i, o):
        # Process i / o parameters of add_task, and task decorator.

        # Collapse input and output generators like pake.glob etc..

        # return i / o as a list always according to the allowed syntax
        # of the task decorators input and output parameters, which can
        # accept single strings, list of strings, input or output generators,
        # or list of input or output generators

        if i is None:
            i = []
        elif callable(i):
            i = i()
        elif type(i) is str or not pake.util.is_iterable_not_str(i):
            i = [i]
        else:
            i = map(lambda inp: inp() if callable(inp) else inp, i)

        i = list(pake.util.flatten_non_str(i))

        if o is None:
            o = []
        if callable(o):
            o = o(list(i))
        elif type(o) is str or not pake.util.is_iterable_not_str(o):
            o = [o]

        o = list(pake.util.flatten_non_str(o))

        return i, o

    def _increment_run_count(self):
        if self._cur_max_jobs > 1:
            with self._run_count_lock:
                self._run_count += 1
        else:
            self._run_count += 1

    @staticmethod
    def _change_detect(task_name, i, o):
        len_i = len(i)
        len_o = len(o)

        if len_i > 0 and len_o == 0:
            raise MissingOutputsException(task_name)

        outdated_inputs = []
        outdated_outputs = []

        if len_i == 0 and len_o == 0:
            return [], []

        if len_o > 1:
            Pake._change_detect_multiple_outputs(task_name, i, o,
                                                 outdated_inputs,
                                                 outdated_outputs)

        else:
            Pake._change_detect_single_output(task_name, i, o,
                                              outdated_inputs,
                                              outdated_outputs)

        return outdated_inputs, outdated_outputs

    @staticmethod
    def _change_detect_single_output(task_name, i, o, outdated_inputs, outdated_outputs):
        output_object = o[0]

        if not path.exists(output_object):
            for input_object in i:
                if not path.exists(input_object):
                    raise InputNotFoundException(task_name, input_object)

            outdated_outputs.append(output_object)
            outdated_inputs += i
        else:
            outdated_output = None
            for input_object in i:
                if not path.exists(input_object):
                    raise InputNotFoundException(task_name, input_object)
                if pake.util.is_more_recent(input_object, output_object):
                    outdated_inputs.append(input_object)
                    outdated_output = output_object

            if outdated_output:
                outdated_outputs.append(outdated_output)

    @staticmethod
    def _change_detect_multiple_outputs(task_name, i, o, outdated_inputs, outdated_outputs):
        len_i = len(i)
        len_o = len(o)

        if len_i == 0:
            for output_object in o:
                if not path.exists(output_object):
                    outdated_outputs.append(output_object)

        elif len_o != len_i:
            output_set = set()
            input_set = set()

            for input_object in i:
                if not path.exists(input_object):
                    raise InputNotFoundException(task_name, input_object)
                for output_object in o:
                    if not path.exists(output_object) or pake.util.is_more_recent(input_object, output_object):
                        input_set.add(input_object)
                        output_set.add(output_object)

            outdated_inputs += input_set
            outdated_outputs += output_set

        else:
            for input_object, output_object in zip(i, o):
                if not path.exists(input_object):
                    raise InputNotFoundException(task_name, input_object)
                if not path.exists(output_object) or pake.util.is_more_recent(input_object, output_object):
                    outdated_inputs.append(input_object)
                    outdated_outputs.append(output_object)

    def task(self, *args, i=None, o=None, show_header=None):
        """
        Decorator for registering pake tasks.
        
        Any input files specified must be accompanied by at least one output file.

        A callable object, or list of callable objects may be passed to **i** or **o** in addition to
        a raw file/directory name or names.  This is how **pake.glob** and **pake.pattern** work.
        
        Input/Output Generation Example:
        
        .. code-block:: python
        
           def gen_inputs(pattern):
               def input_generator():
                   return glob.glob(pattern)
               return input_generator
               
           def gen_output(pattern):
               def output_generator(inputs):
                   # inputs is always a flat list, and a copy
                   # inputs is safe to mutate if you want

                   for inp in inputs:
                       dir = os.path.dirname(inp)
                       name, ext = os.path.splitext(os.path.basename(inp))
                       yield pattern.replace('{dir}', dir).replace('%', name).replace('{ext}', ext)

               return output_generator
           
           @pk.task(i=gen_inputs('*.c'), o=gen_outputs('%.o'))
           def my_task(ctx):
               # Do your build task here
               pass
               
           
           @pk.task(i=[gen_inputs('src_a/*.c'), gen_inputs('src_b/*.c')], o=gen_outputs('{dir}/%.o'))
           def my_task(ctx):
               # Do your build task here
               pass
        
        Dependencies Only Example:
        
        .. code-block:: python
           
           @pk.task(dependency_task_a, dependency_task_b)
           def my_task(ctx):
               # Do your build task here
               pass
               
        Change Detection Examples:
        
        .. code-block:: python
        
           # Dependencies come before input and output files.
           
           @pk.task(dependency_task_a, dependency_task_b, i='main.c', o='main')
           def my_task(ctx):
               # Do your build task here
               pass
               
           
           # Tasks without input or output files will always run when specified.
           
           @pk.task
           def my_task(ctx):
               # I will always run when specified!
               pass
               
               
           # Tasks with dependencies but no input or output files will also
           # always run when specified.
           
           @pk.task(dependency_task_a, dependency_task_b)
           def my_task(ctx):
               # I will always run when specified!
               pass
            
            
           # Having an output with no input is allowed, this task
           # will always run.  The opposite (having an input file with no output file)
           # will cause an error.  ctx.outdated_outputs is populated with 'main' in this case.
           
           @pk.task(o='main')
           def my_task(ctx):
               # Do your build task here
               pass
        
        
           # Single input and single output, 'main.c' has its creation time checked
           # against 'main'
           
           @pk.task(i='main.c', o='main')
           def my_task(ctx):
               # Do your build task here
               pass
               
               
           # When multiple input files exist and there is only one output file, each input file
           # has its creation time checked against the output files creation time.
           
           @pk.task(i=['otherstuff.c', 'main.c'], o='main')
           def my_task(ctx):
               # Do your build task here
               pass
               
               
           # all files in 'src/*.c' have their creation date checked against 'main' 
           
           @pk.task(i=pake.glob('src/*.c'), o='main')
           def my_task(ctx):
               # Do your build task here
               pass
               
               
           # each input file has its creation date checked against its corresponding
           # output file in this case.  Out of date file names can be found in 
           # ctx.outdated_inputs and ctx.outdated_outputs.  ctx.outdated_pairs is a
           # convenience property which returns: zip(ctx.outdated_inputs, ctx.outdated_outputs)
           
           @pk.task(i=['file_b.c', 'file_b.c'], o=['file_b.o', 'file_b.o'])
           def my_task(ctx):
               # Do your build task here
               pass
               
               
           # Similar to the above, inputs and outputs end up being of the same
           # length when using pake.glob with pake.pattern
           
           @pk.task(i=pake.glob('src/*.c'), o=pake.pattern('obj/%.o'))
           def my_task(ctx):
               # Do your build task here
               pass
               
    
           # All input files have their creation date checked against all output files
           # if there are more inputs than outputs, in general.
           
           @pk.task(i=['a.c', 'b.c', 'c.c'], o=['main', 'what_are_you_planning'])
           def my_task(ctx):
               # Do your build task here
               pass
               
               
           # Leaving the inputs and outputs as empty list will cause the task
           # to never run.
           
           @pk.task(i=[], o=[])
           def my_task(ctx):
               # I will never run!
               pass
           
           
           # If an input generator produces no results 
           # (IE, something like pake.glob returns no files) and the tasks 
           # outputs also end up being empty such as in this case, 
           # then the task will never run.
        
           @pk.task(i=pake.glob('*.some_extension_that_no_file_has'), o=pake.pattern('%.o'))
           def my_task(ctx):
               # I will never run!
               pass
        
        :raises: :py:exc:`pake.UndefinedTaskException` if a given dependency is not a registered task function.
        
        :param args: Tasks which this task depends on, this may be passed as variadic arguments or a single iterable object.
        :param i: Optional input files/directories for change detection.
        :param o: Optional output files/directories for change detection.
        
        :param show_header: Whether or not to print an **Executing Task:** header when the task begins executing.
                            This defaults to **None**, which means the header is printed unless :py:attr:`pake.Pake.show_task_header`
                            is set to **False**.  If you specify **True** and :py:attr:`pake.Pake.show_task_header` is set to
                            **False**, it will force the task header to print anyway.  By explicitly specifying **True** you
                            override the :py:attr:`pake.Pake.show_task_header` setting.

        """

        if len(args) == 1 and inspect.isfunction(args[0]):
            if args[0].__name__ not in self._task_contexts:
                func = args[0]
                self.add_task(func.__name__, func, show_header=show_header)
                return func

        if len(args) == 1 and pake.util.is_iterable_not_str(args[0]):
            dependencies = list(args[0])
        else:
            dependencies = args

        def outer(task_func):
            self.add_task(task_func.__name__, task_func, dependencies, i, o, show_header=show_header)
            return task_func

        return outer

    def get_task_name(self, task):
        """
        Returns the name of a task by the task function or callable reference used to define it.
        
        The name of the task may be different than the name of the task function/callable when
        :py:meth:`pake.Pake.add_task` is used to register the task.
        
        If a string is passed it is returned unmodified as long as the task exists, otherwise
        a :py:exc:`pake.UndefinedTaskException` is raised.
        
        Example:
        
        .. code-block:: python
           
           @pk.task
           def my_task(ctx):
               pass
               
           def different_name(ctx):
               pass
               
           pk.add_task("my_task2", different_name)
               
           pk.get_task_name(my_task) # -> "my_task"
           
           pk.get_task_name(different_name) # -> "my_task2"
        
        :param task: Task name string, or registered task callable.
        
        :raises: :py:exc:`ValueError` if the **task** parameter is not a string or a callable function/object.
        :raises: :py:exc:`pake.UndefinedTaskException` if the task function/callable is not registered to the pake context.

        :return: Task name string.


        """
        if type(task) is str:
            ctx = self._task_contexts.get(task, None)
            if ctx is None:
                raise UndefinedTaskException(task)
            return task

        elif callable(task):
            name = self._task_func_names.get(task, None)
            if name is None:
                raise UndefinedTaskException(task.__name__)
            return name
        raise ValueError('Task was neither a string task name reference or callable.')

    def get_task_context(self, task):
        """
        Get the :py:class:`pake.TaskContext` object for a specific task.
        
        :raises: :py:exc:`ValueError` if the **task** parameter is not a string or a callable function/object.
        :raises: :py:exc:`pake.UndefinedTaskException` if the task in not registered.
        
        :param task: Task function or function name as a string
        :return: :py:class:`pake.TaskContext`
        """

        # self.get_task_name will raise if the task is undefined

        return self._task_contexts.get(self.get_task_name(task))

    @staticmethod
    def _should_run_task(ctx, inputs, outputs):
        if inputs is None and outputs is None:
            return True

        i, o = Pake._process_i_o_params(inputs, outputs)
        outdated_inputs, outdated_outputs = Pake._change_detect(ctx.name, i, o)

        ctx.inputs = list(i)
        ctx.outputs = list(o)
        ctx.outdated_inputs = list(outdated_inputs)
        ctx.outdated_outputs = list(outdated_outputs)

        if (len(i) > 0 or len(o) > 0) and (len(outdated_inputs) > 0 or len(outdated_outputs) > 0):
            return True

        return False

    def add_task(self, name, func, dependencies=None, inputs=None, outputs=None, show_header=None):
        """
        Method for programmatically registering pake tasks.
        
        
        This method expects for the most part the same argument types as the :py:meth:`pake.Pake.task` decorator.
        
        
        Example:
        
        .. code-block:: python
           
           # A contrived example using a callable class
           
           class FileToucher:
               \"\"\"Task Documentation Here\"\"\"
               
               def __init__(self, tag):
                   self._tag = tag
               
               def __call__(self, ctx):
                   ctx.print('Toucher {}'.format(self._tag))
                   
                   fp = pake.FileHelper(ctx)
                   
                   for i in ctx.outputs:
                       fp.touch(i)
                   
                   
          task_instance_a = FileToucher('A')
          task_instance_b = FileToucher('B')
          
          pk.add_task('task_a', task_instance_a, outputs=['file_1', 'file_2'])
          
          pk.add_task('task_b', task_instance_b, dependencies=task_instance_a, outputs='file_3')
          
          # Note: you can refer to dependencies by name (by string) as well as reference.
          
          # Equivalent calls:
          
          # pk.add_task('task_b', task_instance_b, dependencies='task_a', outputs='file_3')
          # pk.add_task('task_b', task_instance_b, dependencies=['task_a'], outputs='file_3')
          # pk.add_task('task_b', task_instance_b, dependencies=[task_instance_a], outputs='file_3')
          
          
          # Example using a function
          
          def my_task_func_c(ctx):
              ctx.print('my_task_func_c')
              
          pk.add_task('task_c', my_task_func_c, dependencies='task_b')
          
          pake.run(pk, tasks=my_task_func_c)
          
          # Or equivalently:
          
          # pake.run(pk, tasks='task_c')
        
        :param name: The name of the task
        :param func: The task function (or callable class)
        :param dependencies: List of task dependencies or single task, by name or by reference
        :param inputs: List of input files/directories, or a single input (accepts input file generators like :py:meth:`pake.glob`)
        :param outputs: List of output files/directories, or a single output (accepts output file generators like :py:meth:`pake.pattern`)

        :param show_header: Whether or not to print an **Executing Task:** header when the task begins executing.
                            This defaults to **None**, which means the header is printed unless :py:attr:`pake.Pake.show_task_header` is set to **False**.
                            If you specify **True** and :py:attr:`pake.Pake.show_task_header` is set to **False**, it will force the task header to print
                            anyway.  By explicitly specifying **True** you override :py:attr:`pake.Pake.show_task_header`.

        :return: The :py:class:`pake.TaskContext` for the new task.


        """

        if name in self._task_contexts:
            raise RedefinedTaskException(name)

        @wraps(func)
        def func_wrapper(*args, **kwargs):
            ctx = self.get_task_context(func)

            try:
                ctx._i_io_open()

                if not Pake._should_run_task(ctx, inputs, outputs):
                    return None

                self._increment_run_count()

                if self._dry_run_mode:
                    ctx.print('Visited Task: "{}"'.format(ctx.name))
                else:

                    # If the show_header parameter is True, force the task
                    # to print a header regardless of what pake.show_task_headers
                    # says to do

                    # If the show_header parameter is left unspecified (None), check
                    # pake.show_task_headers to see if it should be printed

                    if show_header is True or (show_header is None and ctx.pake.show_task_headers):
                        ctx.print('===== Executing Task: "{}"'.format(ctx.name))

                    return func(*args, **kwargs)

            except BaseException as err:
                _handle_task_exception(ctx, err)
            finally:
                ctx._i_io_close()

        if len(inspect.signature(func).parameters) == 1:
            @wraps(func_wrapper)
            def _add_ctx_param_stub():
                func_wrapper(task_context)

            # functools.partial will not work for this, __doc__ needs to be maintained on the wrapper.
            # @wraps does this

            task_context = TaskContext(self, TaskGraph(name, _add_ctx_param_stub))
        else:
            task_context = TaskContext(self, TaskGraph(name, func_wrapper))

        self._task_contexts[name] = task_context

        # alias for the unwrapped function
        self._task_func_names[func] = name

        if func is not task_context.func:
            # alias for the wrapped function (for internal usage)
            self._task_func_names[task_context.func] = name

        if dependencies:
            if pake.util.is_iterable_not_str(dependencies):
                for dependency in dependencies:
                    dep_task = self.get_task_context(dependency)
                    task_context.node.add_edge(dep_task.node)
                    try:
                        self._graph.remove_edge(dep_task.node)
                    except KeyError:
                        pass
            else:
                dep_task = self.get_task_context(dependencies)
                task_context.node.add_edge(dep_task.node)
                try:
                    self._graph.remove_edge(dep_task.node)
                except KeyError:
                    pass

        self._graph.add_edge(task_context.node)

        return task_context

    def run(self, tasks, jobs=1):
        """
        Run all given tasks, with an optional level of concurrency.

        :raises: :py:exc:`ValueError` if **jobs** is less than 1,
                 or if **tasks** is **None** or an empty list.
        
        :raises: :py:exc:`pake.TaskException` if an exception occurred while running a task.
        
        :raises: :py:exc:`pake.TaskExitException` if :py:exc:`SystemExit` or an exception derived from it
                          such as :py:exc:`pake.TerminateException` is raised inside of a task.
        
        :raises: :py:exc:`pake.MissingOutputsException` if a task defines input files/directories without specifying any output files/directories.
        :raises: :py:exc:`pake.InputNotFoundException` if a task defines input files/directories but one of them was not found on disk.
        :raises: :py:exc:`pake.UndefinedTaskException` if one of the default tasks given in the *tasks* parameter is unregistered.
        
        :param tasks: Single task, or Iterable of task functions to run (by ref or name).
        :param jobs: Maximum number of threads, defaults to 1. (must be >= 1)
        """

        if not tasks:
            raise ValueError('Tasks parameter may not be None or an empty list.')

        if jobs < 1:
            raise ValueError('Job count must be >= to 1.')

        if not pake.util.is_iterable_not_str(tasks):
            tasks = [tasks]

        self._cur_max_jobs = jobs
        self._run_count = 0

        task_graphs = (self.get_task_context(task).node.topological_sort() for task in tasks)

        if jobs == 1:
            self._run_sync(task_graphs)
            return

        self._run_parallel(jobs, task_graphs)

    def _run_parallel(self, jobs, task_graphs):

        # Task futures pending wait
        pending_futures = []

        try:
            self._threadpool = ThreadPoolExecutor(max_workers=jobs)

            # is_running, and _threadool will be left 'None'
            # if constructing the threadpool throws

            self._is_running = True

            for graph in task_graphs:
                for i in (i for i in graph if i is not self._graph):
                    context = self.get_task_context(i.name)
                    pending_futures.append(context._i_submit_self())
        finally:
            all_futures_waited = False
            try:
                # This will raise if a task throws an exception.
                _wait_futures_and_raise(pending_futures)

                # No exception was raised if execution got to here
                all_futures_waited = True
            finally:
                # Be very paranoid about object state

                t_pool = self._threadpool  # t_pool.shutdown might throw, maybe

                # Fix object state
                self._threadpool = None
                self._is_running = False

                if t_pool:
                    # Only wait here if _wait_futures_and_raise did not finish.
                    # this function will not complain if you have already waited
                    # some of your threadpool tasks
                    t_pool.shutdown(wait=not all_futures_waited)

    def _run_sync(self, graphs):
        try:
            self._is_running = True
            for graph in graphs:
                for i in graph:
                    i()
        finally:
            self._is_running = False

    @property
    def is_running(self):
        """Check if pake is currently running tasks.

        This can be used to determine if code is executing inside of a task.

        Example:

        .. code-block:: python

            import pake

            pk = pake.init()

            pk.print(pk.is_running) # -> False

            @pk.task
            def my_task(ctx):
                ctx.print(pk.is_running) # -> True


            pake.run(pk, tasks=my_task, call_exit=False)

            pk.print(pk.is_running) # -> False


        :return:  **True** if pake is currently running tasks, **False** otherwise.


        """
        return self._is_running

    def dry_run(self, tasks):
        """
        Dry run over task, print a 'visited' message for each visited task.
        
        When using change detection, only out of date tasks will be visited.
        
        :raises: :py:exc:`ValueError` If **tasks** is **None** or an empty list.

        :raises: :py:exc:`pake.MissingOutputsException` if a task defines input files/directories without specifying any output files/directories.
        :raises: :py:exc:`pake.InputNotFoundException` if a task defines input files/directories but one of them was not found on disk.
        :raises: :py:exc:`pake.UndefinedTaskException` if one of the default tasks given in the **tasks** parameter is unregistered.
        
        :param tasks: Single task, or Iterable of task functions to run (by ref or name).
        """
        self._dry_run_mode = True
        try:
            self.run(tasks=tasks, jobs=1)
        finally:
            self._dry_run_mode = False

    def set_defines_dict(self, dictionary):  # pragma: no cover
        """
        Set and overwrite all defines with a dictionary object.
        
        :param dictionary: The dictionary object
        """
        self._defines = dict(dictionary)

    def merge_defines_dict(self, dictionary):  # pragma: no cover
        """
        Merge the current defines with another dictionary, overwriting anything
        that is already defined with the value from the new dictionary.

        :param dictionary: The dictionary to merge into the current defines.
        """
        self._defines.update(dictionary)

    def print(self, *args, **kwargs):  # pragma: no cover
        """Print to the file object assigned to :py:attr:`pake.Pake.stdout`

        Shorthand for: ``print(..., file=pk.stdout)``
        """

        kwargs.pop('file', None)

        if self.sync_output:
            with self._stdout_lock:
                print(*args, file=self.stdout, **kwargs)
        else:
            print(*args, file=self.stdout, **kwargs)


class TaskSubprocessException(StreamingSubprocessException):
    """
    Raised by default upon encountering a non-zero return code from a subprocess spawned
    by the :py:class:`pake.TaskContext` object.

    This exception can be raised from :py:meth:`pake.TaskContext.call`,
    :py:meth:`pake.TaskContext.check_call`, and :py:meth:`pake.TaskContext.check_output`.

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

        :param output_stream: (Optional) A file like object containing the process output, at **seek(0)**.
                               By providing this parameter instead of **output**, you give this object permission
                               to close the stream when it is garbage collected or when :py:meth:`pake.TaskSubprocessException.write_info` is called.

        :param message: Optional exception message.
        """
        super().__init__(cmd=cmd,
                         returncode=returncode,
                         output=output,
                         output_stream=output_stream,
                         message=message)
