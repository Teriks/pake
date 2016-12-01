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
import os
import sys

import pake

from pake.util import ChangeDirContext, DefinesContainer, str_is_int, str_is_float


class _DefineSyntaxError(SyntaxError):
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
            return path
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

_arg_parser.add_argument('-D', '--define', nargs=1, action='append',
                         help='Add defined value.')

_arg_parser.add_argument('-C', '--directory', type=_validate_dir,
                         help='Change directory before executing.')


def _coerce_define_value(value_name, value):
    if str_is_int(value):
        return int(value)
    elif str_is_float(value):
        return float(value)
    else:
        ls = value.lstrip()
        if len(ls) > 0:
            if ls[0] == '\'' or ls[0] == '\"':
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


def get_defines():
    """Preemptively get the defines passed to the pakefile on the command line.

    :return: A :py:class:`pake.util.DefinesContainer` which behaves
        similarly to how :py:class:`Make` does when it comes to reading
        defines that do not exist.

    :rtype: pake.util.DefinesContainer
    """

    args = _arg_parser.parse_args()
    if args.define:
        try:
            return DefinesContainer(_defines_to_dic(args.define))
        except _DefineSyntaxError as syn_err:
            print(str(syn_err), file=sys.stderr)
            exit(1)
    return DefinesContainer({})


def get_directory():
    """Get the desired working directory for pake, the return value depends on if -C/--directory is used, and what value is passed to it.
    If a value is passed to -C, that value is returned by this function.  If -C is not specified then the currrent working directory is returned.

    :return: The value passed to -C/--directory on the command line, or the current working directory if -C was not used.
    :rtype: str
    """

    args = _arg_parser.parse_args()
    if args.directory:
        return args.directory
    else:
        return os.getcwd()


def run(make, default_targets=None):
    """The main entry point into pake, handles program arguments and sets up your :py:class:`pake.Make` object for execution.
    :param make: your :py:class:`pake.Make` object, with targets registered.
    :type make: pake.Make

    :param default_targets: The targets to execute if no targets are specified on the command line.
        This can be a single target, or a list.  The elements may be direct function references or function names as strings.

    :type default_targets: list or func
    """

    args = _arg_parser.parse_args()

    if args.dry_run and args.jobs:
        _arg_parser.error("-n/--dry-run and -j/--jobs cannot be used together.")

    with ChangeDirContext(args.directory):

        if make.target_count() == 0:
            _arg_parser.error('*** No Targets.  Stop.')

        if args.jobs:
            make.set_max_jobs(args.jobs)

        if len(args.targets) > 0:
            run_targets = args.targets
        else:
            if default_targets is None:
                _arg_parser.error("No targets were provided and no default target was specified in the pakefile.")

            if pake.util.is_iterable_not_str(default_targets):
                run_targets = default_targets
            else:
                run_targets = [default_targets]

        try:
            make.set_run_targets(run_targets)
        except pake.UndefinedTargetException as target_undef_err:
            _arg_parser.error(str(target_undef_err))

        try:
            if args.dry_run:
                make.visit()
            else:
                make.execute()
        except pake.TargetInputNotFound as input_file_err:
            _arg_parser.error(str(input_file_err))

        if make.get_last_run_count() == 0:
            print("Nothing to do, all targets up to date.")

    make.clear_targets()
