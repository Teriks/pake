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

import argparse
import ast
import atexit
import inspect
import os
import textwrap


import pake
import pake.exception
import pake.util
import pake.console


class _DefineSyntaxError(SyntaxError):
    pass


class PakeUninitializedException(pake.exception.PakeException):
    """Occurs when calling certain pake functions (that rely on global state)
    prior to py:meth:`pake.program.init` being called"""
    pass


_arg_parser = argparse.ArgumentParser()


def _validate_gt_one(value):
    i_value = int(value)
    if i_value < 1:
        _arg_parser.error('Max number of parallel jobs cannot be less than 1.')
    return i_value


def _validate_dir(path):
    if os.path.exists(path):
        if os.path.isdir(path):
            return os.path.abspath(path)
        else:
            _arg_parser.error('Path "{path}" is not a directory.'.format(path=path))
    else:
        _arg_parser.error('Directory "{path}" does not exist.'.format(path=path))


_arg_parser.add_argument('-v', '--version', action='version', version='pake ' + pake.__version__)

_arg_parser.add_argument('targets', type=str, nargs='*', help='Build targets.')

_arg_parser.add_argument('-j', '--jobs',
                         metavar='NUM_JOBS',
                         type=_validate_gt_one,
                         help='Max number of parallel jobs.  Using this option '
                              'enables unrelated targets to run in parallel with a '
                              'max of N targets running at a time.')

_arg_parser.add_argument('-n', '--dry-run', action='store_true', dest='dry_run',
                         help='Use to preform a dry run, lists all targets that '
                              'will be executed in the next actual invocation.')

_arg_parser.add_argument('-t', '--targets', action='store_true', dest='list_targets',
                         help='List all target names.')

_arg_parser.add_argument('-ti', '--targets-info', action='store_true', dest='list_targets_info',
                         help='List all targets which have info strings provided, with their info string.')

_arg_parser.add_argument('-D', '--define', nargs=1, action='append',
                         help='Add defined value.')

_arg_parser.add_argument('-C', '--directory', type=_validate_dir,
                         help='Change directory before executing.')

_arg_parser.add_argument('--s_depth', type=int, default=0, help=argparse.SUPPRESS)


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
                    raise _DefineSyntaxError(
                        'Error parsing define value of "{name}": {message}'
                            .format(name=value_name, message=str(syn_err)))
        else:
            return True

        lower = ls.rstrip().lower()
        if lower == 'false':
            return False
        if lower == 'true':
            return True
    return value


def _defines_to_dic(defines):
    result = {}
    for i in defines:
        d = i[0].split('=', maxsplit=1)
        if len(d) == 1:
            result[d[0].strip()] = True
        else:
            result[d[0].strip()] = _coerce_define_value(d[0], d[1])
    return result


_cur_args = None
_init_file_name = ""


def _error(message):
    pake.console.print_error("{}: error: {}".format(_init_file_name, message))


def _exit_error(message):
    _error(message)
    exit(1)


def get_submake_depth():
    """Get the submake depth of this script, which depends on if another pakefile is executing it
    or not.  Successive calls to :py:meth:`pake.submake.run_script` in child scripts increase the
    submake depth.  Submake depth starts at 0.

    :raises pake.program.PakeUninitializedException: Raised if :py:meth:`pake.program.init`
            has not been called prior to calling this method.

    :return: The submake depth
    :rtype: int
    """

    if _cur_args is None:
        raise PakeUninitializedException("pake.init() has not been called yet.")

    if hasattr(_cur_args, 's_depth'):
        return _cur_args.s_depth
    else:
        return 0



def init():
    """Init pake (Possibly change working directory) and return a :py:class:`pake.make.Make` instance.

    :return: :py:class:`pake.make.Make` instance.
    :rtype: pake.make.Make
    """

    global _cur_args
    global _init_file_name

    frame = inspect.stack()[1]
    module = inspect.getmodule(frame[0])
    _init_file_name = os.path.abspath(module.__file__)

    _cur_args = _arg_parser.parse_args()

    if _cur_args.directory and _cur_args.directory != os.getcwd():
        os.chdir(_cur_args.directory)
        print('Entering Directory: "{dir}"'.format(dir=_cur_args.directory))

        def _at_exit_chdir():
            print('Leaving Directory: "{dir}"'.format(dir=_cur_args.directory))

        atexit.register(_at_exit_chdir)

    make = pake.Make()
    if _cur_args.define:
        try:
            make.set_defines(_defines_to_dic(_cur_args.define))
        except _DefineSyntaxError as syn_err:
            _arg_parser.error(str(syn_err))

    return make


def _sort_target_by_name_key(target):
    return target.name.lower()


def run(make, default_targets=None):
    """The main entry point into pake, handles program arguments and sets up your :py:class:`pake.make.Make` object for execution.

    :param make: your :py:class:`pake.make.Make` object, with targets registered.
    :type make: pake.make.Make

    :param default_targets: The targets to execute if no targets are specified on the command line.
                            This can be a single target, or a list.  The elements may be direct function references
                            or function names as strings.

    :raises pake.program.PakeUninitializedException: Raised if :py:meth:`pake.program.init`
            has not been called prior to calling this method.

    :type default_targets: list or func
    """

    if _cur_args is None:
        raise PakeUninitializedException("pake.init() has not been called yet.")

    if _cur_args.dry_run and _cur_args.jobs:
        _arg_parser.error("-n/--dry-run and -j/--jobs cannot be used together.")

    if len(_cur_args.targets) > 0 and _cur_args.list_targets:
        _arg_parser.error("Run targets may not be specified when using the -t/--targets option to list targets.")

    if _cur_args.list_targets and _cur_args.list_targets_info:
        _arg_parser.error("-t/--targets and -ti/--targets-info cannot be used together.")

    if make.target_count() == 0:
        _arg_parser.error('*** No Targets.  Stop.')

    if _cur_args.list_targets:
        print('\nAll Targets:\n')
        for i in sorted(make.get_all_targets(), key=_sort_target_by_name_key):
            print(i.name)
        return

    if _cur_args.list_targets_info:
        info_targets = sorted(
            [x for x in make.get_all_targets() if x.info],
            key=_sort_target_by_name_key
        )

        longest_target_name = len(
            max(info_targets, key=_sort_target_by_name_key).name
        )

        newline_header = ('\n ' + (' ' * longest_target_name) + ' # ')

        if len(info_targets) == 0:
            print("No targets with info strings are present.")
            return

        print('\nDocumented Targets:\n')
        for i in info_targets:
            print(('{:<' + str(longest_target_name) + '}  {}')
                  .format(i.name, '# ' + newline_header.join(textwrap.wrap(i.info))) + '\n')
        return

    if _cur_args.jobs:
        make.set_max_jobs(_cur_args.jobs)

    if len(_cur_args.targets) > 0:
        run_targets = _cur_args.targets
    else:
        if default_targets is None:
            _arg_parser.error(
                "No targets were provided and no default target "
                "was specified in the pakefile.")

        if pake.util.is_iterable_not_str(default_targets):
            run_targets = default_targets
        else:
            run_targets = [default_targets]

    try:
        make.set_run_targets(run_targets)
    except pake.UndefinedTargetException as target_undef_err:
        _arg_parser.error(str(target_undef_err))

    try:
        if _cur_args.dry_run:
            make.visit()
        else:
            make.execute()
    except pake.TargetInputNotFoundException as input_file_err:
        _exit_error(str(input_file_err))
    except pake.SubMakeException as submake_err:
        _exit_error(str(submake_err))
    except pake.TargetAggregateException as inner_target_err:
        _exit_error(str(inner_target_err))

    if make.get_last_run_count() == 0:
        print("Nothing to do, all targets up to date.")
