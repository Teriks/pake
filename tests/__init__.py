
import os
import sys

sys.path.insert(1,
                os.path.abspath(
                    os.path.join(os.path.dirname(os.path.realpath(__file__)), '..')))

_dev_null = None


def open_devnull():
    global _dev_null
    if _dev_null is None:
        _dev_null = open(os.devnull, 'w')
        return _dev_null
    else:
        return _dev_null