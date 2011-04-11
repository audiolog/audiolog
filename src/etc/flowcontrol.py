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

"""Communication between threads and flow control.

This file contains functions to stop or pause the handler thread.
Because there is no good way from within the GUI thread to immediately pause or 
stop the handler thread, we instead use a pause lock and stop flag which the 
handler thread checks at regular intervals. This done by calling the checkpoint
function which will hang if the pause lock has already been acquired (and will 
stay there until it is released) and will raise a StopException if the stop 
flag is set. This exception is then caught in traverse.handleIt. Because these
actions will only be taken when the checkpoint function is called, pausing and
stopping happen quickly but not immediately.

The file also contains an emitter which is used by the handler thread to 
send signals which are caught by the GUI. The emitter is somewhat out of place
in this file but currently there is nowhere better to put it."""

import threading

import PyQt4.QtCore

PAUSED = False
PAUSE_LOCK = threading.Lock()

STOP_NOW = False
STOP_CLEANLY = False

emitter = PyQt4.QtCore.QObject()

class StopException(Exception):
    """Raised when stop flag is set.
    
    This exception is caught in traverse.handleIt."""
    
    pass

def checkpoint(cleanStopPoint=False, pauseOnly=False):
    """Pause if pause lock is unavailable; stop if DIE flag is set.
    
    This function is called regularly throughout the handling process.
    
    The cleanStopPoint parameter indicates that we are not in the middle of 
    processing a directory. Currently this is only true at the top of traverse.
    If the user asks to stop after the current directory (to stop "cleanly")
    then we will only stop if cleanStopPoint is True. If the user asks to stop
    now (the default), the handler thread will stop at the next checkpoint.
    The pauseOnly parameter indicates that we do not want allow processing to 
    be stopped now. Currently this is only used while we are writing tags."""
    
    PAUSE_LOCK.acquire()
    PAUSE_LOCK.release()
    
    if not pauseOnly and (STOP_NOW or (STOP_CLEANLY and cleanStopPoint)):
        raise StopException
    
def pause():
    """Acquire pause lock and set pause flag."""
    
    global PAUSED
    if not PAUSED:
        PAUSE_LOCK.acquire()
        PAUSED = True
    
def unpause():
    """Release pause lock and clear pause flag."""
    
    global PAUSED
    if PAUSED:
        PAUSE_LOCK.release()
        PAUSED = False

def stop(cleanly=False):
    """Set appropriate stop flag and unpause if paused."""
    
    global STOP_CLEANLY, STOP_NOW
    if cleanly:
        STOP_CLEANLY = True
    else:
        STOP_NOW = True
    unpause()

def initialize():
    """Clear flags and release pause lock for a new run."""
    
    global STOP_CLEANLY, STOP_NOW
    STOP_CLEANLY = False
    STOP_NOW = False
    unpause()
    
