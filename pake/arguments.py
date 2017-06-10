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
from gettext import gettext as _

__all__ = ['parse_args', 'get_parser', 'args_are_parsed', 'get_args']

_arg_parser = argparse.ArgumentParser(prog='pake')


def _create_gt_int(less_message):
    def _gt_zero_int(val):
        val = int(val)
        if val < 1:
            _arg_parser.print_usage(pake.conf.stderr)
            print(_('{}: error: {}').format(_arg_parser.prog, less_message), file=pake.conf.stderr)
            exit(2)
        return val

    return _gt_zero_int


_arg_parser.add_argument('-v', '--version', action='version', version='pake ' + pake.__version__)

_arg_parser.add_argument('tasks', type=str, nargs='*', help='Build tasks.')

_arg_parser.add_argument('-D', '--define', action='append', help='Add defined value.')

_arg_parser.add_argument('-j', '--jobs', type=_create_gt_int('--jobs must be greater than one.'),
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
                         help='List all tasks along side their doc string. '
                              'Only tasks with doc strings present will be shown.')

_parsed_args = None


def parse_args(args=None):
    global _parsed_args
    _parsed_args = _arg_parser.parse_args(args=args)
    return _parsed_args


def get_parser():  # pragma: no cover
    return _arg_parser


def args_are_parsed():
    return _parsed_args is not None


def get_args():
    return _parsed_args


def clear_args():
    global _parsed_args
    _parsed_args = None
