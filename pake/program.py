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

import argparse
import ast
import inspect
import os.path
import textwrap

import os
import pake

from pake.util import is_iterable, is_iterable_not_str, get_task_arg_name
from .pake import Pake


class PakeUninitializedException(Exception):
    """
    Thrown if :py:func:`pake.run` is called without first calling :py:func:`pake.init`
    """

    def __init__(self):
        super(PakeUninitializedException, self).__init__('pake.init() has not been called yet.')


_arg_parser = argparse.ArgumentParser(prog='pake')


def _create_gt_int(less_message):
    def _gt_zero_int(val):
        val = int(val)
        if val < 1:
            _arg_parser.error(less_message)
        return val

    return _gt_zero_int


_arg_parser.add_argument('-v', '--version', action='version', version='pake ' + pake.__version__)

_arg_parser.add_argument('tasks', type=str, nargs='*', help='Build tasks.')

_arg_parser.add_argument('-D', '--define', action='append', help='Add defined value.')

_arg_parser.add_argument('-j', '--jobs', default=1, type=_create_gt_int('--jobs must be greater than one.'),
                         help='Max number of parallel jobs.  Using this option '
                              'enables unrelated tasks to run in parallel with a '
                              'max of N tasks running at a time.')

_arg_parser.add_argument('--s_depth', default=0, type=int, help=argparse.SUPPRESS)

_arg_parser.add_argument('-n', '--dry-run', action='store_true', dest='dry_run',
                         help='Use to preform a dry run, lists all tasks that '
                              'will be executed in the next actual invocation.')

_arg_parser.add_argument('-C', '--directory', help='Change directory before executing.')

_arg_parser.add_argument('-t', '--show-tasks', action='store_true', dest='show_tasks',
                         help='List all task names.')

_arg_parser.add_argument('-ti', '--show-task-info', action='store_true', dest='show_task_info',
                         help='List all tasks along side their doc string.'
                              'Only tasks with doc strings present will be shown')

_parsed_args = None
_init_file_name = None


def get_max_jobs():
    """
    Get the max number of jobs passed from the --jobs command line argument.
    
    The minimum number of jobs allowed is 1.
    
    :raises: :py:class:`pake.PakeUninitializedException` if :py:class:`pake.init` has not been called.
    :return: The max number of jobs from the --jobs command line argument. (an integer >= 1)
    """
    if _parsed_args is None:
        raise PakeUninitializedException()
    return _parsed_args.jobs


def get_subpake_depth():
    """
    Get the depth of execution, which increases for nested calls to :py:func:`pake.subpake`
    
    The depth of execution starts at 0.
    
    :raises: :py:class:`pake.PakeUninitializedException` if :py:class:`pake.init` has not been called.
    :return: The current depth of execution (an integer >= 0)
    """
    if _parsed_args is None:
        raise PakeUninitializedException()

    if hasattr(_parsed_args, 's_depth'):
        return _parsed_args.s_depth
    else:
        return 0


def _coerce_define_value(value_name, value):
    literal_eval_triggers = {"'", '"', "(", "{", "["}

    if pake.util.str_is_int(value):
        return int(value)
    elif pake.util.str_is_float(value):
        return float(value)
    else:
        ls = value.lstrip()
        if len(ls) > 0:
            if ls[0] in literal_eval_triggers:
                try:
                    return ast.literal_eval(ls)
                except SyntaxError as syn_err:
                    raise RuntimeError(
                        'Error parsing define value of "{name}": {message}'
                            .format(name=value_name, message=str(syn_err)))
        else:
            return ''

        lower = ls.rstrip().lower()
        if lower == 'false':
            return False
        if lower == 'true':
            return True
    return value


def _defines_to_dict(defines):
    if defines is None: return dict()

    result = {}
    for i in defines:
        d = i.split('=', maxsplit=1)
        result[d[0].strip()] = True if len(d) == 1 else _coerce_define_value(d[0], d[1])
    return result


def init(stdout=None, stderr=None):
    """
    Read command line arguments relevant to initialization, and return a :py:class:`pake.Pake` object.
    
    :param stdout: The stdout object passed to the :py:class:`pake.Pake` instance. (defaults to sys.stdout)
    :param stderr: The stderr object passed to the :py:class:`pake.Pake` instance. (defaults to sys.stderr)
    
    :return: :py:class:`pake.Pake`
    """

    global _parsed_args, _init_file_name

    frame = inspect.stack()[1]
    module_obj = inspect.getmodule(frame[0])
    _init_file_name = os.path.abspath(module_obj.__file__)

    p = Pake(stdout=stdout, stderr=stderr)

    _parsed_args = _arg_parser.parse_args()

    p.set_defines_dict(_defines_to_dict(_parsed_args.define))

    return p


def _format_task_info(max_name_width, task_name, task_doc):
    field_sep = ':  '

    lines = textwrap.wrap(task_doc)

    if len(lines):
        lines[0] = ' ' * (max_name_width - len(task_name)) + lines[0]

    for i in range(1, len(lines)):
        lines[i] = ' ' * (max_name_width + len(field_sep)) + lines[i]

    spacing = (os.linesep if len(lines) > 1 else '')
    return spacing + task_name + field_sep + os.linesep.join(lines) + spacing


def _list_tasks(pake_obj, default_tasks):
    if len(default_tasks):
        pake_obj.print('# Default Tasks' + os.linesep)
        for task in default_tasks:
            pake_obj.print(get_task_arg_name(task))
        pake_obj.stdout.write(os.linesep)
        pake_obj.stdout.flush()

    pake_obj.print('# All Tasks' + os.linesep)

    if len(pake_obj.task_contexts):
        for ctx in pake_obj.task_contexts:
            pake_obj.print(ctx.name)
    else:
        pake_obj.print('Not tasks present.')


def _list_task_info(pake_obj, default_tasks):
    if len(default_tasks):
        pake_obj.print('# Default Tasks' + os.linesep)
        for task in default_tasks:
            pake_obj.print(get_task_arg_name(task))
        pake_obj.stdout.write(os.linesep)
        pake_obj.stdout.flush()

    documented = [ctx for ctx in pake_obj.task_contexts if ctx.func.__doc__ is not None]

    pake_obj.print('# Documented Tasks' + os.linesep)

    if len(documented):
        max_name_width = len(max(documented, key=lambda x: len(x.name)).name)

        for ctx in documented:
            pake_obj.print(_format_task_info(
                               max_name_width,
                               ctx.name,
                               ctx.func.__doc__))
    else:
        pake_obj.print('No documented tasks present.')


def run(pake_obj, tasks=None):
    """
    Run pake (the program) given a :py:class:`pake.Pake` instance and options default tasks.
    
    This function will call exit(return_code) upon non exception related errors.
    
    :raises: :py:class:`pake.PakeUninitializedException` if :py:class:`pake.init` has not been called.
    :param pake_obj: A :py:class:`pake.Pake` instance, usually created by :py:func:`pake.init`.
    :param tasks: A list of, or a single default task to run if no tasks are specified on the command line.
    """

    if not is_iterable_not_str(tasks):
        tasks = [tasks]

    if _parsed_args is None:
        raise PakeUninitializedException()

    if _parsed_args.show_tasks and _parsed_args.show_task_info:
        pake_obj.print('-t/--show-tasks and -ti/--show-task-info cannot be used together.')
        return

    if _parsed_args.show_tasks:
        _list_tasks(pake_obj, tasks)
        return

    if _parsed_args.show_task_info:
        _list_task_info(pake_obj, tasks)
        return

    run_tasks = []
    if _parsed_args.tasks:
        run_tasks += _parsed_args.tasks
    elif tasks:
        run_tasks += tasks
    else:
        pake_obj.print("No tasks specified.")
        return

    if _parsed_args.dry_run:
        pake_obj.dry_run(run_tasks)
        return

    depth = get_subpake_depth()

    if depth > 0:
        pake_obj.print('*** enter subpake[{}]:'.format(depth))

    exit_dir = None
    if _parsed_args.directory:
        exit_dir = os.getcwd()

        pake_obj.print('pake[{}]: Entering Directory "{}"'.
                       format(depth, _parsed_args.directory))

        os.chdir(_parsed_args.directory)

    return_code = 0
    try:
        pake_obj.run(jobs=_parsed_args.jobs, tasks=run_tasks)
    except pake.UndefinedTaskException as err:
        pake_obj.print_err(str(err))
        return_code = 1
    except FileNotFoundError as err:
        pake_obj.print_err(str(err))
        return_code = 1

    if exit_dir:
        pake_obj.print('pake[{}]: Exiting Directory "{}"'.
                       format(depth, _parsed_args.directory))

    if depth > 0:
        pake_obj.print('*** exit subpake[{}]:'.format(depth))

    if return_code != 0:
        exit(return_code)
