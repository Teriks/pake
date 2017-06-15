import sys
import os

script_dir = os.path.dirname(os.path.realpath(__file__))

sys.path.insert(1, os.path.abspath(
    os.path.join(script_dir, os.path.join('..', '..'))))

import pake

pk = pake.init()


DEPTH = pk.get_define('DEPTH')

@pk.task
def default(ctx):
    depth = pake.get_subpake_depth()
    assert depth == DEPTH

pk.run(tasks=default)

