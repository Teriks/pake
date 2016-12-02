# Copyright (c) 2016, Teriks
# All rights reserved.
#
# pake is distributed under the following BSD 3-Clause License
#
# Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
#
# 3. Neither the name of the copyright holder nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
# ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


class ReadOnlyList:
    """A read only list wrapper that allows for concatenation and the usual python list comparisons, iteration, etc...
    but no modifying operations.
    """

    def __init__(self, base_list):
        self._l = base_list

    def __getitem__(self, item):
        return self._l[item]

    def __iter__(self):
        return self._l.__iter__()

    def __len__(self):
        return self._l.__len__()

    def __contains__(self, item):
        return item in self._l

    def __str__(self):
        return self._l.__str__()

    def __hash__(self):
        return self._l.__hash__()

    def __eq__(self, other):
        return self._l.__eq__(other)

    def __radd__(self, other):
        return other.__add__(self._l)

    def __add__(self, other):
        return self._l.__add__(other)

    def __ge__(self, other):
        return self._l.__ge__(other)

    def __le__(self, other):
        return self._l.__le__(other)

    def __lt__(self, other):
        return self._l.__lt__(other)

    def __gt__(self, other):
        return self._l.__gt__(other)


def is_iterable(obj):
    """Test if an object is iterable.

    :returns: True or False
    :rtype: bool
    """

    try:
        a = iter(obj)
    except TypeError:
        return False
    return True


def is_iterable_not_str(obj):
    """Test if an object is iterable and not a string.

    :returns: True or False
    :rtype: bool
    """

    return is_iterable(obj) and type(obj) is not str


def str_is_float(s):
    """Test if a string can be parsed into a float.

    :returns: True or False
    :rtype: bool
    """

    try:
        float(s)
        return True
    except ValueError:
        return False


def str_is_int(s):
    """Test if a string can be parsed into an integer.

    :returns: True or False
    :rtype: bool
    """

    try:
        int(s)
        return True
    except ValueError:
        return False