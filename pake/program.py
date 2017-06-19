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
import textwrap
import os.path
import os
import sys
import pake
import pake.arguments
import pake.conf
import pake.pake
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
    'terminate',
    'TerminateException',
    'de_init'
]


def _print_err(*args):
    print(*args, file=pake.conf.stderr)


def _print(*args):
    print(*args, file=pake.conf.stdout)


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

    This function will print information to :py:attr:`pake.conf.stderr` and call ``exit(pake.returncodes.BAD_ARGUMENTS)``
    immediately if arguments parsed from the command line or passed to the **args** parameter do not pass validation.
    
    :param stdout: The file object that task output gets written to, as well as 'changing directory/entering & leaving subpake' messages.
                   The default value is :py:attr:`pake.conf.stdout`.

    :param args: Optional command line arguments, if not provided they will be parsed from the command line.

    :raises: :py:exc:`SystemExit` if bad command line arguments are parsed, or the **args** parameter contains bad arguments.

    :return: :py:class:`pake.Pake`
    """

    global _INIT_FILE, _INIT_DIR

    parsed_args = pake.arguments.parse_args(args=args)

    pk = pake.Pake(stdout=stdout)

    if parsed_args.stdin_defines:  # pragma: no cover

        # This is all covered by unit test 'test_stdin_defines.py'
        # Confirmed by debugger, coverage.py is not picking it
        # up though.

        try:
            parsed_stdin_defines = ast.literal_eval(sys.stdin.read())

            if type(parsed_stdin_defines) != dict:
                _print_err('The --stdin-defines option expects that a python dictionary '
                           'object be written to stdin.  A literal of type "{}" was '
                           'deserialized instead.'.format(type(parsed_stdin_defines).__name__))

                exit(returncodes.STDIN_DEFINES_SYNTAX_ERROR)

        except Exception as err:

            _print_err('Syntax error parsing defines from standard input '''
                       'with --stdin-defines option:' + os.linesep)
            _print_err(err)

            exit(returncodes.STDIN_DEFINES_SYNTAX_ERROR)
        else:
            pk.merge_defines_dict(parsed_stdin_defines)

    try:
        parsed_cmd_arg_defines = _defines_to_dict(parsed_args.define)
    except ValueError as err:
        _print_err(err)
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


def de_init(
        clear_conf=True,
        clear_exports=True):
    """
    Return the pake module to a pre-initialized state.
    
    Used primarily for unit tests.

    :param clear_conf: If **True**, call :py:meth:`pake.conf.reset`
    :param clear_exports: If **True**, call **clear** on :py:attr:`pake.EXPORTS`
    """

    global _INIT_FILE, _INIT_DIR

    _INIT_FILE = None
    _INIT_DIR = None

    pake.arguments.clear_args()

    if clear_exports:
        pake.EXPORTS.clear()

    if clear_conf:
        pake.conf.reset()


def is_init():
    """
    Check if :py:meth:`pake.init` has been called.
    
    :return: True if :py:meth:`pake.init` has been called. 
    """
    return _INIT_FILE is not None


def get_max_jobs():
    """
    Get the max number of jobs passed from the **--jobs** command line argument.
    
    The minimum number of jobs allowed is 1.

    Be aware, the value this function returns will not be affected by the optional
    **jobs** argument of :py:meth:`pake.run` and :py:meth:`pake.Pake.run`.  It is purely
    for retrieving the value passed on the command line.
    
    :raises: :py:exc:`pake.PakeUninitializedException` if :py:class:`pake.init` has not been called.
    :return: The max number of jobs from the **--jobs** command line argument. (an integer >= 1)
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
    
    :raises: :py:exc:`pake.PakeUninitializedException` if :py:class:`pake.init` has not been called.
    :return: The current depth of execution (an integer >= 0)
    """

    if not is_init():
        raise PakeUninitializedException()

    args = pake.arguments.get_args()

    return args.subpake_depth


def get_init_file():
    """Gets the full path to the file :py:meth:`pake.init` was called in.
    
    :raises: :py:exc:`pake.PakeUninitializedException` if :py:class:`pake.init` has not been called.
    :return: Full path to pakes entrypoint file, or **None** 
    """

    if not is_init():
        raise PakeUninitializedException()

    return _INIT_FILE


def get_init_dir():
    """Gets the full path to the directory pake started running in.
    
    If pake preformed any directory changes, this returns the working path before that happened.
    
    :raises: :py:exc:`pake.PakeUninitializedException` if :py:class:`pake.init` has not been called.
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
    """

    :type pake_obj: pake.Pake
    """
    if len(default_tasks):
        _print('# Default Tasks' + os.linesep)
        for task in default_tasks:
            _print(pake_obj.get_task_name(task))
        pake.conf.stdout.write(os.linesep)
        pake.conf.stdout.flush()

    _print('# All Tasks' + os.linesep)

    if len(pake_obj.task_contexts):
        for ctx in pake_obj.task_contexts:
            _print(ctx.name)
    else:
        _print('No tasks present.')


def _list_task_info(pake_obj, default_tasks):  # pragma: no cover
    """

    :type pake_obj: pake.Pake
    """
    if len(default_tasks):
        _print('# Default Tasks' + os.linesep)
        for task in default_tasks:
            _print(pake_obj.get_task_name(task))
        pake.conf.stdout.write(os.linesep)
        pake.conf.stdout.flush()

    documented = [ctx for ctx in pake_obj.task_contexts if ctx.func.__doc__ is not None]

    _print('# Documented Tasks' + os.linesep)

    if len(documented):
        max_name_width = len(max(documented, key=lambda x: len(x.name)).name)

        for ctx in documented:
            _print(_format_task_info(
                   max_name_width,
                   ctx.name,
                   ctx.func.__doc__))
    else:
        _print('No documented tasks present.')


def run(pake_obj, tasks=None, jobs=None, call_exit=True):
    """
    Run pake *(the program)* given a :py:class:`pake.Pake` instance and default tasks.

    This function should be used to invoke pake at the end of your pakefile.
    
    This function will call **exit(return_code)** upon handling any exceptions from :py:meth:`pake.Pake.run`
    or :py:meth:`pake.Pake.dry_run` if **call_exit=True**, and will print information to
    :py:attr:`pake.Pake.stderr` if necessary.

    This function will not call **exit** if pake executes successfully with a return code of zero.
    
    This function will return pake's exit code when **call_exit=False**.

    For all return codes see: :py:mod:`pake.returncodes`.

    This function will never return :py:attr:`pake.returncodes.BAD_ARGUMENTS`,
    because :py:meth:`pake.init` will have already called **exit**.
    
    :raises: :py:exc:`pake.PakeUninitializedException` if :py:class:`pake.init` has not been called.
    :raises: :py:exc:`ValueError` if the **jobs** parameter is used, and is set less than 1.

    :param pake_obj: A :py:class:`pake.Pake` instance, created by :py:func:`pake.init`.

    :param tasks: A list of, or a single default task to run if no tasks are specified on the command line.
                  Tasks specified on the command line completely override this argument.

    :param jobs: Call with an arbitrary number of max jobs, overriding the command line value of **--jobs**.
                 The default value of this parameter is **None**, which means the command line value or default of 1 is not overridden.

    :param call_exit: Whether or not **exit(return_code)** should be called by this function on error.
                      This defaults to **True** and when set to **False** the return code is instead
                      returned to the caller.

    :return: A return code from :py:mod:`pake.returncodes`.

    :type pake_obj: pake.Pake
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

    if pake_obj.task_count == 0:
        _print_err('*** No Tasks.  Stop.')
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
        _print_err("No tasks specified.")
        return m_exit(returncodes.NO_TASKS_SPECIFIED)

    if parsed_args.directory and os.getcwd() != parsed_args.directory:
        # Quietly enforce directory change before running any tasks,
        # incase the current directory was changed after init was called.
        os.chdir(parsed_args.directory)

    if parsed_args.dry_run:
        try:
            pake_obj.dry_run(run_tasks)
            if pake_obj.run_count == 0:
                _print('Nothing to do, all tasks up to date.')
            return 0
        except pake.InputNotFoundException as err:
            _print_err(err)
            return m_exit(returncodes.TASK_INPUT_NOT_FOUND)
        except pake.MissingOutputsException as err:
            _print_err(err)
            return m_exit(returncodes.TASK_OUTPUT_MISSING)
        except pake.UndefinedTaskException as err:
            _print_err(err)
            return m_exit(returncodes.UNDEFINED_TASK)
        except pake.CyclicGraphException as err:
            _print_err(err)
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
            _print('Nothing to do, all tasks up to date.')

    except pake.TaskExitException as err:
        return_code = err.return_code

        if return_code != returncodes.SUCCESS:
            # Print info only for error conditions
            _print_err(os.linesep + str(err) + os.linesep)
            err.print_traceback(file=pake.conf.stderr)
            pake.conf.stderr.write(os.linesep)

    except pake.InputNotFoundException as err:
        _print_err(err)
        return_code = returncodes.TASK_INPUT_NOT_FOUND
    except pake.MissingOutputsException as err:
        _print_err(err)
        return_code = returncodes.TASK_OUTPUT_MISSING
    except pake.UndefinedTaskException as err:
        _print_err(err)
        return_code = returncodes.UNDEFINED_TASK
    except pake.CyclicGraphException as err:
        _print_err(err)
        return_code = returncodes.CYCLIC_DEPENDENCY
    except pake.TaskException as err:
        inner_err = err.exception

        if isinstance(inner_err, pake.SubpakeException):
            pake.conf.stderr.write(os.linesep)
            inner_err.write_info(file=pake.conf.stderr)
            pake.conf.stderr.write(os.linesep)

            return_code = returncodes.SUBPAKE_EXCEPTION

        elif isinstance(inner_err, pake.TaskSubprocessException):
            pake.conf.stderr.write(os.linesep)
            inner_err.write_info(file=pake.conf.stderr)
            pake.conf.stderr.write(os.linesep)

            return_code = returncodes.TASK_SUBPROCESS_EXCEPTION

        else:
            _print_err(os.linesep + str(err) + os.linesep)
            err.print_traceback(file=pake.conf.stderr)
            pake.conf.stderr.write(os.linesep)

            return_code = returncodes.TASK_EXCEPTION

    return _terminate(pake_obj, return_code, exit_func=m_exit)


class TerminateException(SystemExit):
    """
    This exception is raised by :py:meth:`pake.terminate` and :py:meth:`pake.Pake.terminate`,
    it derives :py:exc:`SystemExit` and if it is not caught pake will exit gracefully with
    the return code provided to the exception.

    If this exception is raised inside of a task, :py:meth:`pake.Pake.run` with raise a
    :py:exc:`pake.TaskExitException` in response.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)  # pragma: no cover


def terminate(pake_obj, return_code=returncodes.SUCCESS):  # pragma: no cover
    """
    Preform a graceful exit from a pakefile, printing the leaving directory or exit subpake message if
    needed, then exiting with a given return code.  The default return code is :py:attr:`pake.returncodes.SUCCESS`.

    This should be used as opposed to a raw **exit** call to ensure the output of pake remains consistent.
    
    Use Case:
    
    .. code-block:: python

       import os
       import pake
       from pake import returncodes

       pk = pake.init()

       # Say you need to wimp out of a build for some reason
       # But not inside of a task.  pake.terminate will make sure the
       # 'leaving directory/exiting subpake' message is printed
       # if it needs to be.

       if os.name == 'nt':
           pk.print('You really thought you could '
                    'build my software on windows? nope!')

           pake.terminate(pk, returncodes.ERROR)

           # or

           # pk.terminate(returncodes.ERROR)


       # Define some tasks...

       @pk.task
       def build(ctx):
            # You can use pake.terminate() inside of a task as well as exit()
            # pake.terminate() may offer more functionality than a raw exit()
            # in the future, however exit() will always work as well.

            something_bad_happened = True

            if something_bad_happened:
                pake.terminate(pk, returncodes.ERROR)

                # Or:

                # pk.terminate(returncodes.ERROR)

       pake.run(pk, tasks=build)

    :py:meth:`pake.Pake.terminate` is a shortcut method which passes the **pake_obj** instance to this function for you.

    :param pake_obj: A :py:class:`pake.Pake` instance, created by :py:func:`pake.init`.

    :param return_code: Return code to exit the pakefile with, see :py:mod:`pake.returncodes` for standard return codes.
                        The default return code for this function is :py:attr:`pake.returncodes.SUCCESS`.
                        :py:attr:`pake.returncodes.ERROR` is intended to be used with **terminate** to indicate a
                        generic error, but other return codes may be used.

    :raises: :py:exc:`pake.PakeUninitializedException` if :py:class:`pake.init` has not been called.

    :type pake_obj: pake.Pake
    """

    def m_exit(code):
        raise TerminateException(code)

    if pake_obj.is_running:
        # If is_running is True, then we must be inside a task.

        # It is safe to call exit() inside a task,
        # just call exit, pake will handle the 'leaving directory/exit subpake'
        # message if needed.

        m_exit(return_code)
    else:
        _terminate(pake_obj, return_code, exit_func=m_exit)


def _terminate(pake_obj, return_code, exit_func=exit):
    """

    :type pake_obj: pake.Pake
    """
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
