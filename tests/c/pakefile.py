#!/usr/bin/python3

import sys
import os

sys.path.append(os.path.abspath('../../'))

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


@make.target(inputs="foo.c", outputs="foo", depends=["bar", baz])
def foo(target):
    pake.touch(target.output)
    print(target.input)


@make.target
def dummy():
    if make['DUMMY_PRINT_CAPS']:
        print("DUMMY")
    else:
        print("dummy")


@make.target
def dummy2(target):
    # catch -D DUMMY_PRINT_CAPS=true or even just
    # -D DUMMY_PRINT_CAPS
    if make['DUMMY_PRINT_CAPS']:
        print("DUMMY2")
    else:
        print("dummy2")


pake.run_program(make)