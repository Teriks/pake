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

import colorama
import re
import sys

colorama.init()

_remove_ansi_codes_regex = re.compile(r'\x1b\[([0-9,A-Z]{1,2}(;[0-9]{1,2})?(;[0-9]{3})?)?[m|K]?')


def remove_ansi_codes(string):
    """Strip ANSI escape sequences out of a string.

    :return: A string with any ANSI escape sequences removed.
    :rtype: str
    """
    return _remove_ansi_codes_regex.sub('', string)


def print_error(*objects, sep=' ', end='\n', file=sys.stdout):
    """print_error(\*objects, sep=' ', end='\\\\n', file=sys.stdout)

    Print objects to stdout or a file like object, ANSI escape codes are added to
    make the foreground text color red."""
    print(colorama.Fore.RED + remove_ansi_codes(sep.join(objects)) + colorama.Style.RESET_ALL,
          end=end, file=file)


def print_warning(*objects, sep=' ', end='\n', file=sys.stdout):
    """print_warning(\*objects, sep=' ', end='\\\\n', file=sys.stdout)

    Print objects to stdout or a file like object, ANSI escape codes are added to
    make the foreground text color yellow."""
    print(colorama.Fore.YELLOW + remove_ansi_codes(sep.join(objects)) + colorama.Style.RESET_ALL,
          end=end, file=file)
