# -*- coding: utf-8 -*-

#  Azul Music Organizer
#  Copyright © 2009  Matt Hubert <matt@cfxnetworks.com> and Robert Nagle <rjn945@gmail.com>
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

from PyQt4.QtCore import *

emitter = QObject()
lastLevel = 0
bufferOn = False
logBuffer = []

def log(message, category):
    """Send message to LogFrame and, if on, the log buffer."""
    
    global lastLevel, bufferOn, logBuffer, emitter
    
    if message[0] == "\n":
        message = "\n" + "    "*(lastLevel) + message[1:]
    else:
        message = "    "*(lastLevel) + message
    
    if bufferOn:
        logBuffer.append(message)
        
    emitter.emit(SIGNAL("AppendToLog"), message, lastLevel, category)

def startSection():
    """Increase indentation level."""
    
    global lastLevel
    lastLevel += 1

def endSection(num=1):
    """Decrease indentation level."""
    
    global lastLevel
    lastLevel -= num

def startBuffer():
    """Start writing all log messages to buffer."""
    
    global bufferOn
    bufferOn = True

def getBuffer():
    """Returns the contents of the log buffer."""
    
    global logBuffer
    return logBuffer

def endBuffer():
    """Stop writing log messages to buffer and clear buffer."""
    
    global bufferOn, logBuffer
    bufferOn = False
    logBuffer = []
