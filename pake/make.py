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


import concurrent.futures
import inspect
import itertools
import os
import threading
import traceback
import sys
import pake.submake
import pake.console

from pake.exception import PakeException
from pake.graph import topological_sort, check_cyclic, CyclicDependencyException
from pake.util import ReadOnlyList, is_iterable_not_str


class TargetAggregateException(PakeException):
    """Raised when an exception that does not derive from
       :py:class:`pake.exception.PakeException` is raised while a target is executing."""

    def __init__(self, inner_exceptions):
        self._inner_exceptions = inner_exceptions
        super().__init__(self.inner_trace_str)

    def _get_trace(self, exception):
        if isinstance(exception[1], PakeException):
            return str(exception[1]).rstrip('\n')
        else:
            return (''.join(traceback.format_exception(None, exception[1], exception[1].__traceback__))).rstrip('\n')

    @property
    def inner_trace_str(self):
        """Returns a formatted stack trace string for the inner exception."""
        except_str = ['Exception encountered in target "{target}", stack trace:\n\n{trace}'
                      .format(target=x[0].name, trace=self._get_trace(x)) for x in self._inner_exceptions]

        return 'One or more exceptions were raised inside pake targets:\n\n' + '\n\n'.join(except_str)

    @property
    def inner_exceptions(self):
        """Returns a list in the form [(:py:class:`pake.make.Target`, exception_object), ...] representing all
        exceptions raised inside pake targets which do not derive from :py:class:`pake.exception.PakeException`."""
        return self._inner_exceptions


class TargetRedefinedException(PakeException):
    """Raised when the same target function is registered to a :py:class:`pake.make.Make` instance more than once"""
    pass


class UndefinedTargetException(PakeException):
    """Raised in cases where a target function is not registered to a :py:class:`pake.make.Make` instance
    when it should be in order for a given operation to complete."""
    pass


class TargetInputNotFoundException(PakeException):
    """Raised when one of a targets input files is not found at the time of that targets execution."""

    def __init__(self, target, input_file):
        super().__init__('Input "{input}" of Target "{target}" did not exist upon target execution.'
                         .format(target=target.name, input=input_file))
        self._target = target
        self._input = input

    @property
    def target(self):
        """Return a reference to the :py:class:`pake.make.Target` instance that has the missing input.

        :rtype: pake.make.Target
        """
        return self._target_function

    @property
    def input(self):
        """Return the path to the missing input.

        :rtype: str
        """
        return self._input


class Target:
    """Holds information about a registered targets inputs, outputs, dependencies etc.
    This is a contextual object that is created for each target function registered to a :py:meth:`pake.make.Make`
    instance, it can be retrieved by passing a given targets function reference or function name to
    :py:meth:`pake.make.Make.get_target`

    An instance of a registered targets :py:class:`pake.make.Target` object is passed to it's target function as
    the first argument when the target executes.  A target functions first argument can be omitted and
    pake will avoid passing it to the target function when it is not needed.
    """

    def __init__(self, make, function, inputs, outputs, dependencies, info=None):
        self._make = make
        self._function = function
        self._inputs = inputs
        self._outputs = outputs
        self._dependencies = dependencies
        self._outdated_inputs = []
        self._outdated_outputs = []
        self._dependency_outputs = [output for output in
                                    itertools.chain.from_iterable(self._make.get_outputs(d)
                                                                  for d in self._dependencies)]
        if info is None:
            self._info = info
        else:
            self._info = str(info)

        self._print_queue = []
        self._print_queue_lock = threading.RLock()

    def _write_stdout_queue(self):
        sys.stdout.write(''.join(self._print_queue))
        self._print_queue.clear()

    def run_script(self, script_path, *args, stdout_collect=True):
        """Run a sub pakefile and print it's output to stdout in a synchronized fashion.  See
        :py:meth:`pake.submake.run_script`.

        :param script_path: The path to the pakefile that is going to be ran.
        :param args: Command line arguments to pass the pakefile.
        :param stdout_collect: If set to True, the scripts output will be collected and written all at once to the targets
                               stdout queue.  Otherwise the scripts output will be written line by line as it is read from
                               the stdout pipe.

        :raises FileNotFoundError: Raised if the given pakefile script does not exist.
        :raises pake.submake.SubMakeException: Raised if the submake script exits in a non successful manner.

        """

        pake.submake.run_script(script_path, *args, stdout=self, stdout_collect=stdout_collect)

    def print_error(self, *objects, sep=' ', end='\n'):
        """Print red colored data to stdout in a synchronized fashion.  See :py:meth:`pake.console.print_warning`."""
        pake.console.print_error(*objects, sep=sep, end=end, file=self)

    def print_warning(self, *objects, sep=' ', end='\n'):
        """Print yellow colored data to stdout in a synchronized fashion.  See :py:meth:`pake.console.print_warning`."""
        pake.console.print_warning(*objects, sep=sep, end=end, file=self)

    def print(self, *objects, sep=' ', end='\n'):
        """Print data to stdout in a synchronized fashion."""
        print(*objects, sep=sep, end=end, file=self)

    def write(self, data):
        """Write data to stdout in a synchronized fashion."""
        if self._make.get_max_jobs() > 1:
            with self._print_queue_lock:
                self._print_queue.append(data)
        else:
            sys.stdout.write(data)

    @property
    def info(self):
        """Get the info string for the target.

        :return: The target info string, or None if no info string exists.
        :rtype: str
        """

        return self._info

    @property
    def name(self):
        """Get the name of the target function.

        :return: The name of the target function.
        :rtype: str
        """
        return self._function.__name__

    @property
    def function(self):
        """Gets the function that is executed by this target.

        :return: A function reference.
        :rtype: func
        """
        return self._function

    @property
    def dependency_outputs(self):
        """Gets a read only list outputs produced by this targets immediate dependencies.

        :return: Read only list outputs from this targets immediate dependencies.
        :rtype: pake.util.ReadOnlyList
        """
        return ReadOnlyList(self._dependency_outputs)

    @property
    def dependencies(self):
        """Gets a read only list of dependencies for the target.

        The dependencies are listed as function references, you can resolve their :py:class:`pake.make.Target`
        instance by using :py:meth:`pake.make.Make.get_target` on the :py:class:`pake.make.Make` instance the dependency
        was registered to.

        :return: Read only list of target inputs.
        :rtype: pake.util.ReadOnlyList
        """
        return ReadOnlyList(self._dependencies)

    @property
    def inputs(self):
        """Gets a read only list of inputs for the target.

        :return: Read only list of target inputs.
        :rtype: pake.util.ReadOnlyList
        """
        return ReadOnlyList(self._inputs)

    @property
    def outputs(self):
        """Gets a read only list of outputs for the target.

        :return: Read only list of target outputs.
        :rtype: pake.util.ReadOnlyList
        """
        return ReadOnlyList(self._outputs)

    @property
    def make(self):
        """Gets the :py:class:`pake.make.Make` instance which this target is registered in.

        :return: pake.make.Make
        """

        return self._make

    def _add_outdated_input_output(self, input_file, output_file):
        self._add_outdated_input(input_file)
        self._add_outdated_output(output_file)

    def _add_outdated_input(self, input_file):
        if is_iterable_not_str(input_file):
            self._outdated_inputs += list(input_file)
        else:
            self._outdated_inputs.append(input_file)

    def _add_outdated_output(self, input_file):
        if is_iterable_not_str(input_file):
            self._outdated_outputs += list(input_file)
        else:
            self._outdated_outputs.append(input_file)

    @property
    def outdated_inputs(self):
        """Gets a read only list of target inputs that pake considers to be outdated.

        :returns: Read only list of outdated target inputs.
        :rtype: pake.util.ReadOnlyList
        """

        return ReadOnlyList(self._outdated_inputs)

    @property
    def outdated_outputs(self):
        """Gets a read only list of target outputs that pake considers to be outdated.

        :returns: Read only list of outdated target outputs.
        :rtype: pake.util.ReadOnlyList
        """

        return ReadOnlyList(self._outdated_outputs)

    def __hash__(self):
        return hash(self.function)

    def __eq__(self, other):
        return self.function is other.function


def _is_input_newer(input_file, output_file):
    return (os.path.getmtime(input_file) - os.path.getmtime(output_file)) > 0.1


class Make:
    """The make context class.  Target functions can be registered to an instance of this class
    using the :py:meth:`pake.make.Make.target` python decorator, or manually using the :py:meth:`pake.make.Make.add_target`
    function.

    This class can execute registered targets in the correct order according to their dependencies, it also handles file
    change detection based off each targets inputs and outputs.

    It is the main context object used by pake, an instance is returned by :py:meth:`pake.program.init`.
    """

    def __init__(self):
        self._target_graph = {}
        self._target_funcs_by_name = {}
        self._run_targets = []
        self._outdated_target_funcs = set()
        self._task_dict_lock = threading.RLock()
        self._target_func_to_task_dict = {}
        self._max_jobs = 1
        self._last_run_count = 0
        self._defines = {}
        self._task_exceptions_lock = threading.RLock()
        self._task_exceptions = []
        self._target_print_lock = threading.RLock()

    def __getitem__(self, name):
        """Retrieve the value of a define, returns None if the define does not exist.

        :param name: The name of the define.
        :type name: str
        :return: The defines value, or None if the define does not exist.
        """
        return self.get_define(name)

    def set_defines(self, defines_dict):
        """Set the available defines for this :py:class:`pake.make.Make` instance.

        :param defines_dict: A dictionary of defined values, in the format {str: value}
        """
        self._defines = dict(defines_dict)

    def get_define(self, name, default=None):
        """Get the value of a define, or an alternative default.

        By default, if the given define does not exist this method returns None, a default can be specified
        in the second parameter.

        :param name: The name of the define.
        :type name: str
        :param default: The optional default value of the define, the normal default is None
        :return: The defines value.
        """
        if name in self._defines:
            return self._defines[name]
        else:
            return default

    def _get_threadpool_executor(self):
        return concurrent.futures.ThreadPoolExecutor(max_workers=self.get_max_jobs())

    def set_run_targets(self, *target_functions):
        """Set the entry targets for the next call to execute.  These are the targets that will be ran.

        :param target_functions: List of target function names, or direct references to target functions.

        :raises pake.make.UndefinedTargetException: Raised if a given target is not a registered target reference or name.
        """

        if is_iterable_not_str(target_functions[0]):
            self._run_targets = self._resolve_target_strings(target_functions[0])
        else:
            self._run_targets = self._resolve_target_strings(target_functions)

    def target_count(self):
        """Get the number of defined targets.

        :return: The number of currently defined targets.
        :rtype: int
        """
        return len(self._target_graph)

    def get_last_run_count(self):
        """Get the number of targets executed during the last run.

        :return: The number of targets executed during the last run.
        :rtype: int
        """
        return self._last_run_count

    def set_max_jobs(self, count):
        """Set the max number of targets that can run in parallel.

         :raises ValueError: Raised if count is less than 1.

        :param count: The max number of targets that can run in parallel at a time.
        :type count: int
        """

        if count < 1:
            raise ValueError("Max job count must be greater than zero.")
        self._max_jobs = count

    def get_max_jobs(self):
        """Get the max number of targets that can run in parallel.

        :return: The max number of targets that can run in parallel.
        :rtype: int
        """
        return self._max_jobs

    def is_target(self, target_function):
        """Determine if a specific function is a registered pake target.

        :param target_function: The function to test.
        :type target_function: func
        :return: True if target_function is a registered pake target.
        :rtype: bool
        """

        if type(target_function) is str:
            return target_function in self._target_funcs_by_name
        return target_function in self._target_graph

    def get_all_targets(self):
        """Get a list of :py:class:`pake.make.Target` representing the targets registered to this :py:class:`pake.make.Make` object.

        :return: List of :py:class:`pake.make.Target` objects
        :rtype: list
        """
        return list(t for k, t in self._target_graph.items())

    def target(self, *args, **kwargs):
        """Decorator for registering pake targets, this decorator delegates to :py:meth:`pake.make.Make.add_target`.

        :param target_function: The function for the target.
        :type target_function: func

        :param info: (Optional) information string for the target.  :py:meth:`pake.program.run` can display
                     documented targets with their corresponding info string when the -ti/--target-info option is passed
                     to a pakefile script.
        :type info: str
        :param inputs: (Optional) input files for the target, used for change detection.
                       This may be a single string, or a list of strings.
        :type inputs: str, or list of str
        :param outputs: (Optional) output files for the target, used for change detection.
                        This may be a single string, or a list of strings.
        :type outputs: str, or list of str
        :param depends: (Optional) dependencies, this may be a list of other target function references, or a single target function.
                        Functions may be referenced by string but they must be previously defined.
        :type depends: func/str, or list of func/str

        :raises pake.make.TargetRedefinedException: Raised if the given target_function has already been registered as a target.
        :raises pake.make.UndefinedTargetException: Raised if there is a reference to an unregistered target in this targets dependencies.
        """

        if len(args) == 1 and inspect.isfunction(args[0]):
            self.add_target(args[0])
            return args[0]

        def wrapper(f):
            self.add_target(f, **kwargs)
            return f

        return wrapper

    def get_target(self, target_function):
        """Get the :py:class:`pake.make.Target` object that holds details regarding a registered target function.

        :param target_function: The registered target function to return the :py:class:`pake.make.Target` instance for.
        :type target_function: func
        :return: :py:class:`pake.make.Target` representing the defails of a registered target function.
        """

        if type(target_function) is str:
            return self._target_graph[self._target_funcs_by_name[target_function]]
        return self._target_graph[target_function]

    def get_outputs(self, target_function):
        """Gets the outputs of a registered target function.

        :param target_function:
        :type target_function: func
        :return: List of declared output files, as str objects.
        :rtype: list of str
        """

        return self.get_target(target_function).outputs

    def get_inputs(self, target_function):
        """Gets the inputs of a registered target function.

        :param target_function:
        :type target_function: func
        :return: List of declared input files, as str objects.
        :rtype: list of str
        """
        return self.get_target(target_function).inputs

    def get_dependencies(self, target_function):
        """Gets the dependencies of a registered target function.

        :param target_function:
        :type target_function: func
        :return: List of declared target functions, as func objects.
        :rtype: list of func
        """
        return self.get_target(target_function).dependencies

    def add_target(self, target_function, inputs=None, outputs=None, depends=None, info=None):
        """Manually register a pake target function.

        :param target_function: The function for the target.
        :type target_function: func

        :param info: (Optional) information string for the target.  :py:meth:`pake.program.run` can display
                     documented targets with their corresponding info string when the -ti/--target-info option is passed
                     to a pakefile script.
        :type info: str
        :param inputs: (Optional) input files for the target, used for change detection.
                       This may be a single string, or a list of strings.
        :type inputs: str, or list of str
        :param outputs: (Optional) output files for the target, used for change detection.
                        This may be a single string, or a list of strings.
        :type outputs: str, or list of str
        :param depends: (Optional) dependencies, this may be a list of other target function references, or a single target function.
                        Functions may be referenced by string but they must be previously defined.
        :type depends: func/str, or list of func/str

        :raises pake.make.TargetRedefinedException: Raised if the given target_function has already been registered as a target.
        :raises pake.make.UndefinedTargetException: Raised if there is a reference to an unregistered target in this targets dependencies.
        """

        if not depends:
            depends = []
        if not inputs:
            inputs = []
        if not outputs:
            outputs = []

        if type(depends) is not list:
            depends = [depends]
        if type(inputs) is not list:
            inputs = [inputs]
        if type(outputs) is not list:
            outputs = [outputs]

        if target_function in self._target_graph:
            raise TargetRedefinedException('Target "{target}" already defined.'
                                           .format(target=target_function.__name__))
        else:
            resolved_dependencies = self._resolve_target_strings(depends)

            self._target_graph[target_function] = Target(
                self,
                target_function,
                inputs,
                outputs,
                resolved_dependencies,
                info
            )

            self._target_funcs_by_name[target_function.__name__] = target_function

    def _handle_target_out_of_date(self, target):
        dependencies, inputs, outputs = target.dependencies, target.inputs, target.outputs

        for i in inputs:
            if not os.path.exists(i):
                raise TargetInputNotFoundException(target, i)

        for d in dependencies:
            if d in self._outdated_target_funcs:
                target._add_outdated_input_output(inputs, outputs)
                return True

        if len(inputs) == len(outputs):
            if len(inputs) == 0:
                return True

            out_of_date = False
            for x in range(0, len(inputs)):
                i, o = inputs[x], outputs[x]
                if not os.path.exists(o):
                    target._add_outdated_input_output(i, o)
                    out_of_date = True
                elif _is_input_newer(i, o):
                    target._add_outdated_input_output(i, o)
                    out_of_date = True

            if out_of_date:
                return True
        else:
            if len(inputs) == 0 and len(outputs) > 0:
                for o in outputs:
                    if not os.path.exists(o):
                        target._add_outdated_output(o)
                        return True

            if len(inputs) > 0 and len(outputs) == 0:
                return True

            for o in outputs:
                if not os.path.exists(o):
                    target._add_outdated_input_output(inputs, outputs)
                    return True
                for i in inputs:
                    if _is_input_newer(i, o):
                        target._add_outdated_input_output(inputs, outputs)
                        return True

        return False

    def _sort_graph(self):
        def get_edges(e):
            return e.dependencies

        if check_cyclic(self._target_graph, get_edges=get_edges):
            raise CyclicDependencyException("Cyclic target dependency detected.")

        visited, no_dep_targets, graph_out, to_visit = set(), set(), [], []

        for target_function in self._run_targets:
            target = self._target_graph[target_function]
            dependencies = target.dependencies
            if len(dependencies) == 0:
                if target_function not in no_dep_targets:
                    no_dep_targets.add(target_function)
                    visited.add(target_function)
            else:
                to_visit.append((target_function, target))

        while to_visit:
            cur = to_visit.pop()
            if cur[0] not in visited:
                to_visit.extend(
                    [(edge, self._target_graph[edge]) for edge in cur[1].dependencies])

                graph_out.insert(0, (cur[0], cur[1]))
                visited.add(cur[0])

        return itertools.chain(((no_deps, self.get_target(no_deps)) for no_deps in no_dep_targets),
                               topological_sort(graph_out, get_edges=get_edges))

    def _resolve_target_strings(self, target_functions):
        result = list(target_functions)
        for i in range(0, len(result)):
            target = result[i]
            if type(target) is str:
                if target in self._target_funcs_by_name:
                    result[i] = self._target_funcs_by_name[target]
                else:
                    raise UndefinedTargetException('Target "{target}" is not defined.'
                                                   .format(target=target))
            elif not inspect.isfunction(target):
                raise ValueError('Given target "{obj}" was neither a function or a string.'
                                 .format(obj=target))
        return result

    def _target_task_exists(self, target_function):
        return target_function in self._target_func_to_task_dict

    def _target_task_running(self, target_function):
        return self._target_func_to_task_dict[target_function].running()

    def _run_target_task(self, target):
        with self._task_dict_lock:
            for dep_target_func in target.dependencies:
                if self._target_task_exists(dep_target_func):
                    task = self._target_func_to_task_dict[dep_target_func]
                    if self._target_task_running(dep_target_func):
                        task.result()

        sig = inspect.signature(target.function)
        if len(sig.parameters) > 0:
            target.function(target)
        else:
            target.function()

    def _run_target(self, thread_pool, target):
        def done_callback(t):
            with self._target_print_lock:
                target._write_stdout_queue()
            if t.exception():
                with self._task_exceptions_lock:
                    self._task_exceptions.append(
                        (target, t.exception())
                    )

        task = thread_pool.submit(self._run_target_task, target)
        task.add_done_callback(done_callback)
        with self._task_dict_lock:
            self._target_func_to_task_dict[target.function] = task

    def execute(self):
        """Execute out of date targets, IE. run pake.

        :raises pake.graph.CyclicDependencyException: Raised if a cyclic dependency is detected in the target graph.
        :raises pake.make.TargetInputNotFoundException: Raised if one of a targets inputs does not exist upon target execution.

        :raise pake.make.TargetAggregateException: Raised if an exception not derived from :py:class:`pake.exception.PakeException`
                                               is thrown inside of a target function.
        """

        self._last_run_count = 0

        with self._get_threadpool_executor() as thread_pool:
            for node in self._sort_graph():
                target = node[1]
                if self._handle_target_out_of_date(target):
                    self._last_run_count += 1
                    self._outdated_target_funcs.add(target.function)
                    self._run_target(thread_pool, target)

            self._outdated_target_funcs = set()

        self._dispatch_target_exceptions()
        self._target_func_to_task_dict = {}

    def _dispatch_target_exceptions(self):
        ex = list(self._task_exceptions)
        self._task_exceptions.clear()
        if len(ex) > 0:
            raise TargetAggregateException(ex)

    def visit(self, visitor=None):
        """Visit out of date targets without executing them, the default visitor prints:  "Execute Target: target_function_name"

        :param visitor: (Optional) A function which takes a single :py:class:`pake.make.Target` argument.
                        It can be used to visit out of date targets.

        :raises pake.graph.CyclicDependencyException: Raised if a cyclic dependency is detected in the target graph.
        :raises pake.make.TargetInputNotFoundException: Raised if one of a targets inputs does not exist upon visiting the target.
        """

        if not visitor:
            def visitor(target):
                print("Execute Target: " + target.function.__name__)

        self._last_run_count = 0

        for node in self._sort_graph():
            target_function = node[0]
            if self._handle_target_out_of_date(target_function):
                self._last_run_count += 1
                visitor(self._target_graph[target_function])

        self._dispatch_target_exceptions()
        self._target_func_to_task_dict = {}

    def clear_targets(self):
        """Clear all registered targets, and run targets set by :py:meth:`pake.make.Make.set_run_targets`"""

        self._target_graph = {}
        self._target_funcs_by_name = {}
        self._run_targets = []
