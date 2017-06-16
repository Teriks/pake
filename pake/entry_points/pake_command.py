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

import pake.arguments
import pake.conf
import pake.returncodes as returncodes

# Inherit pakes normal help output

parser = pake.arguments.get_parser()


def _pakefile_not_found(message):
    parser.print_usage(pake.conf.stderr)
    print('{}: error: {}'
          .format(parser.prog, message),
          file=pake.conf.stderr)
    exit(pake.returncodes.PAKEFILE_NOT_FOUND)


def _verify_pakefile_exists(in_file):
    if os.path.exists(in_file):
        if not os.path.isfile(in_file):
            _pakefile_not_found('"{}" is not a file.'.format(in_file))
    else:
        _pakefile_not_found('File "{}" does not exist.'.format(in_file))
    return os.path.abspath(in_file)


parser.add_argument("-f", "--file", nargs=1, action='append', type=_verify_pakefile_exists,
                    help='Pakefile path(s).  This switch can be used more than once, '
                         'all specified pakefiles will be executed in order with the '
                         'current directory as the working directory (unless -C is specified).')


def _find_pakefile_or_exit(directory):
    option_one = os.path.join(directory, 'pakefile.py')
    option_two = os.path.join(directory, 'pakefile')

    if os.path.exists(option_one):
        return os.path.abspath(option_one)
    elif os.path.exists(option_two):
        return os.path.abspath(option_two)
    else:
        print("No pakefile.py or pakefile was found in this directory.", file=pake.conf.stderr)
        exit(returncodes.PAKEFILE_NOT_FOUND)


def _strip_single_arg_switches(sys_args, switch_set):
    continue_twice = False
    for arg in sys_args:
        if continue_twice:
            continue_twice = False
            continue
        if arg in switch_set:
            continue_twice = True
            continue
        yield arg


def main(args=None):
    # Affects interpreter sub processes, not this process.
    os.environ['PYTHONUNBUFFERED'] = '1'

    if args is None:
        args = parser.parse_args()
    else:
        args = parser.parse_args(args=args)

    init_dir = os.getcwd()
    sys_args = sys.argv[1:]

    if not args.file:

        if args.directory:
            file = _find_pakefile_or_exit(args.directory)
        else:
            file = _find_pakefile_or_exit(init_dir)

        exit(subprocess.call([sys.executable, file] + sys_args, stdout=pake.conf.stdout, stderr=pake.conf.stderr))

    # Strip out the -f/--file switches and arguments, put everything else into actual_args.
    # The pakefile itself will not accept a --file argument.  The -C/--directory argument is still
    # going to be forwarded, allowing for this syntax:  pake -f some_file.py -C work_in_some_directory_please

    actual_args = list(
        _strip_single_arg_switches(sys_args, {'-f', '--file'})
    )

    for file in itertools.chain.from_iterable(args.file):
        return_code = subprocess.call([sys.executable, file] + actual_args, stdout=pake.conf.stdout, stderr=pake.conf.stderr)
        if return_code != 0:
            exit(return_code)


if __name__ == "__main__":
    main()
