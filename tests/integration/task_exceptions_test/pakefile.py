import sys
import os

sys.path.insert(1,
                os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../../../')))

import pake
import pake.conf

pake.conf.stdout = open(os.devnull,'w')
pake.conf.stderr = open(os.devnull,'w')

pk = pake.init()


@pk.task
def c_task(ctx):
    pass

@pk.task
def b_task(ctx):
    raise Exception()


@pk.task(b_task, c_task)
def a_task(ctx):
    pass

output = ''
try:
    pk.run(tasks=a_task)
except pake.TaskException:
    output += 'pass'
else:
    output += 'fail'


try:
    pk.run(tasks=a_task, jobs=10)
except pake.TaskException:
    output += 'pass'
else:
    output += 'fail'

print(output)