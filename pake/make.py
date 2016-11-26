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


from pake.topologicalsort import topological_sort
import itertools
import threading
import concurrent.futures
import inspect
import os


class TargetRedefinedException(Exception):
    pass


class UndefinedTargetException(Exception):
    pass


class TargetInputNotFound(FileNotFoundError):
    pass


def _is_iterable(obj):
    try:
        a = iter(obj)
    except TypeError:
        return False
    return True


def _is_iterable_not_str(obj):
    return _is_iterable(obj) and type(obj) is not str


class Target:
    def __init__(self, function, inputs, outputs, dependencies):
        self.function = function
        self.inputs = inputs
        self.outputs = outputs
        self.dependencies = dependencies

    @property
    def output(self):
        return self.outputs[0]

    @property
    def input(self):
        return self.inputs[0]

    def __hash__(self):
        return hash(self.function)

    def __eq__(self, other):
        return self.function is other.function


class Make:
    def __init__(self):
        self._target_graph = {}
        self._target_funcs_by_name = {}
        self._run_targets = []
        self._outdated_target_funcs = set()
        self._task_dict_lock = threading.RLock()
        self._task_dict = {}
        self._max_jobs = 1
        self._last_run_count = 0
        self._defines = {}

    def __getitem__(self, item):
        if item in self._defines:
            return self._defines[item]
        else:
            return None

    def set_defines(self, defines_dict):
        if type(defines_dict) is not dict:
            raise ValueError('defines_dict must be a dictionary.')
        self._defines = defines_dict

    def get_defines(self):
        return self._defines

    def get_last_run_count(self):
        return self._last_run_count

    def set_max_jobs(self, count):
        if count < 1:
            raise ValueError("Max job count must be greater than zero.")
        self._max_jobs = count

    def get_max_jobs(self):
        return self._max_jobs

    def is_target_function(self, target_function):
        if type(target_function) is str:
            return target_function in self._target_funcs_by_name
        return target_function in self._target_graph

    def get_target_functions(self):
        return list(self._target_graph.keys())

    def target(self, *args, **kwargs):
        if len(args) == 1 and inspect.isfunction(args[0]):
            self.add_target(args[0])
            return args[0]

        def wrapper(f):
            self.add_target(f, **kwargs)
            return f

        return wrapper

    def get_outputs(self, target_function):
        if type(target_function) is str:
            return self._target_graph[self._target_funcs_by_name[target_function]].outputs
        return self._target_graph[target_function].outputs

    def get_inputs(self, target_function):
        if type(target_function) is str:
            return self._target_graph[self._target_funcs_by_name[target_function]].inputs
        return self._target_graph[target_function].inputs

    def get_dependencies(self, target_function):
        if type(target_function) is str:
            return self._target_graph[self._target_funcs_by_name[target_function]].dependencies
        return self._target_graph[target_function].dependencies

    def add_target(self, target_function, inputs=None, outputs=None, depends=None):
        if not depends: depends = []
        if not inputs: inputs = []
        if not outputs: outputs = []

        if type(depends) is not list:
            depends = [depends]

        if type(inputs) is not list:
            inputs = [inputs]

        if type(outputs) is not list:
            outputs = [outputs]

        if type(outputs) is not list:
            outputs = [outputs]

        if target_function in self._target_graph:
            raise TargetRedefinedException('Target "{target}" already defined.'
                                           .format(target=target_function.__name__))
        else:
            self._target_graph[target_function] = Target(target_function, inputs, outputs, depends)
            self._target_funcs_by_name[target_function.__name__] = target_function
        for dep in depends:
            if dep not in self._target_graph:
                raise UndefinedTargetException('Target "{target}" is not defined.'
                                               .format(target=dep.__name__))

    def _check_target_out_of_date(self, target_function):
        dependencies = self.get_dependencies(target_function)
        inputs = self.get_inputs(target_function)
        outputs = self.get_outputs(target_function)

        if (len(inputs) == 0 or len(outputs) == 0) and len(dependencies) == 0:
            return True

        for o in outputs:
            if not os.path.exists(o):
                return True
            for i in inputs:
                diff = (os.path.getmtime(i) - os.path.getmtime(o))
                if diff > 0.1:
                    return True

        for d in dependencies:
            if d in self._outdated_target_funcs:
                return True

        return False

    def _sort_graph(self):
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
                to_visit.extend([(edge, self._target_graph[edge]) for edge in cur[1].dependencies])
                graph_out.insert(0, (cur[0], cur[1]))
                visited.add(cur[0])

        def get_edges(e): return e.dependencies

        return itertools.chain(((no_deps, []) for no_deps in no_dep_targets),
                               topological_sort(graph_out, get_edges=get_edges))

    def set_run_targets(self, *target_functions):
        if _is_iterable_not_str(target_functions[0]):
            self._run_targets = list(target_functions[0])
        else:
            self._run_targets = list(target_functions)

        for i in range(0, len(self._run_targets)):
            target = self._run_targets[i]
            if type(target) is str:
                if target in self._target_funcs_by_name:
                    self._run_targets[i] = self._target_funcs_by_name[target]
                else:
                    raise UndefinedTargetException('Target "{target}" is not defined.'
                                                   .format(target=target))

    def _run_target_task(self, target_function):
        with self._task_dict_lock:
            for dep_target_func in self.get_dependencies(target_function):
                if dep_target_func in self._task_dict and self._task_dict[dep_target_func].running():
                    self._task_dict[dep_target_func].result()

        sig = inspect.signature(target_function)
        if len(sig.parameters) > 0:
            target_function(self._target_graph[target_function])
        else:
            target_function()

    def _run_target(self, thread_pool, target_function):
        task = thread_pool.submit(self._run_target_task, target_function)
        with self._task_dict_lock:
            self._task_dict[target_function] = task

    def _check_inputs_exist(self):
        for target_function, target in self._target_graph.items():
            for i in target.inputs:
                if not os.path.exists(i):
                    raise TargetInputNotFound('Input file "{file}" in target "{target}" could not be found.'
                                              .format(file=i, target=target_function.__name__))

    def execute(self):
        self._last_run_count = 0
        self._check_inputs_exist()

        with concurrent.futures.ThreadPoolExecutor(max_workers=self._max_jobs) as thread_pool:
            for node in self._sort_graph():
                target_function = node[0]
                if self._check_target_out_of_date(target_function):
                    self._last_run_count += 1
                    self._outdated_target_funcs.add(target_function)
                    self._run_target(thread_pool, target_function)
            self._outdated_target_funcs = set()

        self._task_dict = {}

    def visit(self, visitor=None):
        if not visitor:
            def visitor(target):
                print("Execute Target: " + target.function.__name__)

        self._last_run_count = 0

        self._check_inputs_exist()

        for node in self._sort_graph():
            target_function = node[0]
            if self._check_target_out_of_date(target_function):
                self._last_run_count += 1
                visitor(self._target_graph[target_function])

        self._task_dict = {}

    def clear(self):
        self._target_graph = {}
        self._target_funcs_by_name = {}
        self._run_targets = []