
import os
import sys

sys.path.insert(1,
                os.path.abspath(
                    os.path.join(os.path.dirname(os.path.realpath(__file__)), '..')))

import pake.conf

pake.conf.stdout = open(os.devnull, 'w')
pake.conf.stderr = open(os.devnull, 'w')