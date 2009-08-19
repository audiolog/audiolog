# -*- coding: utf-8 -*-

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
import logger

from utils import *
from flowcontrol import emitter

def handleIt(directoryPathsToScan):
    """Call traverse on directories; when run ends for any reason inform GUI."""
    
    try:
        for directoryPath in directoryPathsToScan:  
            logger.log("Traversing %s." % quote(directoryPath), "Actions")
            logger.startSection()
            configuration.PATHS["CURRENT"] = directoryPath
            traverse(directoryPath, True)
            logger.endSection()
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
        logger.startSection()
    
    if configuration.ACTIONS["IMAGE"] and "image" in filePathsByType:           # Rename/delete image(s)
        logger.log('\nRenaming cover image to "cover" and deleting other images.', "Actions")
        logger.startSection()
        clean.handleImages(filePathsByType["image"])
        logger.endSection()
        
    if configuration.ACTIONS["CLEAN"] and "other" in filePathsByType:           # Delete extra files
        logger.log("\nDeleting miscellaneous files.", "Actions")
        logger.startSection()
        clean.cleanDir(filePathsByType["other"])
        logger.endSection()
    
    if configuration.ACTIONS["EXTRACT"] and "archive" in filePathsByType:       # Extract archives
        logger.log("\nExtracting archives then scanning directory again.", "Actions")
        logger.startSection()
        extract.extract(filePathsByType["archive"])
        logger.endSection(2)
        traverse(directoryPath, initialCall=initialCall, rescan=True)
        return
        
    if configuration.ACTIONS["CONVERT"] and "bad_audio" in filePathsByType:     # Convert audio to Ogg
        logger.log("\nConverting audio to Ogg then scanning again.", "Actions")
        logger.startSection()
        convert.convert(filePathsByType["bad_audio"])
        logger.endSection(2)
        traverse(directoryPath, initialCall=initialCall, rescan=True)
        return
    
    if not "good_audio" in filePathsByType:                                     # Continue if audio present
        if not initialCall:
            logger.log("\nNo audio found in %s." % quote(directoryPath), "Actions")
            logger.startSection()
            functions.deleteItem(directoryPath)
            logger.endSection()
        logger.endSection()
        return
                                                   
    if configuration.ACTIONS["SPLIT"] and "cue" in filePathsByType:             # Split based on cue
        logger.log("\nSplitting audio into tracks then scanning again.", "Actions")
        logger.startSection()
        split.split(filePathsByType["cue"], filePathsByType["good_audio"])
        logger.endSection(2)
        traverse(directoryPath, initialCall=initialCall, rescan=True)
        return
        
    if configuration.ACTIONS["AUDIO"]:                                          # Handle audio
        logger.log("\nCleaning up filenames.", "Actions")
        logger.startSection()
        audioPaths = clean.standardizeFilenames(filePathsByType["good_audio"])
        logger.endSection()
        
        logger.log("\nIdentifying audio then writing tags and filenames.", "Actions")
        logger.startSection()
        audio.handleAudio(directoryPath, audioPaths)
        logger.endSection()

    logger.endSection()

