import sys
import os

script_dir = os.path.dirname(os.path.realpath(__file__))

sys.path.insert(1, os.path.abspath(
    os.path.join(script_dir, os.path.join('..', '..'))))

import pake

pk = pake.init()

RETURNCODE = pk.get_define('RETURNCODE', 0)
TERMINATE = pk.get_define('TERMINATE', False)


@pk.task
def default(ctx):
    if TERMINATE:
        pk.terminate(RETURNCODE)
    else:
        exit(RETURNCODE)


pake.run(pk, tasks=default)