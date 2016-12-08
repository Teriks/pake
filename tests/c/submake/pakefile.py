#!/usr/bin/python3

import sys
import os
import glob

# the directory above tests to the path so pake can be included
# not needed if module is 'installed'
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../../../')))

import pake

make = pake.init()

print("Import Export TEST 0 = "+str(make["TEST_EXPORT"]))
print("Import Export TEST 1 = "+str(make["TEST_EXPORT1"]))
print("Import Export TEST 2 = "+str(make["TEST_EXPORT2"]))
print("Import Export TEST 3 = "+str(make["TEST_EXPORT3"]))
print("Import Export TEST 4 = "+str(make["TEST_EXPORT4"]))
print("Import Export TEST 5 = "+str(make["TEST_EXPORT5"]))


@make.target(inputs="test.c", outputs="test.o")
def all(target):
    file_helper = pake.FileHelper(target)
    file_helper.touch(target.outputs[0])
    target.print(target.inputs[0])


@make.target
def clean(target):
    for i in glob.glob("*.o"):
        os.unlink(i)

pake.run(make)