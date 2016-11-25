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

import pake
import argparse
import sys

_arg_parser = argparse.ArgumentParser()


def _validate_gt_one(value):
    i_value = int(value)
    if i_value < 1:
        _arg_parser.error('Number of jobs cannot be less than 1.')
    return i_value


_arg_parser.add_argument('-v', '--version', action='version', version='pake '+pake.__version__)

_arg_parser.add_argument('targets', type=str, nargs='+', help='Build targets.')

_arg_parser.add_argument('-j', '--jobs',
                         metavar='NUM_JOBS',
                         type=_validate_gt_one,
                         help='Max number of jobs, default is 1.')


_arg_parser.add_argument('-d', '--dry', action='store_true', 
                         help='Use to preform a dry run, lists all targets that '
                              'will be executed in the next actual invocation.')


def run_program(make):
    args = _arg_parser.parse_args()
    
    if args.dry and args.jobs:
        print("-d/--dry and -j/--jobs cannot be used together.", file=sys.stderr)
        exit(1)

    if args.jobs:
        make.set_max_jobs(args.jobs)
    else:
        make.set_max_jobs(1)

    try:
        make.set_run_targets(args.targets)
    except pake.UndefinedTargetException as target_undef_err:
        print(str(target_undef_err), file=sys.stderr)
        exit(1)

    try:
        if args.dry:
            make.visit()
        else:
            make.execute()
    except pake.TargetInputNotFound as input_file_err:
        print(str(input_file_err), file=sys.stderr)
        exit(1)

    if make.get_last_run_count() == 0:
        print("Nothing to do, all targets up to date.")

    make.clear()