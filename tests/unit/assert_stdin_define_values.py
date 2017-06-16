import sys

import os

script_dir = os.path.dirname(os.path.realpath(__file__))

sys.path.insert(1, os.path.abspath(
    os.path.join(script_dir, os.path.join('..', '..'))))

import pake
import pake.returncodes

pk = pake.init()

assert pk['DEFINE_VALUE_TRUE'] is True
assert pk['DEFINE_VALUE_FALSE'] is False
assert pk['DEFINE_VALUE_STRING'] == 'string'
assert pk['DEFINE_VALUE_LIST'] == ['list', 42]
assert pk['DEFINE_VALUE_DICT'] == {'dict': 42}

assert type(pk['DEFINE_VALUE_TUP']) is tuple
assert pk['DEFINE_VALUE_TUP'] == ('tuple', 42)

assert type(pk['DEFINE_VALUE_SET']) is set
assert pk['DEFINE_VALUE_SET'] == {'set', 42}

pk.terminate(pake.returncodes.SUCCESS)
