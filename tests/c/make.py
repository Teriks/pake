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


@make.target(inputs="foo.c", outputs="foo", depends=[bar, baz])
def foo(target):
    pake.touch(target.output)
    print(target.input)


@make.target
def dummy():
    print("dummy")


@make.target
def dummy2(target):
    print("dummy2")


pake.run_program(make)