#!/usr/bin/python3

import sys
import os
import glob

# the directory above tests to the path so pake can be included
# not needed if module is 'installed'
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../../../')))

import pake

make = pake.Make()


@make.target(inputs="test.c", outputs="test.o")
def all(target):
    pake.touch(target.output)
    print(target.input)


@make.target
def clean(target):
    for i in glob.glob("*.o"):
        os.unlink(i)

pake.run(make)