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
import inspect
import shutil
import subprocess
import tempfile
import threading
import traceback
from functools import wraps
from glob import glob as file_glob

import os

import sys

import pake
from concurrent.futures import ThreadPoolExecutor, wait as futures_wait, Executor, Future
from os import path

import pake.conf
import pake.graph
import pake.process
import pake.util
import pake.returncodes

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
           'MissingOutputsException']


class TaskException(Exception):  # pragma: no cover
    """
    Raised by :py:meth:`pake.Pake.run` and :py:meth:`pake.Pake.dry_run` if an exception is 
    encountered running/visiting a task.
    
    .. py:attribute:: exception
    
        The exception raised.
    """

    def __init__(self, exception):
        """
        :param exception: The exception raised.
        """
        super().__init__()
        self.exception = exception

    def __str__(self):
        return str(self.exception)


class TaskExitException(Exception):
    """Raised from :py:meth:`pake.Pake.run` when **exit()** is called inside of a task.
    
    .. py:attribute:: task_name
       
       The name of the task in which **exit** was called.
       
       
    .. py:attribute:: exit_exception
       
       Reference to the :py:exc:`SystemExit` exception which caused this exception to be raised.

    """
    def __init__(self, task_name, exit_exception):
        """
        
        :param task_name: The name of the task that raised the :py:exc:`SystemExit` exception.
        :param exit_exception: Reference to the :py:exc:`SystemExit` exception raised inside the task.
        """
        super().__init__('exit({code}) was called within task "{task}".'
                         .format(code=exit_exception.code, task=task_name))

        self.task_name = task_name
        self.exit_exception = exit_exception

    @property
    def return_code(self):
        """The return code passed to **exit()** inside the task."""
        return self.exit_exception.code

    def print_traceback(self, file=None):
        """
        Print the traceback of the :py:exc:`SystemExit` exception that was raised inside the task to a file object.
        
        :param file: The file object to print to.  Default value is :py:attr:`pake.conf.stderr` if **None** is specified.
        """

        traceback.print_exception(
            type(self.exit_exception),
            self.exit_exception,
            self.exit_exception.__traceback__,
            file=pake.conf.stderr if file is None else file)


class MissingOutputsException(Exception):  # pragma: no cover
    """
    Raised by :py:meth:`pake.Pake.run` and :py:meth:`pake.Pake.dry_run` if a task declares input files without
    specifying any output files/directories.
    """

    def __init__(self, task_name):
        super().__init__(
            'Error: Task "{}" defines inputs with no outputs, this is not allowed.'.format(task_name)
        )


class InputNotFoundException(Exception):  # pragma: no cover
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
        # Handle exit() within tasks
        raise TaskExitException(ctx.name, exception)

    if isinstance(exception, pake.process.SubprocessException):
        # SubprocessException provides detailed information
        # about the call site of the subprocess in the pakefile
        # on its own, print and wrap as it is better for this information
        # to be printed to the task's output.
        exception.write_info(ctx.io)
        raise TaskException(exception)

    if isinstance(exception, pake.process.ProcessException):
        # ProcessException's provide detailed information
        # about the call site of the subprocess in the pakefile
        # on its own, print and wrap as it is better for this information
        # to be printed to the task's output.
        ctx.print(str(exception))
        raise TaskException(exception)

    if isinstance(exception, InputNotFoundException) or isinstance(exception, MissingOutputsException):
        # These are raised inside the task when
        # the task runs and does file detection, they provides information
        # which includes the task name the exception occurred in as well
        # as the name of the file that was missing.  These are handled by pake.run(...) (the library method)
        # which displays the error to the user, these exceptions will come directly out of
        # Pake.run(...) (the object method) as they are.
        raise exception

    # For everything else, print a standard trace
    # to the tasks IO before raising TaskException

    traceback.print_exception(
        type(exception),
        exception,
        exception.__traceback__,
        file=ctx.io)

    raise TaskException(exception)


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
        
        Note: Not available until the task runs.
        
    .. py:attribute:: outputs
    
        All file outputs, or an empty list.
        
        Note: Not available until the task runs.
       
    .. py:attribute:: outdated_inputs
    
        All changed file inputs (or inputs who's corresponding output is missing), or an empty list.
        
        Note: Not available until the task runs.
        
    .. py:attribute:: oudated_outputs
    
        All out of date file outputs, or an empty list
        
        Note: Not available until the task runs.
    """

    def __init__(self, pake_instance, node):
        self._pake = pake_instance
        self._node = node
        self._future = None
        self._io = None
        self.inputs = []
        self.outputs = []
        self.outdated_inputs = []
        self.outdated_outputs = []

    def multitask(self):
        """Returns a contextual object for submitting work to pake's current thread pool.

           .. code-block:: python

              @pk.task(i=pake.glob('src/*.c'), o=pake.pattern('obj/%.o'))
              def build_c(ctx):
                  with ctx.multitask() as mt:
                      for i, o in ctx.outdated_pairs:
                          mt.submit(ctx.call, ['gcc', '-c', i, '-o', o])


        At the end of the **with** statement, all submitted tasks are simultaneously waited on.

        :returns: :py:class:`pake.MultitaskContext`
        """

        return MultitaskContext(self)

    @property
    def outdated_pairs(self):
        """Short hand for: zip(ctx.outdated_inputs, ctx.outdated_outputs)
           
           Returns a generator object over outdated (input, output) pairs.
           
           This is only useful when the task has the same number of inputs as it does outputs.

           Example:

           .. code-block:: python
              
              @pk.task(i=pake.glob('src/*.c'), o=pake.pattern('obj/%.o'))
              def build_c(ctx):
                  for i, o in ctx.outdated_pairs:
                      ctx.call(['gcc', '-c', i, '-o', o])
                      
                 
           Note: Not available until the task runs.

        """
        return zip(self.outdated_inputs, self.outdated_outputs)

    @property
    def func(self):
        """Task function reference."""
        return self.node.func

    @property
    def name(self):
        """Task name."""
        return self._node.name

    @property
    def io(self):
        """Task IO file stream, a file like object that is only open for writing during a tasks execution.
        
        Any output to be displayed for the task should be written to this file object.
        """
        return self._io

    def print(self, *args, **kwargs):
        """Prints to the task IO file stream using the builtin print function."""
        kwargs.pop('file', None)
        print(*args, file=self._io, **kwargs)

    def subpake(self, *args, silent=False):
        """Run :py:func:`pake.subpake` and direct all output to the task IO file stream."""

        pake.subpake(*args, stdout=self._io, silent=silent, exit_on_error=False)

    @staticmethod
    def check_call(*args, stdin=None, shell=False, ignore_errors=False):
        """
        Return the return code of an executed system command.
        
        :raises: :py:class:`pake.SubprocessException` if **ignore_errors** is False
                 and the process exits with a non zero return code.
                 
        :raises: :py:class:`OSError` (commonly) if a the executed command or file does not exist.
                 This exception will still be raised even if **ignore_errors** is **True**.
                 
        :raises: :py:class:`ValueError` if no command + optional arguments are provided.
        
        :param args: Command arguments, same syntax as :py:meth:`pake.TaskContext.call`
        :param stdin: Optional stdin to pipe into the called process.
        :param shell: Whether to execute in shell mode or not.
        :param ignore_errors: Whether to ignore non zero return codes and return the return code anyway.
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
            raise pake.process.SubprocessException(cmd=args,
                                                   returncode=err.returncode,
                                                   output=err.output,
                                                   message='An error occurred while executing a system '
                                                           'command inside a pake task.')

    @staticmethod
    def check_output(*args, stdin=None, shell=False, ignore_errors=False):
        """
        Return the output of a system command as a bytes object.
        
        Output will include stdout and stderr.
        
        :raises: :py:class:`pake.SubprocessException` if **ignore_errors** is False
                 and the process exits with a non zero return code.

        :raises: :py:class:`OSError` (commonly) if a the executed command or file does not exist.
                 This exception will still be raised even if **ignore_errors** is **True**.
                 
        :raises: :py:class:`ValueError` if no command + optional arguments are provided.
        
        :param args: Command arguments, same syntax as :py:meth:`pake.TaskContext.call`
        :param stdin: Optional stdin to pipe into the called process.
        :param shell: Whether to execute in shell mode or not.
        :param ignore_errors: Whether to ignore non zero return codes and return the output anyway.
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
            raise pake.process.SubprocessException(cmd=args,
                                                   returncode=err.returncode,
                                                   output=err.output,
                                                   message='An error occurred while executing a system '
                                                           'command inside a pake task.')

    def call(self, *args, stdin=None, shell=False, ignore_errors=False, silent=False, print_cmd=True):
        """Calls a sub process, all output is written to the task IO file stream.
        
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
        
        
        :param args: Process and arguments.
        :param stdin: Set the stdin of the process.
        :param shell: Whether or not to use the system shell for execution.
        :param ignore_errors: Whether or not to raise a :py:class:`pake.SubprocessException` on non 0 exit codes.
        :param silent: Whether or not to silence all output from the command.
        :param print_cmd: Whether or not to print the executed command line to the tasks output.
        
        :raises: :py:class:`pake.SubprocessException` if *ignore_errors* is *False* and the process exits with a non 0 exit code.
        
        :raises: :py:class:`OSError` (commonly) if a the executed command or file does not exist.
         This exception will still be raised even if **ignore_errors** is **True**.
         
        :raises: :py:class:`ValueError` if no command + optional arguments are provided.
        """
        args = pake.util.handle_shell_args(args)

        if len(args) < 1:
            raise ValueError('Not enough arguments provided.  '
                             'Must provide at least one argument, IE. the command.')

        self._io.flush()

        if print_cmd:
            self.print(' '.join(args))

        if ignore_errors:
            if silent:
                stdout = subprocess.DEVNULL
            else:
                stdout = self._io
                stdout.flush()

            subprocess.call(args,
                            stdout=stdout, stderr=subprocess.STDOUT,
                            stdin=stdin, shell=shell)
        else:

            with subprocess.Popen(args,
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT,
                                  stdin=stdin, shell=shell) as process:

                output_copy_buffer = tempfile.TemporaryFile(mode='w+')

                stdout_encoding = 'utf-8' if sys.stdout.encoding is None else sys.stdout.encoding  # pragma: no cover

                try:
                    process_stdout = codecs.getreader(stdout_encoding)(process.stdout)

                    if not silent:
                        pake.util.copyfileobj_tee(process_stdout, [self._io, output_copy_buffer])
                    else:  # pragma: no cover
                        pake.util.copyfileobj_tee(process_stdout, [output_copy_buffer])

                except:  # pragma: no cover
                    output_copy_buffer.close()
                    raise

                try:
                    exitcode = process.wait()
                except:  # pragma: no cover
                    output_copy_buffer.close()
                    process.kill()
                    process.wait()
                    raise

                if exitcode:
                    output_copy_buffer.seek(0)
                    raise pake.process.SubprocessException(cmd=args,
                                                           returncode=exitcode,
                                                           output_stream=output_copy_buffer,
                                                           message='An error occurred while executing a system '
                                                                   'command inside a pake task.')
                else:
                    output_copy_buffer.close()

    @property
    def dependencies(self):
        """Dependencies of this task, iterable of :py:class:`Pake.TaskGraph`"""
        return self._node.edges

    @property
    def dependency_outputs(self):
        """Returns a list of output files generated by the tasks immediate dependencies."""

        return list(pake.util.flatten_non_str(
            self.pake.get_task_context(i.func).outputs for i in self.dependencies)
        )

    def _i_io_open(self):
        self._io = tempfile.TemporaryFile(mode='w+')

    def _i_io_close(self):
        self._io.seek(0)
        shutil.copyfileobj(self._io, self.pake.stdout)
        self._io.close()

    def _i_submit_self(self, thread_pool):
        futures = [self.pake.get_task_context(i.name)._future for i in self.node.edges]

        # Wait dependents, Raise pending exceptions
        _wait_futures_and_raise(futures)

        # Submit self
        self._future = thread_pool.submit(self.node.func)

        return self._future

    @property
    def node(self):
        """The :py:class:`pake.TaskGraph` node for the task."""
        return self._node

    @property
    def pake(self):
        """The :py:class:`pake.Pake` instance the task is registered to."""
        return self._pake


class TaskGraph(pake.graph.Graph):
    """Task graph node.
    
    .. py:attribute:: func
    
        The task function associated with the node
    """

    def __init__(self, name, func):
        self._name = name
        self.func = func
        super(TaskGraph, self).__init__()

    def __call__(self, *args, **kwargs):
        self.func(*args, **kwargs)

    @property
    def name(self):
        """The task name."""
        return self._name

    def __str__(self):
        return self._name


def glob(expression):
    """Deferred file input glob, the glob is not executed until the task executes.

    This input generator handles recursive directory globs by default.
       
    Collects files for input with a unix style glob expression.
    
    Example:
           
    .. code-block:: python
    
       @pk.task(build_c, i=pake.glob('obj/*.o'), o='main')
       def build_exe(ctx):
           ctx.call(['gcc'] + ctx.inputs + ['-o'] + ctx.outputs)
           
       @pk.task(build_c, i=[pake.glob('obj_a/*.o'), pake.glob('obj_b/*.o')], o='main')
       def build_exe(ctx):
           ctx.call(['gcc'] + ctx.inputs + ['-o'] + ctx.outputs)
           
    pake.glob returns a function similar to this:
    
    .. code-block:: python
    
       def input_generator():
           return glob.glob(expression)
    """

    def input_generator():
        return file_glob(expression, recursive=True)

    return input_generator


def pattern(file_pattern):
    """Produce a substitution pattern that can be used in place of an output file.
    
    The % character represents the file name, while {dir} and {ext} represent the directory of 
    the input file, and the input file extension.
    
    Example:
    
    .. code-block:: python
    
        @pk.task(i=pake.glob('src/*.c'), o=pake.pattern('obj/%.o'))
        def build_c(ctx):
            for i, o in ctx.outdated_pairs:
                ctx.call(['gcc', '-c', i, '-o', o])
                
        @pk.task(i=[pake.glob('src_a/*.c'), pake.glob('src_b/*.c')], o=pake.pattern('{dir}/%.o'))
        def build_c(ctx):
            for i, o in ctx.outdated_pairs:
                ctx.call(['gcc', '-c', i, '-o', o])
                
                
    pake.pattern returns function similar to this:
    
    .. code-block:: python
    
       def output_generator(inputs):
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


class MultitaskContext(Executor):
    """Returned by :py:meth:`pake.TaskContext.multitask` (see for more details).  

    This object is meant to be used in a **with** statement.
    """

    def __init__(self, ctx):
        self._ctx = ctx
        self._threadpool = ctx.pake.threadpool
        self._pending = []

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
    
    :param wait: Whether or not to wait on all submitted tasks, default is true.
        """
        if wait and len(self._pending):
            _wait_futures_and_raise(self._pending)

    def __exit__(self, exc_type, exc_value, tb):
        self.shutdown()


class Pake:
    """
    Pake's main instance, which should not be initialized directly.
    
    Use: :py:meth:`pake.init` to create a :py:class:`pake.Pake` object
    and initialize the pake module.
    
    .. py:attribute:: stdout
    
        (set-able) The stream all standard task output gets written to.
    
    """

    def __init__(self, stdout=None):
        """
        Create a pake object, optionally set stdout for the instance.
        
        :param stdout: The stream all standard task output gets written to, \
                       this includes exceptions encountered inside tasks for simplicity. (defaults to pake.conf.stdout)
        """

        self._graph = TaskGraph("_", lambda: None)

        # maps task name to TaskContext
        self._task_contexts = dict()

        # maps task functions to their task name
        self._task_func_names = dict()

        self._defines = dict()
        self._dry_run_mode = False
        self._threadpool = None
        self.stdout = stdout if stdout is not None else pake.conf.stdout
        self._run_count_lock = threading.Lock()
        self._run_count = 0
        self._cur_job_count = 0

    @property
    def task_count(self):
        """Returns the number of registered tasks.
        
        :returns: Number of tasks registered to the :py:class:`pake.Pake` instance.
        """

        return len(self._task_contexts)

    @property
    def run_count(self):
        """Contains the number of tasks ran/visited by the last invocation of :py:meth:`pake.Pake.run` or :py:meth:`pake.Pake.dry_run`
        
        If a task did not run because change detection on input/output files decided it did not need to, then it does 
        not count towards this total.  This also applies when doing a dry run with :py:meth:`pake.Pake.dry_run`
        
        :returns: Number of tasks last run.
        """

        return self._run_count

    @property
    def threadpool(self):
        """Current execution thread pool, is only ever not **None** while pake is running.
        
        If pake is running with a job count of 1, no threadpool is used so this property will be **None**.
        """
        return self._threadpool

    def set_define(self, name, value):  # pragma: no cover
        """
        Set a defined value.
        
        :param name: The name of the define.
        :param value: The value of the define.
        """
        self._defines[name] = value

    def __getitem__(self, item):  # pragma: no cover
        """
        Access a define using the indexing operator []
        
        :param item: Name of the define.
        :return: The defines value, or *None*
        """
        return self.get_define(item)

    def get_define(self, name, default=None):  # pragma: no cover
        """Get a defined value.
           
        This is used to get defines off the command line, as well as retrieve
        values exported from top level pake scripts.
        
        If the define is not found, then **None** is returned by default.
        
        The indexer operator can also be used on the pake instance to fetch defines, IE:
          
        *pk['YOURDEFINE']*
        
        Which also produces **None** if the define does not exist.
        
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

    def terminate(self, return_code=pake.returncodes.SUCCESS):  # pragma: no cover
        """Shorthand for ``pake.terminate(this, return_code=return_code)``.
        
        Do not use this inside of tasks, this is meant to be used before any tasks are run.

        See for more details: :py:meth:`pake.terminate`

        :param return_code: Return code to exit the pakefile with.
                            The default return code is :py:attr:`pake.returncodes.SUCCESS`.
        """
        pake.terminate(self, return_code=return_code)

    @staticmethod
    def _process_i_o_params(i, o):
        if i is None:
            i = []
        if o is None:
            o = []

        if callable(i):
            i = list(i())
        elif type(i) is str or not pake.util.is_iterable_not_str(i):
            i = [i]

        for idx, inp in enumerate(i):
            if callable(inp):
                i[idx] = inp()

        i = list(pake.util.flatten_non_str(i))

        if callable(o):
            o = list(o(i))
        elif type(o) is str or not pake.util.is_iterable_not_str(o):
            o = [o]

        for idx, outp in enumerate(i):
            if callable(outp):
                o[idx] = outp(i)

        o = list(pake.util.flatten_non_str(o))

        return i, o

    def _increment_run_count(self):
        if self._cur_job_count > 1:
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
                if path.getmtime(output_object) < path.getmtime(input_object):
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
                    if not path.exists(output_object) or path.getmtime(output_object) < path.getmtime(input_object):
                        input_set.add(input_object)
                        output_set.add(output_object)

            outdated_inputs += input_set
            outdated_outputs += output_set

        else:
            for input_object, output_object in zip(i, o):
                if not path.exists(input_object):
                    raise InputNotFoundException(task_name, input_object)
                if not path.exists(output_object) or path.getmtime(output_object) < path.getmtime(input_object):
                    outdated_inputs.append(input_object)
                    outdated_outputs.append(output_object)

    def task(self, *args, i=None, o=None, no_header=False):
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
           
           @pk.task(dependent_task_a, dependent_task_b)
           def my_task(ctx):
               # Do your build task here
               pass
               
        Change Detection Examples:
        
        .. code-block:: python
        
           # Dependencies come before input and output files.
           
           @pk.task(dependent_task_a, dependent_task_b, i='main.c', o='main')
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
           
           @pk.task(dependent_task_a, dependent_task_b)
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
        
        
           # Single input and single output, 'main.c' has it's creation time checked
           # against 'main'
           
           @pk.task(i='main.c', o='main')
           def my_task(ctx):
               # Do your build task here
               pass
               
               
           # When multiple input files exist and there is only one output file, each input file
           # has it's creation time checked against the output files creation time.
           
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
        
        :raises: :py:class:`pake.UndefinedTaskException` if a given dependency is not a registered task function.
        :param args: Tasks which this task depends on.
        :param i: Optional input files for change detection.
        :param o: Optional output files for change detection.
        :param no_header: Whether or not to avoid printing a task header when the task begins executing, defaults to **False** (Header is printed).
                  This does not apply to dry run visits, the task header will still be printed during dry runs.
        """

        if len(args) == 1 and inspect.isfunction(args[0]):
            if args[0].__name__ not in self._task_contexts:
                func = args[0]
                self.add_task(func.__name__, func, no_header=no_header)
                return func

        if len(args) > 1 and pake.util.is_iterable_not_str(args[0]):
            dependencies = args[0]
        else:
            dependencies = args

        def outer(task_func):
            self.add_task(task_func.__name__, task_func, dependencies, i, o, no_header=no_header)
            return task_func

        return outer

    def get_task_name(self, task):
        """
        Returns the name of a task by the task function or callable reference used to define it.
        
        The name of the task may be different than the name of the task function/callable when
        :py:meth:`pake.Pake.add_task` is used to register the task.
        
        If a string is passed it is returned unmodified as long as the task exists, otherwise
        a :py:class:`pake.UndefinedTaskException` is raised.
        
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
        
        :raises: :py:class:`pake.UndefinedTaskException` if the task function/callable is not registered to the pake context.
        :raises: :py:class:`ValueError` if the **task** parameter is not a string or a callable function/object.
        
        :return: Task name string
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
        
        :raises: :py:class:`pake.UndefinedTaskException` if the task in not registered.
        :param task: Task function or function name as a string
        :return: :py:class:`pake.TaskContext`
        """

        task = self.get_task_name(task)

        context = self._task_contexts.get(task, None)
        if context is None:
            raise UndefinedTaskException(task)
        return context

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

        if len(i) > 0 or len(o) > 0:
            if len(outdated_inputs) > 0 or len(outdated_outputs) > 0:
                return True

        return False

    def add_task(self, name, func, dependencies=None, inputs=None, outputs=None, no_header=False):
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
        :param dependencies: List of dependent tasks or single task, by name or by reference
        :param inputs: List of input files/directories, or a single input (accepts input file generators like :py:meth:`pake.glob`)
        :param outputs: List of output files/directories, or a single output (accepts output file generators like :py:meth:`pake.pattern`)
        :param no_header: Whether or not to avoid printing a task header when the task begins executing, defaults to **False** (Header is printed).
                          This does not apply to dry run visits, the task header will still be printed during dry runs.
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
                    if not no_header:
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

        :raises: :py:class:`ValueError` if **jobs** is less than 1.
        
        :raises: :py:class:`pake.TaskException` if an exception occurred while running a task, information will have \
                 already been printed to the :py:attr:`pake.TaskContext.io` file object which belongs to the given task.
        
        :raises: :py:class:`pake.TaskExitException` if **exit()** is called inside of a task.
        
        :raises: :py:class:`pake.MissingOutputsException` if a task defines input files/directories without specifying any output files/directories.
        :raises: :py:class:`pake.InputNotFoundException` if a task defines input files/directories but one of them was not found on disk.
        :raises: :py:class:`pake.CyclicGraphException` if a cycle is found in the dependency graph.
        :raises: :py:class:`pake.UndefinedTaskException` if one of the default tasks given in the *tasks* parameter is unregistered. 
        
        :param tasks: Single task, or Iterable of task functions to run (by ref or name).
        :param jobs: Maximum number of threads, defaults to 1. (must be >= 1)
        """

        if not pake.util.is_iterable_not_str(tasks):
            tasks = [tasks]

        if jobs < 1:
            raise ValueError('Job count must be >= to 1.')

        self._cur_job_count = jobs
        self._run_count = 0

        graphs = []
        if tasks:
            for task in tasks:
                graphs.append(self.get_task_context(task).node.topological_sort())
        else:
            graphs.append(self._graph.topological_sort())

        if jobs == 1:
            for graph in graphs:
                for i in graph:
                    i()
            return

        executor = None
        pending = []
        try:
            executor = ThreadPoolExecutor(max_workers=jobs)
            self._threadpool = executor
            for graph in graphs:
                for i in (i for i in graph if i is not self._graph):
                    context = self.get_task_context(i.name)
                    pending.append(context._i_submit_self(executor))
        finally:
            _wait_futures_and_raise(pending)
            self._threadpool = None
            if executor:
                executor.shutdown(wait=False)

    def dry_run(self, tasks):
        """
        Dry run over task, print a 'visited' message for each visited task.
        
        When using change detection, only out of date tasks will be visited.
        

        :raises: :py:class:`pake.MissingOutputsException` if a task defines input files/directories without specifying any output files/directories.
        :raises: :py:class:`pake.InputNotFoundException` if a task defines input files/directories but one of them was not found on disk.
        :raises: :py:class:`pake.CyclicGraphException` if a cycle is found in the dependency graph.
        :raises: :py:class:`pake.UndefinedTaskException` if one of the default tasks given in the *tasks* parameter is unregistered. 
        
        :param tasks: Single task, or Iterable of task functions to run (by ref or name).
        """
        self._dry_run_mode = True
        try:
            self.run(tasks=tasks, jobs=1)
        finally:
            self._dry_run_mode = False

    def set_defines_dict(self, dictionary):  # pragma: no cover
        """
        Set an overwrite all defines with a dictionary object.
        
        :param dictionary: The dictionary object
        """
        self._defines = dict(dictionary)

    def print(self, *args, **kwargs):  # pragma: no cover
        """Shorthand for print(..., file=this_instance.stdout)"""

        kwargs.pop('file', None)
        print(*args, file=self.stdout, **kwargs)
