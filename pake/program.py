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

from pake.util import ChangeDirContext


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

_arg_parser.add_argument('targets', type=str, nargs='+', help='Build targets.')

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


def _is_float(s):
    try:
        float(s)
        return True
    except ValueError:
        return False


def _is_int(s):
    try:
        int(s)
        return True
    except ValueError:
        return False


def _coerce_define_value(value_name, value):
    if _is_int(value):
        return int(value)
    elif _is_float(value):
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


def run(make):
    """The main entry point into pake, handles program arguments and sets up your :py:class:`pake.Make` object for execution.
    :param make: your :py:class:`pake.Make` object, with targets registered.
    :type make: pake.Make
    """

    args = _arg_parser.parse_args()

    if args.dry_run and args.jobs:
        print("-n/--dry-run and -j/--jobs cannot be used together.", file=sys.stderr)
        exit(1)

    with ChangeDirContext(args.directory):

        if make.target_count() == 0:
            print('*** No Targets.  Stop.')
            exit(0)

        if args.jobs:
            make.set_max_jobs(args.jobs)

        try:
            make.set_run_targets(args.targets)
        except pake.UndefinedTargetException as target_undef_err:
            print(str(target_undef_err), file=sys.stderr)
            exit(1)

        if args.define:
            try:
                make.set_defines(_defines_to_dic(args.define))
            except _DefineSyntaxError as syn_err:
                print(str(syn_err), file=sys.stderr)
                exit(1)

        try:
            if args.dry_run:
                make.visit()
            else:
                make.execute()
        except pake.TargetInputNotFound as input_file_err:
            print(str(input_file_err), file=sys.stderr)
            exit(1)

        if make.get_last_run_count() == 0:
            print("Nothing to do, all targets up to date.")

    make.clear_targets()
