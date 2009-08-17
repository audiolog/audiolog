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
