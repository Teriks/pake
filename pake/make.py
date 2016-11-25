from pake.topologicalsort import topological_sort
import inspect
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
                raise UndefinedTargetException('Target "{target}" not defined.'
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
        visited, dummy_targets, graph_out, to_visit = set(), set(), [], []

        for target_function in self._run_targets:
            target = self._target_graph[target_function]
            dependencies = self._target_graph[target_function].dependencies
            if len(dependencies) == 0:
                if target_function not in dummy_targets:
                    dummy_targets.add(target_function)
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

        return itertools.chain(((dummy, []) for dummy in dummy_targets), topological_sort(graph_out, get_edges=get_edges))

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
                    raise UndefinedTargetException("Target {target} not defined."
                                                   .format(target=target))

    def _run_target_task(self, target_function):
        with self._task_dict_lock:
            for i in self.get_dependencies(target_function):
                if i in self._task_dict and self._task_dict[i].running():
                    self._task_dict[i].result()

        sig = inspect.signature(target_function)
        if len(sig.parameters) > 0:
            target_function(self._target_graph[target_function])
        else:
            target_function()

    def _run_target(self, thread_pool, target_function):
        task = thread_pool.submit(self._run_target_task, target_function)
        with self._task_dict_lock:
            self._task_dict[target_function] = task

    def _visit_target(self, thread_pool, target_function, visitor):
        task = thread_pool.submit(visitor, self._target_graph[target_function])
        with self._task_dict_lock:
            self._task_dict[target_function] = task

    def _check_inputs_exist(self):
        for target_function, target in self._target_graph.items():
            for i in target.inputs:
                if not os.path.exists(i):
                    raise TargetInputNotFound('Input file "{file}" in target "{target}" could not be found.'
                                              .format(file=i, target=target_function.__name__))

    def execute(self):
        self._check_inputs_exist()

        with concurrent.futures.ThreadPoolExecutor(max_workers=self._max_jobs) as thread_pool:
            sorted_graph = self._sort_graph()
            for i in sorted_graph:
                target_function = i[0]
                if self._check_target_out_of_date(target_function):
                    self._outdated_target_funcs.add(target_function)
                    self._run_target(thread_pool, target_function)
            self._outdated_target_funcs = set()

        self._task_dict = {}

    def visit(self, visitor=None):
        if not visitor:
            def visitor(target):
                print("Target: " + target.function.__name__)

        self._check_inputs_exist()

        with concurrent.futures.ThreadPoolExecutor(max_workers=self._max_jobs) as thread_pool:
            sorted_graph = self._sort_graph()
            for i in sorted_graph:
                target_function = i[0]
                if self._check_target_out_of_date(target_function):
                    self._outdated_target_funcs.add(target_function)
                    self._visit_target(thread_pool, target_function, visitor)
            self._outdated_target_funcs = set()

        self._task_dict = {}

    def clear(self):
        self._target_graph = {}
        self._target_funcs_by_name = {}
        self._run_targets = []