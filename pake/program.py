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

import ast
import inspect
import os.path
import textwrap

import os
import pake
import sys

import pake.arguments
import pake.conf
import pake.util

__all__ = [
    'PakeUninitializedException',
    'run',
    'init',
    'is_init',
    'get_max_jobs',
    'get_subpake_depth',
    'get_init_file',
    'get_init_dir'
]


class PakeUninitializedException(Exception):
    """
    Thrown if a function is called which depends on :py:func:`pake.init` being called first.
    """

    def __init__(self):
        super(PakeUninitializedException, self).__init__('pake.init() has not been called yet.')


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


_init_file = None
_init_dir = None


def init(stdout=None, args=None):
    """
    Read command line arguments relevant to initialization, and return a :py:class:`pake.Pake` object.
    
    :param stdout: The stdout object passed to the :py:class:`pake.Pake` instance. (defaults to pake.conf.stdout)
    :param args: Optional command line arguments.
    
    :return: :py:class:`pake.Pake`
    """

    global _init_file, _init_dir

    _init_dir = os.getcwd()

    pk = pake.Pake(stdout=stdout)

    parsed_args = pake.arguments.parse_args(args=args)

    pk.set_defines_dict(_defines_to_dict(parsed_args.define))

    cur_frame = inspect.currentframe()
    try:
        frame, filename, line_number, function_name, lines, index = inspect.getouterframes(cur_frame)[1]
        _init_file = os.path.abspath(filename)
    finally:
        del cur_frame

    return pk


def shutdown():
    """
    Return the pake module to a pre-initialized state.
    
    Used primarily for unit tests.
    """

    global _init_file, _init_dir

    _init_file = None
    _init_dir = None

    pake.arguments.clear_args()


def is_init():
    """
    Check if :py:meth:`pake.init` has been called.
    
    :return: True if :py:meth:`pake.init` has been called. 
    """
    return _init_file is not None


def get_max_jobs():
    """
    Get the max number of jobs passed from the --jobs command line argument.
    
    The minimum number of jobs allowed is 1.
    
    :raises: :py:class:`pake.PakeUninitializedException` if :py:class:`pake.init` has not been called.
    :return: The max number of jobs from the --jobs command line argument. (an integer >= 1)
    """

    if not is_init():
        raise PakeUninitializedException()

    jobs = pake.arguments.get_args().jobs
    if jobs is None:
        return 1
    else:
        return jobs


def get_subpake_depth():
    """
    Get the depth of execution, which increases for nested calls to :py:func:`pake.subpake`
    
    The depth of execution starts at 0.
    
    :raises: :py:class:`pake.PakeUninitializedException` if :py:class:`pake.init` has not been called.
    :return: The current depth of execution (an integer >= 0)
    """

    if not is_init():
        raise PakeUninitializedException()

    args = pake.arguments.get_args()

    if hasattr(args, 's_depth'):
        return args.s_depth
    else:
        return 0


def get_init_file():
    """Gets the full path to the file :py:meth:`pake.init` was called in.
    
    :raises: :py:class:`pake.PakeUninitializedException` if :py:class:`pake.init` has not been called.
    :return: Full path to pakes entrypoint file, or **None** 
    """

    if not is_init():
        raise PakeUninitializedException()

    return _init_file


def get_init_dir():
    """Gets the full path to the directory pake started running in.
    
    If pake preformed any directory changes, this returns the working path before that happened.
    
    :raises: :py:class:`pake.PakeUninitializedException` if :py:class:`pake.init` has not been called.
    :return: Full path to init dir, or **None**
    """

    if not is_init():
        raise PakeUninitializedException()

    return _init_dir


def _format_task_info(max_name_width, task_name, task_doc):
    field_sep = ':  '

    lines = textwrap.wrap(task_doc)
    lines_len = len(lines)

    if lines_len > 0:
        lines[0] = ' ' * (max_name_width - len(task_name)) + lines[0]

        for i in range(1, lines_len):
            lines[i] = ' ' * (max_name_width + len(field_sep)) + lines[i]

    spacing = (os.linesep if len(lines) > 1 else '')
    return spacing + task_name + field_sep + os.linesep.join(lines) + spacing


def _list_tasks(pake_obj, default_tasks):
    if len(default_tasks):
        pake_obj.print('# Default Tasks' + os.linesep)
        for task in default_tasks:
            pake_obj.print(pake_obj.get_task_name(task))
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
            pake_obj.print(pake_obj.get_task_name(task))
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


def run(pake_obj, tasks=None, call_exit=True):
    """
    Run pake (the program) given a :py:class:`pake.Pake` instance and options default tasks.
    
    This function will call **exit(return_code)** upon handling any exceptions from :py:meth:`pake.Pake.run`
    or :py:meth:`pake.Pake.dry_run` (if **call_exit** is **True**), and print information to :py:attr:`pake.Pake.stderr` if
    necessary.
    
    Return Codes:
    
    3. Invalid parameter combination.
    4. No tasks defined.
    5. No tasks specified.
    6. Task input file not found.
    7. Task defines input files with no output files.
    8. Reference made to an undefined task.
    9. Cyclic dependency detected.
    10. Unhandled exception inside of task.
    
    :raises: :py:class:`pake.PakeUninitializedException` if :py:class:`pake.init` has not been called.
    :param pake_obj: A :py:class:`pake.Pake` instance, usually created by :py:func:`pake.init`.
    :param tasks: A list of, or a single default task to run if no tasks are specified on the command line.
    :param call_exit: Whether or not **exit(return_code)** should be called by this function on error.
                      This defaults to **True**, when set to **False** the return code is instead returned
                      to the caller.
    """

    if not is_init():
        raise pake.PakeUninitializedException()

    if pake_obj is None:
        raise ValueError('Pake instance (pake_obj parameter) was None.')

    if tasks and not pake.util.is_iterable_not_str(tasks):
        tasks = [tasks]

    if tasks is None:
        tasks = []

    parsed_args = pake.arguments.get_args()

    def m_exit(code):
        if call_exit:
            exit(code)
        return code

    if parsed_args.show_tasks and parsed_args.show_task_info:
        print('-t/--show-tasks and -ti/--show-task-info cannot be used together.',
              file=pake.conf.stderr)
        return m_exit(3)

    if parsed_args.dry_run:
        if parsed_args.jobs:
            print("-n/--dry-run and -j/--jobs cannot be used together.",
                  file=pake.conf.stderr)
            return m_exit(3)

        if parsed_args.show_tasks:
            print("-n/--dry-run and the -t/--show-tasks option cannot be used together.",
                  file=pake.conf.stderr)
            return m_exit(3)

        if parsed_args.show_task_info:
            print("-n/--dry-run and the -ti/--show-task-info option cannot be used together.",
                  file=pake.conf.stderr)
            return m_exit(3)

    if parsed_args.tasks and len(parsed_args.tasks) > 0:
        if parsed_args.show_tasks:
            print("Run tasks may not be specified when using the -t/--show-tasks option.",
                  file=pake.conf.stderr)
            return m_exit(3)

        if parsed_args.show_task_info:
            print("Run tasks may not be specified when using the -ti/--show-task-info option.",
                  file=pake.conf.stderr)
            return m_exit(3)

    if parsed_args.jobs:
        if parsed_args.show_tasks:
            print('-t/--show-tasks and -j/--jobs cannot be used together.',
                  file=pake.conf.stderr)
            return m_exit(3)

        if parsed_args.show_task_info:
            print('-ti/--show-task-info and -j/--jobs cannot be used together.',
                  file=pake.conf.stderr)
            return m_exit(3)

    if pake_obj.task_count == 0:
        print('*** No Tasks.  Stop.',
              file=pake.conf.stderr)
        return m_exit(4)

    if parsed_args.show_tasks:
        _list_tasks(pake_obj, tasks)
        return 0

    if parsed_args.show_task_info:
        _list_task_info(pake_obj, tasks)
        return 0

    run_tasks = []
    if parsed_args.tasks:
        run_tasks += parsed_args.tasks
    elif len(tasks):
        run_tasks += tasks
    else:
        pake_obj.print("No tasks specified.")
        return m_exit(5)

    if parsed_args.dry_run:
        try:
            pake_obj.dry_run(run_tasks)
            if pake_obj.run_count == 0:
                pake_obj.print('Nothing to do, all tasks up to date.')
            return 0
        except pake.InputFileNotFoundException as err:
            print(str(err), file=pake.conf.stderr)
            return m_exit(6)
        except pake.MissingOutputFilesException as err:
            print(str(err), file=pake.conf.stderr)
            return m_exit(7)
        except pake.UndefinedTaskException as err:
            print(str(err), file=pake.conf.stderr)
            return m_exit(8)
        except pake.CyclicGraphException as err:
            print(str(err), file=pake.conf.stderr)
            return m_exit(9)

    depth = get_subpake_depth()

    if depth > 0:
        pake_obj.print('*** enter subpake[{}]:'.format(depth))

    exit_dir = None
    if parsed_args.directory:
        exit_dir = os.getcwd()

        pake_obj.print('pake[{}]: Entering Directory "{}"'.
                       format(depth, parsed_args.directory))

        os.chdir(parsed_args.directory)

    return_code = 0
    jobs = 1 if parsed_args.jobs is None else parsed_args.jobs

    try:
        pake_obj.run(jobs=jobs, tasks=run_tasks)

        if pake_obj.run_count == 0:
            pake_obj.print('Nothing to do, all tasks up to date.')

    except pake.InputFileNotFoundException as err:
        print(str(err), file=pake.conf.stderr)
        return_code = 6
    except pake.MissingOutputFilesException as err:
        print(str(err), file=pake.conf.stderr)
        return_code = 7
    except pake.UndefinedTaskException as err:
        print(str(err), file=pake.conf.stderr)
        return_code = 8
    except pake.CyclicGraphException as err:
        print(str(err), file=pake.conf.stderr)
        return_code = 9
    except pake.TaskException:
        # Information has already been printed to Pake.stderr
        return_code = 10

    if exit_dir:
        pake_obj.print('pake[{}]: Exiting Directory "{}"'.
                       format(depth, parsed_args.directory))

    if depth > 0:
        pake_obj.print('*** exit subpake[{}]:'.format(depth))

    if return_code != 0:
        return m_exit(return_code)

    return 0
