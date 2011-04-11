# -*- coding: utf-8 -*-

#  Audiolog Music Organizer
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

import sys

from PyQt4.QtCore import *

emitter = QObject()
printAlso = False
lastLevel = 0
bufferOn = False
openSections = []
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
    
    if printAlso:
        try:
            print message
        except UnicodeEncodeError:
            try:
                print unicode(message, "UTF_8")
            except:
                print "===Line omitted due to encoding errors.==="
        
    if category == "Errors":
        try:
            sys.stderr.write(message)
        except UnicodeEncodeError:
            try:
                sys.stderr.write(unicode(message, "UTF_8"))
            except:
                sys.stderr.write("===Line omitted due to encoding errors.===")

def startSection(sectionName=None):
    """Increase indentation level."""
    
    global lastLevel, openSections
    lastLevel += 1
    #if sectionName:
    #    if sectionName in openSections:
    #        print "Section has been opened twice:", sectionName
    #openSections.append(sectionName)

def endSection(sectionName=None, num=1):
    """Decrease indentation level."""
    
    global lastLevel, openSections
    if type(sectionName) == type(3):
        num = sectionName
        sectionName = None
    lastLevel -= num
    #if sectionName:
    #    if not sectionName in openSections:
    #        print "Closing section which is not open:", sectionName
    #else:
    #    openSections.remove(sectionName)

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

def logWrap(msg):
    """Log message describing function; wrap call in start and end sections."""

    def logWrapInner(fn):
        def wrapped(*args):
            msgd = re.sub(r"\*\d", lambda i: str(args[int(i.group()[1:])]), msg)     # Allows message to contain, parameters to log-wrapped function
            print msgd
            print "start"
            result = fn(*args)
            print "end"
            return result
        return wrapped
    return logWrapInner

def replaceWithArg(match):
    matched = match.group()
    digit = matched[1:]
    num = int(digit)
    arg = args[num]
    return str(arg)
