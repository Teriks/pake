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
import pake
import pake.conf
import os.path
import pake.returncodes
from pake import returncodes

__all__ = ['parse_args', 'get_parser', 'args_are_parsed', 'get_args']

_ARG_PARSER = argparse.ArgumentParser(prog='pake')


def _create_gt_int(minimum, less_message):
    def _gt_zero_int(val):
        val = int(val)
        if val < minimum:
            _ARG_PARSER.print_usage(pake.conf.stderr)
            print('{}: error: {}'
                  .format(_ARG_PARSER.prog, less_message),
                  file=pake.conf.stderr)
            exit(pake.returncodes.BAD_ARGUMENTS)
        return val

    return _gt_zero_int


def _absolute_directory(directory):
    if os.path.isdir(directory):
        return os.path.abspath(directory)
    else:
        _ARG_PARSER.print_usage(pake.conf.stderr)
        print('{prog}: error: Directory "{dir}" does not exist.'
              .format(prog=_ARG_PARSER.prog, dir=directory),
              file=pake.conf.stderr)
        exit(pake.returncodes.BAD_ARGUMENTS)


_ARG_PARSER.add_argument('-v', '--version', action='version', version='pake ' + pake.__version__)

_ARG_PARSER.add_argument('tasks', type=str, nargs='*', help='Build tasks.')

_ARG_PARSER.add_argument('-D', '--define', action='append', help='Add defined value.')

_ARG_PARSER.add_argument('-j', '--jobs', type=_create_gt_int(1, '--jobs must be greater than zero.'),
                         help='Max number of parallel jobs.  Using this option '
                              'enables unrelated tasks to run in parallel with a '
                              'max of N tasks running at a time.')

_ARG_PARSER.add_argument('--_subpake_depth', default=0, type=int, help=argparse.SUPPRESS,  dest='subpake_depth',)

_ARG_PARSER.add_argument('--stdin-defines', action='store_true', dest='stdin_defines',
                         help='Read defines from a Python Dictionary piped into stdin. '
                              'Defines read with this option can be overwritten by defines '
                              'specified on the command line with -D/--define.')

_ARG_PARSER.add_argument('-n', '--dry-run', action='store_true', dest='dry_run',
                         help='Use to preform a dry run, lists all tasks that '
                              'will be executed in the next actual invocation.')

_ARG_PARSER.add_argument('-C', '--directory', help='Change directory before executing.',
                         type=_absolute_directory)

_ARG_PARSER.add_argument('-t', '--show-tasks', action='store_true', dest='show_tasks',
                         help='List all task names.')

_ARG_PARSER.add_argument('-ti', '--show-task-info', action='store_true', dest='show_task_info',
                         help='List all tasks along side their doc string. '
                              'Only tasks with doc strings present will be shown.')

_PARSED_ARGS = None


def _validate_arguments(parsed_args):
    """
    Validate command line arguments.

    This function should return a tuple of (True/False, return_code)

    If the first value of the tuple is True, parse_args will exit with the given return code.

    :param parsed_args: parsed argument object from the argparse module.
    :return: Tuple of (True/False, return_code)
    """

    if parsed_args.stdin_defines:
        if parsed_args.show_tasks:
            print('-t/--show-tasks and --stdin-defines cannot be used together.',
                  file=pake.conf.stderr)
            return True, returncodes.BAD_ARGUMENTS

        if parsed_args.show_task_info:
            print('-ti/--show-task-info and --stdin-defines cannot be used together.',
                  file=pake.conf.stderr)
            return True, returncodes.BAD_ARGUMENTS

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


def parse_args(args=None):
    global _PARSED_ARGS
    _PARSED_ARGS = _ARG_PARSER.parse_args(args=args)

    should_exit, return_code = _validate_arguments(_PARSED_ARGS)
    if should_exit:
        exit(return_code)

    return _PARSED_ARGS


def get_parser():  # pragma: no cover
    return _ARG_PARSER


def args_are_parsed():
    return _PARSED_ARGS is not None


def get_args():
    return _PARSED_ARGS


def clear_args():
    global _PARSED_ARGS
    _PARSED_ARGS = None
