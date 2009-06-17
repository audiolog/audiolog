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

import configuration
import functions
import flowcontrol

import extract
import clean
import convert
import split
import audio

from functions import ext
from functions import quote
from flowcontrol import emitter
from LogFrame import log

def handleIt(directoryPathsToScan):
    """Call traverse on directories; when run ends for any reason inform GUI."""
    
    try:
        for directoryPath in directoryPathsToScan:  
            log("Traversing " + quote(directoryPath), 0, "Actions")
            configuration.PATHS["CURRENT"] = directoryPath
            traverse(directoryPath, True)
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
    
    subdirectoryPaths, filePathsByType = functions.directory(directoryPath)
    
    # If appropriate, rename and recurse into subdirectories
    if configuration.SETTINGS["RECURSE"] and subdirectoryPaths:
        subdirectoryPaths = clean.standardizeFilenames(subdirectoryPaths)
        for subdirectoryPath in subdirectoryPaths:
            traverse(subdirectoryPath)

    # Execute proper actions
    if not rescan:
        log("\nHandling " + quote(directoryPath), 1, "Actions")    
    
    if configuration.ACTIONS["IMAGE"] and "image" in filePathsByType:           # Rename/delete image(s)
        log("Handling images", 2, "Actions")
        clean.handleImages(filePathsByType["image"])
        
    if configuration.ACTIONS["CLEAN"] and "other" in filePathsByType:           # Delete extra files
        log("Deleting extra files", 2, "Actions")
        clean.cleanDir(filePathsByType["other"])
    
    if configuration.ACTIONS["EXTRACT"] and "archive" in filePathsByType:       # Extract archives
        log("Extracting archives then scanning directory again", 2, "Actions")
        extract.extract(filePathsByType["archive"])
        traverse(directoryPath, rescan=True)
        return
        
    if configuration.ACTIONS["CONVERT"] and "bad_audio" in filePathsByType:     # Convert audio to ogg
        log("Converting audio to OGG then scanning again", 2, "Actions")
        convert.convert(filePathsByType["bad_audio"])
        traverse(directoryPath, rescan=True)
        return
    
    if not "good_audio" in filePathsByType:                                     # Continue if audio present
        if not initialCall:
            log("No audio found in " + quote(directoryPath), 2, "Actions")
            functions.deleteItem(directoryPath)
        return
                                                   
    if configuration.ACTIONS["SPLIT"] and "cue" in filePathsByType:             # Split based on cue
        log("Splitting audio into tracks then scanning again", 2, "Actions")
        split.split(filePathsByType["cue"], filePathsByType["good_audio"])
        traverse(directoryPath)
        return
        
    if configuration.ACTIONS["AUDIO"]:                                          # Handle audio
        log("Applying filename conventions", 2, "Actions")
        audioPaths = clean.standardizeFilenames(filePathsByType["good_audio"])
        log("Handling audio", 2, "Actions")
        audio.handleAudio(directoryPath, audioPaths)

