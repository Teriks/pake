#!/usr/bin/env python

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

import itertools
import os.path
import subprocess
import sys

import pake.program

# Inherit pakes normal help output

parser = pake.program._arg_parser


def _verify_file_exists(in_file):
    if os.path.exists(in_file):
        if not os.path.isfile(in_file):
            parser.error('"{}" is not a file.'.format(in_file))
    else:
        parser.error('File "{}" does not exist.'.format(in_file))


parser.add_argument("-f", "--file", nargs=1, action='append', type=_verify_file_exists,
                    help='Pakefile path(s).  This switch can be used more than once, '
                         'all specified pakefiles will be executed in order.')


def main(args=None):
    if args is None:
        args = parser.parse_args()
    else:
        args = parser.parse_args(args=args)

    # Strip out the -f/--file switches, put everything else into actual_args

    sys_args = sys.argv[1:]
    actual_args = []
    switch_set = {'-f', '--file'}
    continue_twice = False

    for arg in sys_args:
        if continue_twice:
            continue_twice = False
            continue
        if arg in switch_set:
            continue_twice = True
            continue

        actual_args.append(arg)

    if not args.file:
        if os.path.exists("pakefile.py"):
            file = os.path.abspath("pakefile.py")
        elif os.path.exists("pakefile"):
            file = os.path.abspath("pakefile")
        else:
            print("No pakefile.py or pakefile was found in this directory.")
            exit(1)

        os.chdir(os.path.dirname(file))
        exit(subprocess.call([sys.executable, file] + actual_args, stdout=sys.stdout, stderr=sys.stderr))

    exit_code = 0
    for file in (os.path.abspath(f) for f in itertools.chain.from_iterable(args.file)):
        os.chdir(os.path.dirname(file))
        code = subprocess.call([sys.executable, file] + actual_args, stdout=sys.stdout, stderr=sys.stderr)
        if code != 0:
            exit_code = 1

    exit(exit_code)


if __name__ == "__main__":
    main()
