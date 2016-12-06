#!/usr/bin/env python

import sys
import os.path
import subprocess
import itertools
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

    for i in range(0, len(sys_args)):
        if continue_twice:
            continue_twice = False
            continue
        if sys_args[i] in switch_set:
            continue_twice = True
            continue

        actual_args.append(sys_args[i])

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