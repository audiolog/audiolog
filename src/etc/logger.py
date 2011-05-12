# -*- coding: utf-8 -*-

#  Audiolog Music Organizer
#  Copyright © 2011  Matt Hubert <matt@cfxnetworks.com> 
#                    Robert Nagle <rjn945@gmail.com>
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.

import re
import sys
from functools import wraps
from contextlib import contextmanager

try:
    from PyQt4.QtCore import QObject, SIGNAL
    gui = True
except ImportError:
    gui = False

from utils import *

class GUILogWriter(object):
    """Provides writeable file-like interface to send text to GUI."""
    
    def __init__(self):
        self.emitter = QObject()
        self.softspace = 0
        
    def write(self, message):
        self.emitter.emit(SIGNAL("AppendToLog"), message)
        
    def flush(self):
        pass
    
    def close(self):
        pass

class Logger(object):
    """Write nested log messages to a set of file-like outputs."""
    
    def __init__(self):
        self.level = 0
        self.outputs = []
        self.indent = "    "
        
    def log(self, msg):
        indent = self.indent * self.level
        msg = ("\n" + indent + msg[1:] + "\n") if msg[0] == "\n" else (indent + msg + "\n")

        for output in self.outputs:
            output.write(toUnicode(msg).encode("UTF-8"))
                
    def startSection(self):
        self.level += 1
        
    def endSection(self):
        self.level = max(0, self.level-1)
        
    def close(self):
        for output in self.outputs:
            output.close()
            
logger = Logger()
if gui:
    logger.outputs.append(GUILogWriter())

# Create aliases so we can treat these as functions provided by this module
# instead of methods of a particular class instance.
log = logger.log
closeLog = logger.close
startLogSection = logger.startSection
endLogSection = logger.endSection
logOutputs = logger.outputs
emitter = logger.outputs[0].emitter


# The two following functions both provide syntatic sugar for implicitly 
# wrapping a section of code in a logging section.
# logSection provides a context manager (for use in a with statement) 
# to log a message and wrap a block of code in a nested log section.
# logfn provides a function decorator with a similar purpose:
# log a message and wrap the execution of a function in a nested log section.
    
@contextmanager
def logSection(msg):
    """For use in with statement; logs message then wraps body in log section."""
    
    log(msg)
    startLogSection()
    yield
    endLogSection()
    
def logfn(msg):
    """Log message describing function; wrap call in start and end sections."""
    
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            # We want to refer to the parameters of the wrapped fn by name,
            # even though that fn has not been called yet.
            # Look away if you're squeamish about seeing hacking and guts.
            # This is gonna get dirty.
            code = fn.func_code
            argNames = code.co_varnames[:code.co_argcount]
            argVals = [None for i in range(code.co_argcount)]
            if fn.func_defaults:
                for i, default in enumerate(reversed(fn.func_defaults)):
                    argVals[-i-1] = default
            for i, val in enumerate(args):
                argVals[i] = val
            fnlocals = dict(zip(argNames, argVals))
            fnlocals.update(kwargs)
            
            def reval(match):
                return toUnicode(eval(match.group()[1:-1], fn.func_globals, fnlocals))
            
            log(re.sub(r"\{.*?\}", reval, msg))
            startLogSection()
            result = fn(*args, **kwargs)
            endLogSection()
            return result
        return wrapper
    return decorator
