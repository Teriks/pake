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

import os


class ReadOnlyList:
    def __init__(self, l):
        self._l = l

    def __getitem__(self, item):
        return self._l[item]

    def __iter__(self):
        for i in self._l:
            yield i


class ChangeDirContext:
    def __init__(self, directory):
        self._cwd = os.getcwd()
        self._dir = directory

        def on_enter(directory):
            print('Entering Directory: "{dir}"'.format(dir=directory))

        def on_exit(directory):
            print('Leaving Directory: "{dir}"'.format(dir=directory))

        self.on_enter = on_enter
        self.on_exit = on_exit

    def __enter__(self):
        if self._dir and self._dir != self._cwd:
            self.on_enter(self._dir)
            os.chdir(self._dir)
        return self

    def __exit__(self, type, value, traceback):
        if self._dir and self._dir != self._cwd:
            self.on_exit(self._dir)
            os.chdir(self._cwd)


def is_iterable(obj):
    """Test if an object is iterable."""
    try:
        a = iter(obj)
    except TypeError:
        return False
    return True


def is_iterable_not_str(obj):
    """Test if an object is iterable and not a string."""
    return is_iterable(obj) and type(obj) is not str


def str_is_float(s):
    """Test if a string can be parsed into a float."""
    try:
        float(s)
        return True
    except ValueError:
        return False


def str_is_int(s):
    """Test if a string can be parsed into an integer."""
    try:
        int(s)
        return True
    except ValueError:
        return False