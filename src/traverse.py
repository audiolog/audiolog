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

from PyQt4.QtCore import *

import etc.configuration
import etc.functions
import etc.flowcontrol
import etc.logger

import filehandling.extract
import filehandling.clean
import filehandling.convert
import filehandling.split

import metadata.metadata

from etc.utils import *
from etc.flowcontrol import emitter

def handleIt(directoryPathsToScan):
    """Call traverse on directories; when run ends for any reason inform GUI."""
    
    try:
        for directoryPath in directoryPathsToScan:  
            logger.log("Traversing %s." % quote(directoryPath), "Actions")
            logger.startSection("traversing")
            configuration.PATHS["CURRENT"] = directoryPath
            traverse(directoryPath, True)
            logger.endSection("traversing")
    except flowcontrol.StopException:
        emitter.emit(SIGNAL("RunEnded"), "stopped")
    except:
        traceback.print_exc()
        emitter.emit(SIGNAL("RunEnded"), "failed")
    else:
        emitter.emit(SIGNAL("RunEnded"), "complete")

def traverse(directoryPath, initialCall=False, rescan=False):
    """Recursively traverse directories; take actions based on directory content."""
    
    flowcontrol.checkpoint(cleanStopPoint=True)
    if not functions.validatePath(directoryPath, isDirectory=True):
        return
    
    subdirectoryPaths, filePathsByType = functions.getDirectoriesAndFiles(directoryPath)
    
    # If appropriate, rename and recurse into subdirectories
    if configuration.SETTINGS["RECURSE"] and subdirectoryPaths:
        subdirectoryPaths = clean.standardizeFilenames(subdirectoryPaths)
        for subdirectoryPath in subdirectoryPaths:
            traverse(subdirectoryPath)

    # Execute proper actions
    if not rescan:
        logger.log("\nHandling %s." % quote(directoryPath), "Actions")
        logger.startSection("handling dir")
    
    if configuration.ACTIONS["IMAGE"] and "image" in filePathsByType:           # Rename/delete image(s)
        logger.log('\nRenaming cover image to "cover" and deleting other images.', "Actions")
        logger.startSection("images")
        clean.handleImages(filePathsByType["image"])
        logger.endSection("images")
        
    if configuration.ACTIONS["CLEAN"] and "other" in filePathsByType:           # Delete extra files
        logger.log("\nDeleting miscellaneous files.", "Actions")
        logger.startSection("clean")
        clean.cleanDir(filePathsByType["other"])
        logger.endSection("clean")
    
    if configuration.ACTIONS["EXTRACT"] and "archive" in filePathsByType:       # Extract archives
        logger.log("\nExtracting archives then scanning directory again.", "Actions")
        logger.startSection("extract")
        extract.extract(filePathsByType["archive"])
        logger.endSection("extract")
        logger.endSection("handling dir")
        traverse(directoryPath, initialCall=initialCall, rescan=True)
        return
        
    if configuration.ACTIONS["CONVERT"] and "bad_audio" in filePathsByType:     # Convert audio to Ogg
        logger.log("\nConverting audio to Ogg then scanning again.", "Actions")
        logger.startSection("convert")
        convert.convert(filePathsByType["bad_audio"])
        logger.endSection("convert")
        logger.endSection("handling dir")
        traverse(directoryPath, initialCall=initialCall, rescan=True)
        return
    
    if not "good_audio" in filePathsByType:                                     # Continue if audio present
        if not initialCall:
            logger.log("\nNo audio found in %s." % quote(directoryPath), "Actions")
            functions.deleteItem(directoryPath)
        logger.endSection("handling dir")
        return
                                                   
    if configuration.ACTIONS["SPLIT"] and "cue" in filePathsByType:             # Split based on cue
        logger.log("\nSplitting audio into tracks then scanning again.", "Actions")
        logger.startSection("split")
        split.split(filePathsByType["cue"], filePathsByType["good_audio"])
        logger.endSection("split")
        logger.endSection("handling dir")
        traverse(directoryPath, initialCall=initialCall, rescan=True)
        return
        
    if configuration.ACTIONS["METADATA"]:                                          # Handle metadata
        logger.log("\nCleaning up filenames.", "Actions")
        logger.startSection("standardizeFilenames")
        audioPaths = clean.standardizeFilenames(filePathsByType["good_audio"])
        logger.endSection("standardizeFilenames")
        
        logger.log("\nIdentifying audio then writing tags and filenames.", "Actions")
        logger.startSection("handleAudio")
        metadata.handleMetadata(directoryPath, audioPaths)
        logger.endSection("handleAudio")

    logger.endSection()

