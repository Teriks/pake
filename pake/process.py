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
import shutil

from .util import get_pakefile_caller_detail

__all__ = ['SubprocessException']


class SubprocessException(Exception):
    """
    Raised upon encountering a non-zero return code from a subprocess,
    when it is not specified that non-zero return codes should be ignored.
    
    .. py:attribute:: cmd
    
        Executed command in list form.
        
    .. py:attribute:: returncode
    
        Process returncode.
        
    .. py:attribute:: message
    
        Optional message from the raising function, may be **None**
        
    .. py:attribute:: filename
    
        Filename describing the file from which the process call was initiated. (might be None)
        
    .. py:attribute:: function_name
    
        Function name describing the function which initiated the process call. (might be None)
        
    .. py:attribute:: line_number
    
        Line Number describing the line where the process call was initiated. (might be None)
    """

    def __init__(self, cmd, returncode,
                 output=None,
                 output_stream=None,
                 message=None):
        """
        :param cmd: Command in list form.
        :param returncode: The command's returncode.

        :param output: (Optional) All output from the command as bytes.

        :param output_stream: (Optional) A file like object containing the process output, at seek(0).
                               By providing this parameter instead of **output**, you give this object permission
                               to close the stream when it is garbage collected or when :py:meth:`pake.SubprocessException.write_info` is called.

        :param message: Optional exception message.
        """

        super().__init__(message)

        if output is not None and output_stream is not None:
            raise ValueError('output and output_stream parameters cannot be used together.')

        c_detail = get_pakefile_caller_detail()

        self.message = message
        self.returncode = returncode
        self.cmd = cmd

        self._output = output
        self._output_stream = output_stream

        if c_detail:
            self.filename = c_detail.filename
            self.line_number = c_detail.line_number
            self.function_name = c_detail.function_name
        else:
            self.filename = None
            self.line_number = None
            self.function_name = None

    def __del__(self):
        if self._output_stream is not None:
            self._output_stream.close()
            self._output_stream = None

    def write_info(self, file):
        """Writes information about the subprocess exception to a file like object.

        This is necessary over implementing in __str__, because the process output might be drawn from another file
        to prevent issues with huge amounts of process output.
        """

        class_name = self.__module__ + "." + self.__class__.__name__

        template = []
        if self.filename:
            template.append('filename="{}"'.format(self.filename))
        if self.function_name:
            template.append('function_name="{}"'.format(self.function_name))
        if self.line_number:
            template.append('line_number={}'.format(self.line_number))

        if len(template):
            file.write('{myname}({sep}\t{template}{sep}){sep}{sep}'.
                       format(myname=class_name, template=(',' + os.linesep + '\t').join(template), sep=os.linesep))
        else:
            file.write('{myname}(){sep}{sep}'.format(myname=class_name, sep=os.linesep))

        if self.message:
            # noinspection PyTypeChecker
            # os.linesep is a string, * 2 duplicates it twice
            file.write('Message: ' + self.message + (os.linesep * 2))

        file.write('The following command exited with return code: {code}{sep}{sep}{cmd}' \
                   .format(code=self.returncode, sep=os.linesep, cmd=' '.join(self.cmd)))

        if self._output or self._output_stream:
            file.write("{sep}{sep}Command Output: {{{sep}{sep}".format(sep=os.linesep))

            if self._output_stream:
                try:
                    shutil.copyfileobj(self._output_stream, file)
                finally:
                    try:
                        self._output_stream.close()
                    finally:
                        self._output_stream = None
            else:
                file.write(self._output.decode())

            file.write("{sep}{sep}}}{sep}".format(sep=os.linesep))
