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

"""Top-level handling control functions.

Handling begins when the GUI invokes handleIt with a list of directories to act
upon. This function calls traverse upon each. After determining what types of
files are present, traverse calls the proper functions to handle each type.
When this process ends - either after being stopped by the user, encountering
an error, or reaching completion - handleIt emits a signal to inform the GUI."""

import os
import sys
import time
import traceback

try:
    from PyQt4.QtCore import SIGNAL
    gui = True
except:
    gui = False

from etc import configuration
from etc import functions
from etc import flowcontrol
from etc import cache

from filehandling import extract
from filehandling import clean
from filehandling import convert
from filehandling import split

from metadata import metadata

from etc.utils import *
from etc.flowcontrol import emitter
from etc.logger import log, logfn, logSection

def handleIt():
    """Call traverse on directories; when run ends for any reason, inform GUI."""
    
    cache.loadCacheDB()
    try:
        for directoryPath in configuration.PATHS["TO_SCAN"]:
            with logSection("Traversing %s." % quote(directoryPath)):
                configuration.PATHS["CURRENT"] = directoryPath
                traverse(directoryPath)
    except flowcontrol.StopException:
        if gui: emitter.emit(SIGNAL("RunEnded"), "stopped")
    except:
        traceback.print_exc()
        if gui: emitter.emit(SIGNAL("RunEnded"), "failed")
    else:
        if gui: emitter.emit(SIGNAL("RunEnded"), "complete")
    cache.saveCacheDB()

def traverse(directoryPath):
    """Recursively traverse directories."""
    
    flowcontrol.checkpoint(cleanStopPoint=True)
    if not functions.validatePath(directoryPath, isDirectory=True):
        return
    
    subdirectoryPaths = functions.getValidSubdirectories(directoryPath)
    
    # If appropriate, rename and recurse into subdirectories
    if subdirectoryPaths:
        for subdirectoryPath in clean.standardizeFilenames(subdirectoryPaths):
            traverse(subdirectoryPath)

    # We are now in a leaf directory with no subdirectories.
    with logSection("\nHandling %s." % quote(directoryPath)):
        handleDirectory(directoryPath)

def handleDirectory(directoryPath):
    """Take actions based on file types present and the user's configuration."""
    
    filePathsByType = functions.getFilePathsByType(directoryPath)
    
    if configuration.ACTIONS["IMAGE"] and "image" in filePathsByType:           # Rename/delete image(s)
        clean.handleImages(filePathsByType["image"])
        
    if configuration.ACTIONS["CLEAN"] and "other" in filePathsByType:           # Delete extra files
        clean.cleanDir(filePathsByType["other"])
    
    if configuration.ACTIONS["EXTRACT"] and "archive" in filePathsByType:       # Extract archives
        extract.extract(filePathsByType["archive"])                             # There may be new subdirectories
        return traverse(directoryPath)                                          # Traverse again
        
    if configuration.ACTIONS["CONVERT"] and "bad_audio" in filePathsByType:     # Convert audio to Ogg and scan again
        convert.convert(filePathsByType["bad_audio"])
        return handleDirectory(directoryPath)
        
    if not "good_audio" in filePathsByType:                                     # Continue if audio present
        log("\nNo audio found in %s." % quote(directoryPath))
        # FIXME: If the user has not requested the metadata process, should this
        # directory actually be accepted rather than deleted at this point?
        if directoryPath != configuration.PATHS["CURRENT"]:
            functions.deleteItem(directoryPath)
        return
            
    if configuration.ACTIONS["SPLIT"] and "cue" in filePathsByType:             # Split based on cue and scan again
        split.split(filePathsByType["cue"], filePathsByType["good_audio"])
        return handleDirectory(directoryPath)
        
    if configuration.ACTIONS["METADATA"]:                                       # Handle metadata
        audioPaths = clean.standardizeFilenames(filePathsByType["good_audio"])
        metadata.handleMetadata(directoryPath, audioPaths)
    