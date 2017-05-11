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
import subprocess
import tempfile
import threading
import traceback
from functools import wraps
from glob import glob as file_glob

import os
import pake
from concurrent.futures import ThreadPoolExecutor, wait as futures_wait, Executor, Future
from os import path

import pake.conf
import pake.graph
import pake.process
import pake.util

__all__ = ['pattern',
           'glob',
           'Pake',
           'TaskContext',
           'MultitaskContext',
           'TaskGraph',
           'UndefinedTaskException',
           'RedefinedTaskException',
           'TaskException',
           'InputFileNotFoundException']


class TaskException(Exception):
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
        self.exception = exception

    def __str__(self):
        return str(self.exception)


class MissingOutputFilesException(Exception):
    """
    Raised by :py:meth:`pake.Pake.run` and :py:meth:`pake.Pake.dry_run` if a task declares input files without
    specifying any output files.
    """

    def __init__(self, task_name):
        super(MissingOutputFilesException, self).__init__(
            'Task "{}" defines inputs with no outputs, this is not allowed.'.format(task_name)
        )


class InputFileNotFoundException(Exception):
    """
    Raised by :py:meth:`pake.Pake.run` and :py:meth:`pake.Pake.dry_run` if a task with input files 
    declared cannot find an input file on disk.
    """

    def __init__(self, task_name, file_name):
        super(InputFileNotFoundException, self).__init__(
            'Could not find input file "{}" used by task "{}".'.format(file_name, task_name)
        )


class UndefinedTaskException(Exception):
    """Raised on attempted lookup/usage of an unregistered task function or task name.
    
    .. py:attribute:: task_name
    
        The name of the referenced task.
    """

    def __init__(self, task_name):
        super(UndefinedTaskException, self).__init__('Task "{}" is undefined.'.format(task_name))
        self.task_name = task_name


class RedefinedTaskException(Exception):
    """Raised on registering a duplicate task.
    
    .. py:attribute:: task_name
    
        The name of the redefined task.
    """

    def __init__(self, task_name):
        super(RedefinedTaskException, self).__init__('Task "{}" has already been defined.'
                                                     .format(task_name))
        self.task_name = task_name


def _handle_task_exception(ctx, exception):
    if isinstance(exception, pake.process.SubprocessException):
        # SubprocessException provides detailed information
        # about the call site of the subprocess in the pakefile
        # on its own, print and wrap as it is better for this information
        # to be printed to the task's output.
        ctx.print(str(exception))
        raise TaskException(exception)

    if isinstance(exception, InputFileNotFoundException) or isinstance(exception, MissingOutputFilesException):
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
    
        All file inputs, or an empty list
        
    .. py:attribute:: outputs
    
        All file outputs, or an empty list
       
    .. py:attribute:: outdated_inputs
    
        All changed file inputs (or inputs who's corresponding output is missing), or an empty list.
        
    .. py:attribute:: oudated_outputs
    
        All out of date file outputs, or an empty list
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
        """
        args = pake.util.handle_shell_args(args)

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
            try:
                output = subprocess.check_output(args, stderr=subprocess.STDOUT,
                                                 stdin=stdin, shell=shell)
                if not silent:
                    self._io.flush()
                    self._io.write(output.decode())

            except subprocess.CalledProcessError as err:
                raise pake.process.SubprocessException(cmd=args,
                                                       returncode=err.returncode,
                                                       output=err.output,
                                                       message='An error occurred while executing a system '
                                                               'command inside a pake task.')

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
        self.pake.stdout.write(self._io.read())
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


class _OutPattern:
    def __init__(self, file_pattern):
        self._pattern = file_pattern

    def _do_template(self, i):
        name = os.path.splitext(os.path.basename(i))[0]
        return self._pattern.replace('%', name)

    def __call__(self, inputs):
        for i in inputs:
            yield self._do_template(i)


class _Glob:
    def __init__(self, expression):
        self._expression = expression

    def __call__(self):
        return file_glob(self._expression)


def glob(expression):
    """Deferred file input glob,  the glob is not executed until the task executes.
       
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
        return file_glob(expression)

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

    def _submit_this_thread(self, fn, *args, **kwargs):
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
        self._task_contexts = dict()
        self._defines = dict()
        self._dry_run_mode = False
        self._threadpool = None
        self.stdout = stdout if stdout is not None else pake.conf.stdout
        self._run_count_lock = threading.Lock()
        self._run_count = 0
        self._cur_job_count = 0

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

    def get_define(self, name, default=None):
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
            raise MissingOutputFilesException(task_name)

        outdated_inputs = []
        outdated_outputs = []

        if len_i == 0 and len_o == 0:
            return [], []

        if len_o > 1:
            if len_i == 0:
                for op in o:
                    if not path.isfile(op):
                        outdated_outputs.append(op)

            elif len_o != len_i:
                output_set = set()
                input_set = set()

                for ip in i:
                    if not path.isfile(ip):
                        raise InputFileNotFoundException(task_name, ip)
                    for op in o:
                        if not path.isfile(op) or path.getmtime(op) < path.getmtime(ip):
                            input_set.add(ip)
                            output_set.add(op)

                outdated_inputs += input_set
                outdated_outputs += output_set

            else:
                for iopair in zip(i, o):
                    ip, op = iopair[0], iopair[1]

                    if not path.isfile(ip):
                        raise InputFileNotFoundException(task_name, ip)
                    if not path.isfile(op) or path.getmtime(op) < path.getmtime(ip):
                        outdated_inputs.append(ip)
                        outdated_outputs.append(op)

        else:
            op = o[0]
            if not path.isfile(op):

                for ip in i:
                    if not path.isfile(ip):
                        raise InputFileNotFoundException(task_name, ip)

                outdated_outputs.append(op)
                outdated_inputs += i

                return outdated_inputs, outdated_outputs

            outdated_output = None
            for ip in i:
                if not path.isfile(ip):
                    raise InputFileNotFoundException(task_name, ip)
                if path.getmtime(op) < path.getmtime(ip):
                    outdated_inputs.append(ip)
                    outdated_output = op

            if outdated_output:
                outdated_outputs.append(outdated_output)

        return outdated_inputs, outdated_outputs

    def task(self, *args, i=None, o=None):
        """
        Decorator for registering pake tasks.
        
        Any input files specified must be accompanied by at least one output file.
        
        
        A callable object, or list of callable objects may be passed to **i** or **o** in addition to
        a raw file name or names.  This is how **pake.glob** and **pake.pattern** work.
        
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
               
           
           @pk.task(i=[gen_inputs('src_a/*.c'), gen_inputs('src_b/*.c'), o=gen_outputs('{dir}/%.o')]
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
               
           @pk.task(i='main.c', o='main')
           def my_task(ctx):
               # Do your build task here
               pass
               
           @pk.task(i=['otherstuff.c', 'main.c'], o='main')
           def my_task(ctx):
               # Do your build task here
               pass
               
           @pk.task(i=pake.glob('src/*.c', o='main')
           def my_task(ctx):
               # Do your build task here
               pass
               
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
        
        :raises: :py:class:`pake.UndefinedTaskException` if a given dependency is not a registered task function.
        :param args: Tasks which this task depends on.
        :param i: Optional input files for change detection.
        :param o: Optional output files for change detection.
        """

        if len(args) == 1 and inspect.isfunction(args[0]):
            if args[0].__name__ not in self._task_contexts:
                func = args[0]
                self._add_task(func.__name__, func)
                return func

        if len(args) > 1 and pake.util.is_iterable_not_str(args[0]):
            dependencies = args[0]
        else:
            dependencies = args

        def outer(task_func):
            self._add_task(task_func.__name__, task_func, dependencies, i, o)
            return task_func

        return outer

    def get_task_context(self, task):
        """
        Get the :py:class:`pake.TaskContext` object for a specific task.
        
        :raises: :py:class:`pake.UndefinedTaskException` if the task in not registered.
        :param task: Task function or function name as a string
        :return: :py:class:`pake.TaskContext`
        """

        task = pake.util.get_task_arg_name(task)

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

    def _add_task(self, name, func, dependencies=None, inputs=None, outputs=None):
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
                    ctx.print('Visited Task: "{}"'.format(func.__name__))
                else:
                    ctx.print('===== Executing Task: "{}"'.format(func.__name__))
                    return func(*args, **kwargs)

            except Exception as err:
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

        if dependencies:
            for dependency in dependencies:
                dep_task = self.get_task_context(dependency)
                task_context.node.add_edge(dep_task.node)
                self._graph.remove_edge(dep_task.node)

        self._graph.add_edge(task_context.node)

        return task_context

    def run(self, tasks=None, jobs=1):
        """
        Run all given tasks, with an optional level of concurrency.

        :raises: :py:class:`ValueError` if **jobs** is less than 1.
        
        :raises: :py:class:`pake.TaskException` if an exception occurred while running a task, information will have \
                 already been printed to the :py:attr:`pake.TaskContext.io` file object which belongs to the given task.
        
        :raises: :py:class:`pake.MissingOutputFilesException` if a task defines input files without specifying any output files.
        :raises: :py:class:`pake.InputFileNotFoundException` if a task defines input files but one of them was not found on disk.
        :raises: :py:class:`pake.CyclicGraphException` if a cycle is found in the dependency graph.
        :raises: :py:class:`pake.UndefinedTaskException` if one of the default tasks given in the *tasks* parameter is unregistered. 
        
        :param tasks: Tasks to run. 
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

    def dry_run(self, tasks=None):
        """
        Dry run over task, print a 'visited' message for each visited task.
        
        When using change detection, only out of date tasks will be visited.
        

        :raises: :py:class:`pake.MissingOutputFilesException` if a task defines input files without specifying any output files.
        :raises: :py:class:`pake.InputFileNotFoundException` if a task defines input files but one of them was not found on disk.
        :raises: :py:class:`pake.CyclicGraphException` if a cycle is found in the dependency graph.
        :raises: :py:class:`pake.UndefinedTaskException` if one of the default tasks given in the *tasks* parameter is unregistered. 
        
        :param tasks: Tasks to run.
        """
        self._dry_run_mode = True
        try:
            self.run(tasks=tasks, jobs=1)
        finally:
            self._dry_run_mode = False

    def set_defines_dict(self, dictionary):
        """
        Set an overwrite all defines with a dictionary object.
        
        :param dictionary: The dictionary object
        """
        self._defines = dict(dictionary)

    def print(self, *args, **kwargs):
        """Shorthand for print(..., file=this_instance.stdout)"""

        kwargs.pop('file', None)
        print(*args, file=self.stdout, **kwargs)
