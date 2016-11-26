#!/usr/bin/python3

import sys
import os

# the directory above tests to the path so pake can be included
# not needed if module is 'installed'
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../../')))

import pake
import time

make = pake.Make()


@make.target(inputs="baz.c", outputs="baz.o")
def baz(target):
    pake.touch(target.output)
    time.sleep(5)
    print(target.input)


@make.target(inputs="bar.c", outputs="bar.o")
def bar(target):
    pake.touch(target.output)
    time.sleep(5)
    print(target.input)


@make.target(inputs="foo.c", outputs="foo", depends=[bar, baz])
def foo(target):
    pake.touch(target.output)
    print(target.input)


@make.target
def dummy():
    dummy_print = "dummy"

    if make['DUMMY_PRINT']:
        dummy_print = make['DUMMY_PRINT']

    if make['DUMMY_PRINT_CAPS']:
        print(dummy_print.upper())
    else:
        print(dummy_print)


@make.target
def dummy2(target):

    dummy_print = "dummy2"

    # get the value of DUMMY_PRINT if it is defined
    if make['DUMMY_PRINT']:
        dummy_print = make['DUMMY_PRINT']

    # catch -D DUMMY_PRINT_CAPS=true or even
    # -D DUMMY_PRINT_CAPS
    if make['DUMMY_PRINT_CAPS']:
        print(dummy_print.upper())
    else:
        print(dummy_print)


pake.run_program(make)
