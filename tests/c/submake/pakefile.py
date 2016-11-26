#!/usr/bin/python3

import sys
import os

# the directory above tests to the path so pake can be included
# not needed if module is 'installed'
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../../../')))

import pake

make = pake.Make()


@make.add_target
def test(target):
    print("TEST SUB MAKE")

pake.run_program(make)
