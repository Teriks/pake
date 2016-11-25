
from pake import TargetInputNotFound
import argparse
import sys

_arg_parser = argparse.ArgumentParser()

_arg_parser.add_argument("targets", type=str, nargs='+', help="Build targets.")

_arg_parser.add_argument("-j", "--jobs",
                         metavar="NUM_JOBS",
                         type=int,
                         default=1,
                         help="Max number of jobs, default is 1.")


def run_program(make):
    args = _arg_parser.parse_args()
    make.set_max_jobs(args.jobs)
    make.set_run_targets(args.targets)

    try:
        make.execute()
    except TargetInputNotFound as input_file_err:
        print(str(input_file_err), file=sys.stderr)
        exit(1)
    make.clear()