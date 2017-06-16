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
import os.path
import textwrap

import os

import sys

import pake

import pake.arguments
import pake.conf
import pake.util
import pake.returncodes as returncodes
import ast

__all__ = [
    'PakeUninitializedException',
    'run',
    'init',
    'is_init',
    'get_max_jobs',
    'get_subpake_depth',
    'get_init_file',
    'get_init_dir',
    'terminate'
]


class PakeUninitializedException(Exception):
    """
    Thrown if a function is called which depends on :py:func:`pake.init` being called first.
    """

    def __init__(self):
        super().__init__('pake.init() has not been called yet.')


def _defines_to_dict(defines):
    if defines is None:
        return dict()

    result = {}
    for i in defines:
        d = i.split('=', maxsplit=1)

        value_name = d[0]

        try:
            result[value_name.strip()] = True if len(d) == 1 else pake.util.parse_define_value(d[1])
        except ValueError as syn_err:
            raise ValueError(
                'Error parsing define value of "{name}": {message}'
                    .format(name=value_name, message=str(syn_err)))
    return result


_INIT_FILE = None
_INIT_DIR = None


def init(stdout=None, args=None):
    """
    Read command line arguments relevant to initialization, and return a :py:class:`pake.Pake` object.
    
    :param stdout: The stdout object passed to the :py:class:`pake.Pake` instance. (defaults to pake.conf.stdout)
    :param args: Optional command line arguments.
    
    :return: :py:class:`pake.Pake`
    """

    global _INIT_FILE, _INIT_DIR

    parsed_args = pake.arguments.parse_args(args=args)

    pk = pake.Pake(stdout=stdout)

    if parsed_args.stdin_defines: # pragma: no cover
        try:
            parsed_stdin_defines = ast.literal_eval(sys.stdin.read())

            if type(parsed_stdin_defines) != dict:
                print('The --stdin-defines option expects that a python dictionary '
                      'object be written to stdin.  A literal of type {} was '
                      'deserialized instead.'.format(type(parsed_stdin_defines).__name__),
                      file=pake.conf.stderr)

                exit(returncodes.STDIN_DEFINES_SYNTAX_ERROR)

        except Exception as err:

            # This is covered by unit test 'test_stdin_defines.py'
            # Confirmed by debugger, coverage.py is not picking it
            # up in the subprocess though.

            print('Syntax error parsing defines from standard input '''
                  'with --stdin-defines option:' + os.linesep,
                  file=pake.conf.stderr)
            print(str(err), file=pake.conf.stderr)

            exit(returncodes.STDIN_DEFINES_SYNTAX_ERROR)
        else:
            pk.merge_defines_dict(parsed_stdin_defines)

    try:
        parsed_cmd_arg_defines = _defines_to_dict(parsed_args.define)
    except ValueError as err:
        print(str(err), file=pake.conf.stderr)
        exit(returncodes.BAD_DEFINE_VALUE)
    else:
        pk.merge_defines_dict(parsed_cmd_arg_defines)

    # Find the init file by examining the stack

    cur_frame = inspect.currentframe()
    try:
        frame, filename, line_number, function_name, lines, index = inspect.getouterframes(cur_frame)[1]
        _INIT_FILE = os.path.abspath(filename)
    finally:
        del cur_frame

    # Init dir is the current directory, before directory changes

    _INIT_DIR = os.getcwd()

    # Print enter subpake / enter directory if needed

    depth = get_subpake_depth()

    if depth > 0:
        pk.print('*** enter subpake[{}]:'.format(depth))

    if parsed_args.directory and parsed_args.directory != os.getcwd():
        pk.print('pake[{}]: Entering Directory "{}"'.
                 format(get_subpake_depth(), parsed_args.directory))
        os.chdir(parsed_args.directory)

    return pk


def shutdown():
    """
    Return the pake module to a pre-initialized state.
    
    Used primarily for unit tests.
    """

    global _INIT_FILE, _INIT_DIR

    _INIT_FILE = None
    _INIT_DIR = None

    pake.arguments.clear_args()


def is_init():
    """
    Check if :py:meth:`pake.init` has been called.
    
    :return: True if :py:meth:`pake.init` has been called. 
    """
    return _INIT_FILE is not None


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

    return args._subpake_depth


def get_init_file():
    """Gets the full path to the file :py:meth:`pake.init` was called in.
    
    :raises: :py:class:`pake.PakeUninitializedException` if :py:class:`pake.init` has not been called.
    :return: Full path to pakes entrypoint file, or **None** 
    """

    if not is_init():
        raise PakeUninitializedException()

    return _INIT_FILE


def get_init_dir():
    """Gets the full path to the directory pake started running in.
    
    If pake preformed any directory changes, this returns the working path before that happened.
    
    :raises: :py:class:`pake.PakeUninitializedException` if :py:class:`pake.init` has not been called.
    :return: Full path to init dir, or **None**
    """

    if not is_init():
        raise PakeUninitializedException()

    return _INIT_DIR


def _format_task_info(max_name_width, task_name, task_doc):  # pragma: no cover
    field_sep = ':  '

    lines = textwrap.wrap(task_doc)
    lines_len = len(lines)

    if lines_len > 0:
        lines[0] = ' ' * (max_name_width - len(task_name)) + lines[0]

        for i in range(1, lines_len):
            lines[i] = ' ' * (max_name_width + len(field_sep)) + lines[i]

    spacing = (os.linesep if len(lines) > 1 else '')
    return spacing + task_name + field_sep + os.linesep.join(lines) + spacing


def _list_tasks(pake_obj, default_tasks):  # pragma: no cover
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


def _list_task_info(pake_obj, default_tasks):  # pragma: no cover
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


def _validate_parsed_run_arguments(parsed_args):
    """
    Validate command line arguments necessary for pake.run before program execution.

    This function should return a tuple of (True/False, return_code)

    If the first value of the tuple is True, pake.run will return/exit with the given return code.

    If the first value of the tuple if False, pake.run is free to continue executing.

    :param parsed_args: parsed argument object from the argparse module.  See: pake.arguments
    :return: Tuple of (True/False, return_code)
    """

    if parsed_args.show_tasks and parsed_args.show_task_info:
        print('-t/--show-tasks and -ti/--show-task-info cannot be used together.',
              file=pake.conf.stderr)
        return True, returncodes.BAD_ARGUMENTS

    if parsed_args.dry_run:
        if parsed_args.jobs:
            print("-n/--dry-run and -j/--jobs cannot be used together.",
                  file=pake.conf.stderr)
            return True, returncodes.BAD_ARGUMENTS

        if parsed_args.show_tasks:
            print("-n/--dry-run and the -t/--show-tasks option cannot be used together.",
                  file=pake.conf.stderr)
            return True, returncodes.BAD_ARGUMENTS

        if parsed_args.show_task_info:
            print("-n/--dry-run and the -ti/--show-task-info option cannot be used together.",
                  file=pake.conf.stderr)
            return True, returncodes.BAD_ARGUMENTS

    if parsed_args.tasks and len(parsed_args.tasks) > 0:
        if parsed_args.show_tasks:
            print("Run tasks may not be specified when using the -t/--show-tasks option.",
                  file=pake.conf.stderr)
            return True, returncodes.BAD_ARGUMENTS

        if parsed_args.show_task_info:
            print("Run tasks may not be specified when using the -ti/--show-task-info option.",
                  file=pake.conf.stderr)
            return True, returncodes.BAD_ARGUMENTS

    if parsed_args.jobs:
        if parsed_args.show_tasks:
            print('-t/--show-tasks and -j/--jobs cannot be used together.',
                  file=pake.conf.stderr)
            return True, returncodes.BAD_ARGUMENTS

        if parsed_args.show_task_info:
            print('-ti/--show-task-info and -j/--jobs cannot be used together.',
                  file=pake.conf.stderr)
            return True, returncodes.BAD_ARGUMENTS

    return False, 0


def run(pake_obj, tasks=None, jobs=None, call_exit=True):
    """
    Run pake (the program) given a :py:class:`pake.Pake` instance and options default tasks.
    
    This function will call **exit(return_code)** upon handling any exceptions from :py:meth:`pake.Pake.run`
    or :py:meth:`pake.Pake.dry_run` (if **call_exit** is **True**), and print information to :py:attr:`pake.Pake.stderr` if
    necessary.
    
    For all return codes see: :py:mod:`pake.returncodes`
    
    :raises: :py:class:`pake.PakeUninitializedException` if :py:class:`pake.init` has not been called.
    :raises: :py:class:`ValueError` if the **jobs** parameter is used, and is set less than 1.

    :param pake_obj: A :py:class:`pake.Pake` instance, usually created by :py:func:`pake.init`.
    :param tasks: A list of, or a single default task to run if no tasks are specified on the command line.
    :param jobs: Call with an arbitrary number of max jobs, overriding the command line value of **--jobs**.
                 The default value of this parameter is **None**, which means the command line value or default of 1 is not overridden.

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
        if call_exit and code != returncodes.SUCCESS:  # pragma: no cover
            exit(code)
        return code

    should_return, return_code = \
        _validate_parsed_run_arguments(parsed_args)

    if should_return:
        return m_exit(return_code)

    if pake_obj.task_count == 0:
        print('*** No Tasks.  Stop.',
              file=pake.conf.stderr)
        return m_exit(returncodes.NO_TASKS_DEFINED)

    if parsed_args.show_tasks:  # pragma: no cover
        _list_tasks(pake_obj, tasks)
        return m_exit(returncodes.SUCCESS)

    if parsed_args.show_task_info:  # pragma: no cover
        _list_task_info(pake_obj, tasks)
        return m_exit(returncodes.SUCCESS)

    run_tasks = []
    if parsed_args.tasks:
        run_tasks += parsed_args.tasks
    elif len(tasks):
        run_tasks += tasks
    else:
        pake_obj.print("No tasks specified.")
        return m_exit(returncodes.NO_TASKS_SPECIFIED)

    if parsed_args.directory and os.getcwd() != parsed_args.directory:
        # Quietly enforce directory change before running any tasks,
        # incase the current directory was changed after init was called.
        os.chdir(parsed_args.directory)

    if parsed_args.dry_run:
        try:
            pake_obj.dry_run(run_tasks)
            if pake_obj.run_count == 0:
                pake_obj.print('Nothing to do, all tasks up to date.')
            return 0
        except pake.InputNotFoundException as err:
            print(str(err), file=pake.conf.stderr)
            return m_exit(returncodes.TASK_INPUT_NOT_FOUND)
        except pake.MissingOutputsException as err:
            print(str(err), file=pake.conf.stderr)
            return m_exit(returncodes.TASK_OUTPUT_MISSING)
        except pake.UndefinedTaskException as err:
            print(str(err), file=pake.conf.stderr)
            return m_exit(returncodes.UNDEFINED_TASK)
        except pake.CyclicGraphException as err:
            print(str(err), file=pake.conf.stderr)
            return m_exit(returncodes.CYCLIC_DEPENDENCY)

    return_code = 0

    if jobs is None:
        max_jobs = 1 if parsed_args.jobs is None else parsed_args.jobs
    elif jobs < 1:
        raise ValueError('jobs parameter may not be less than 1.')
    else:
        max_jobs = jobs

    try:
        pake_obj.run(jobs=max_jobs, tasks=run_tasks)

        if pake_obj.run_count == 0:
            pake_obj.print('Nothing to do, all tasks up to date.')

    except pake.TaskExitException as err:
        return_code = err.return_code

        # Sneaky trick to figure out if someone did not read the documentation.
        # _TerminateException derives SystemExit which triggers TaskExitException inside a task.
        # we can detect if the exit originated from pake.terminate here because that is the exception
        # pake.terminate raises to kill the interpreter.  pake.terminate should not be called
        # inside of a task because it writes to unsynchronized process output, among other reasons.

        if isinstance(err.exit_exception, _TerminateException):  # pragma: no cover
            pake.conf.stderr.write(os.linesep)
            print('pake.terminate(..., {code}) was used inside task "{task}", do not do this!  '
                  'Just use plain a exit() call instead.  '
                  'See "pake.terminate" and "pake.Pake.terminate" documentation for more information '
                  'on where these functions should and should not be used.'
                  .format(code=err.return_code, task=err.task_name),
                  file=pake.conf.stderr)
            pake.conf.stderr.write(os.linesep)
            err.print_traceback(file=pake.conf.stderr)
            pake.conf.stderr.write(os.linesep)

        elif return_code != returncodes.SUCCESS:
            # Print info only for error conditions
            print(os.linesep + str(err) + os.linesep, file=pake.conf.stderr)
            err.print_traceback(file=pake.conf.stderr)
            pake.conf.stderr.write(os.linesep)

    except pake.InputNotFoundException as err:
        print(str(err), file=pake.conf.stderr)
        return_code = returncodes.TASK_INPUT_NOT_FOUND
    except pake.MissingOutputsException as err:
        print(str(err), file=pake.conf.stderr)
        return_code = returncodes.TASK_OUTPUT_MISSING
    except pake.UndefinedTaskException as err:
        print(str(err), file=pake.conf.stderr)
        return_code = returncodes.UNDEFINED_TASK
    except pake.CyclicGraphException as err:
        print(str(err), file=pake.conf.stderr)
        return_code = returncodes.CYCLIC_DEPENDENCY
    except pake.TaskException as err:
        inner_err = err.exception

        if isinstance(inner_err, pake.SubpakeException):
            pake.conf.stderr.write(os.linesep)
            inner_err.write_info(file=pake.conf.stderr)
            pake.conf.stderr.write(os.linesep)

            return_code = returncodes.SUBPAKE_EXCEPTION

        elif isinstance(inner_err, pake.SubprocessException):
            pake.conf.stderr.write(os.linesep)
            inner_err.write_info(file=pake.conf.stderr)
            pake.conf.stderr.write(os.linesep)

            return_code = returncodes.TASK_SUBPROCESS_EXCEPTION

        else:
            print(os.linesep + str(err) + os.linesep, file=pake.conf.stderr)
            err.print_traceback(file=pake.conf.stderr)
            pake.conf.stderr.write(os.linesep)

            return_code = returncodes.TASK_EXCEPTION

    return _terminate(pake_obj, return_code, exit_func=m_exit)


class _TerminateException(SystemExit):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)  # pragma: no cover


def terminate(pake_obj, return_code=returncodes.SUCCESS):  # pragma: no cover
    """
    Preform a graceful exit from a pakefile outside of a task, printing the leaving directory or exit subpake message if
    needed, then exiting with a given return code.  The default return code is :py:attr:`pake.returncodes.SUCCESS`.

    This should be used as opposed to a raw **exit** call outside of pake tasks to ensure the output of pake remains consistent.
    
    Do not use this function from inside of a task, just use a plain **exit** call.  An **exit** call inside of a task will cause
    pake to stop as soon as it can and return with the given exit code.  Pake can handle getting the 'leaving directory/exiting subpake'
    output correct when plain **exit** is called inside a task; so you do not need to use this function inside tasks.
    
    Using this function inside a task will cause the 'leaving directory/exiting subpake' messages to be printed twice, and also
    in a possibly random location in your build output if your running pake with multiple jobs.
    
    :py:meth:`pake.terminate` or :py:meth:`pake.Pake.terminate` should be used to exit the pakefile before tasks have run, if it is necessary.
    
    Use Case:
    
    .. code-block:: python
    
       import os
       import pake
       from pake import returncodes
    
       pk = pake.init()
    
       # Say you need to wimp out of a build for some reason
       # But not inside of a task.
    
       if os.name == 'nt':
           pk.print('You really thought you could '
                    'build my software on windows? nope!')
    
           pake.terminate(pk, returncodes.ERROR)
    
           # or
    
           # pk.terminate(returncodes.ERROR)
           
           
       # Define some tasks...
       
       @pk.task
       def build(ctx):
           pass
        
       pake.run(pk, tasks=build)
           

    :py:meth:`pake.Pake.terminate` is a shorthand which passes the **pake_obj** instance to this function for you.

    :param pake_obj: Reference to the initialized pake object, for message io.

    :param return_code: Return code to exit the pakefile with, see :py:mod:`pake.returncodes` for standard return codes.
                        Defaults to :py:attr:`pake.returncodes.SUCCESS`.  :py:attr:`pake.returncodes.ERROR` is intended
                        to be used with **terminate** to indicate a generic error, but other return codes may be used.

    :raises: :py:class:`pake.PakeUninitializedException` if :py:class:`pake.init` has not been called.
    """

    def m_exit(code):
        raise _TerminateException(code)

    _terminate(pake_obj, return_code, exit_func=m_exit)


def _terminate(pake_obj, return_code, exit_func=exit):
    if not is_init():
        raise pake.PakeUninitializedException()

    parsed_args = pake.arguments.get_args()

    depth = get_subpake_depth()

    if pake.get_init_dir() != os.getcwd():
        pake_obj.print('pake[{}]: Exiting Directory "{}"'.
                       format(depth, parsed_args.directory))
        os.chdir(pake.get_init_dir())

    if depth > 0:
        pake_obj.print('*** exit subpake[{}]:'.format(depth))

    return exit_func(return_code)
