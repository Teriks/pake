# Copyright (c) 2017, Teriks
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

from .util import get_pakefile_caller_detail

__all__ = ['SubprocessException']


class SubprocessException(Exception):  # pragma: no cover
    """
    Raised upon encountering a non-zero return code from a subprocess,
    when it is not specified that non-zero return codes should be ignored.
    
    .. py:attribute:: cmd
    
        Executed command in list form.
        
    .. py:attribute:: returncode
    
        Process returncode.
        
    .. py:attribute:: output
    
        Process output as bytes.
        
    .. py:attribute:: message
    
        Optional message from the raising function, may be **None**
        
    .. py:attribute:: filename
    
        Filename describing the file from which the process call was initiated. (might be None)
        
    .. py:attribute:: function_name
    
        Function name describing the function which initiated the process call. (might be None)
        
    .. py:attribute:: line_number
    
        Line Number describing the line where the process call was initiated. (might be None)
    """

    def __init__(self, cmd, returncode, output,
                 message=None):
        """
        :param cmd: Command in list form.
        :param returncode: The command's returncode.
        :param output: All output from the command as bytes.
        :param message: Option information.
        """

        c_detail = get_pakefile_caller_detail()

        self.message = message
        self.returncode = returncode
        self.output = output
        self.cmd = cmd

        if c_detail:
            self.filename = c_detail.filename
            self.line_number = c_detail.line_number
            self.function_name = c_detail.function_name
        else:
            self.filename = None
            self.line_number = None
            self.function_name = None

    def __str__(self):

        msg = ''

        template = []
        if self.filename:
            template.append('filename="{}"'.format(self.filename))
        if self.function_name:
            template.append('function_name="{}"'.format(self.function_name))
        if self.line_number:
            template.append('line_number={}'.format(self.line_number))

        if len(template):
            msg += 'pake.SubprocessException({sep}\t{template}{sep}){sep}{sep}'. \
                format(template=(',' + os.linesep + '\t').join(template), sep=os.linesep)
        else:
            msg += 'pake.SubprocessException(){sep}{sep}'.format(sep=os.linesep)

        if self.message:
            msg += 'Message: '+self.message+(os.linesep*2)

        msg += 'The following command exited with return code: {code}{sep}{sep}{cmd}' \
            .format(code=self.returncode, sep=os.linesep, cmd=' '.join(self.cmd))

        if self.output:
            msg += "{sep}{sep}Command Output: {{{sep}{sep}{output}{sep}{sep}}}{sep}" \
                .format(sep=os.linesep, output=self.output.decode().strip())

        return msg
