# -*- coding: utf-8 -*-

"""A collection of commonly used functions.

This file contains functions which are not specific to one step of the handling
process but are used throughout. There are two main categories of functions
present: moving functions (such as acceptItem, rejectItem and deleteItem) and 
path functions (such as validatePath, filePathsByExt and findFiles)."""

import os
import shutil
import subprocess
import string
import datetime

import configuration
import logger
from utils import *

#-------------------------------------------
# Accepting, rejecting and deleting functions
#-------------------------------------------

def moveWithContext(currentItemPath, destDirectoryPath):
    """Recreate full path relative configuration.CURRENT in destDirectoryPath.
    
    Example:
    Current folder being scanned: "/media/Ext/Download/"
    Current file: "/media/Ext/Download/Rock/College Rock/Morrissey/disco.rar" 
    Destination directory: REJECTS folder "/media/Ext/Rejects/"
    Final path: "/media/Ext/Rejects/Rock/College Rock/Morissey/disco.rar" """

    logger.startSection()
    if not validatePath(currentItemPath):
        logger.log("Could not move with context " + quote(currentItemPath) + " -- not a valid path.", "Failures")
        return
    else:
        logger.log("Moving with context %s." % quote(currentItemPath), "Actions")
    
    newItemPath = currentItemPath.replace(configuration.PATHS["CURRENT"], destDirectoryPath)
    newDirectoryPath = os.path.dirname(newItemPath)
    
    if not os.path.exists(newDirectoryPath):
        os.makedirs(newDirectoryPath)

    logger.startSection()
    if not os.path.exists(newItemPath):
        logger.log("Moving to %s." % quote(newItemPath), "Details")
        shutil.move(currentItemPath, newItemPath)
    else:
        logger.log("Could not move. Destination path %s already exists." % quote(newItemPath), "Failures")
    logger.endSection(2)
    
    # Remove the old containing directory if it's empty
    try: 
        os.rmdir(os.path.dirname(currentItemPath))
    except OSError: 
        pass


def acceptItem(itemPath, destDirectoryRelPath, depth=1):
    """Move a file or directory to the SORTED folder.
    
    Parameters:
        itemPath can point to a file or directory.
        destDirectoryRelPath is a path relative to the SORTED directory.
        depth is provided only when the function recursively calls itself."""

    logger.startSection()
    logger.log("Accepting %s." % quote(itemPath), "Actions")

    # Create destination directory
    destDirectoryPath = os.path.join(configuration.PATHS["SORTED"], destDirectoryRelPath)
    if not os.path.exists(destDirectoryPath):
        os.makedirs(destDirectoryPath)
    
    if os.path.isdir(itemPath):                         # Directory
        # Recursively accept files in directory
        filePaths = findFiles(itemPath)
        for filePath in filePaths:
            acceptItem(filePath, destDirectoryPath, depth+1)
        
        # Remove the directory if it's empty
        try:
            os.rmdir(itemPath)  
        except OSError: 
            pass

    else:                                               # File
        logger.startSection()
        logger.log("Moving: " + quote(itemPath), "Details")
        logger.log("Into directory: " + quote(destDirectoryPath), "Details")
        try:
            shutil.move(itemPath, destDirectoryPath)
        except:
            logger.log("Move failed.", "Errors")
        logger.endSection()
        
    logger.endSection()


def rejectItem(itemPath):
    """Move a file or directory to the REJECTS folder."""

    logger.startSection()
    logger.log("Rejecting %s." % quote(itemPath), "Actions")
    moveWithContext(itemPath, configuration.PATHS["REJECTS"])
    logger.endSection()


def rejectItems(itemPaths):
    """Move a list of items to the REJECTS folder."""
    
    for itemPath in itemPaths:
        rejectItem(itemPath)


def actuallyDelete(itemPath):
    """Actually delete the item at itemPath."""

    
    if not validatePath(itemPath):
        logger.log("Could not delete %s -- not a valid path." % quote(itemPath), "Failures")
        return
    else:
        logger.log("Actually deleting %s." % quote(itemPath), "Actions")
    logger.startSection()
    
    # Make sure we want to do this
    certainty = raw_input("Are you sure? (y) ")
    if certainty.lower() != "y":
        print "Deletion aborted"
        return

    logger.startSection()
    if os.path.isdir(itemPath):                 # Directory
        try: 
            os.rmdir(itemPath)
        except OSError:                         # TODO: Handle non-empty dirs
            s = "Attempt to delete the folder " + quote(itemPath) + " failed. "
            s += "It's probably not empty."
            logger.log(s, "Errors")
    else:                                       # File
        try: 
            os.remove(itemPath)
        except OSError:
            logger.log("Attempt to delete the file " + quote(itemPath) + " failed.", "Errors")
    logger.endSection()

def deleteItem(itemPath, actuallyDelete=None):
    """Either delete or move to DELETES the file or directory at itemPath.
    
    The deletion method is chosen as follows:
        If the optional actuallyDelete parameter is provided by the caller:
            True will cause the item to actually be deleted.
            False will cause the files to moved the the DELETES folder.
        If actuallyDelete is not provided:
            The global deletion mode stored at configuration.SETTINGS["DELETE"]
            is used, where True and False have the same meanings as above."""

    logger.startSection()
    logger.log("Deleting %s." % quote(itemPath), "Actions")
    
    if actuallyDelete is None: 
        actuallyDelete = configuration.SETTINGS["DELETE"]
        
    if actuallyDelete:
        actuallyDelete(itemPath)                
    else:
        moveWithContext(itemPath, configuration.PATHS["DELETES"])
    logger.endSection()
                
def deleteItems(itemPaths, actuallyDelete=None):
    """Either delete or move to DELETES a list of items.
    
    This function calls deleteItem. See that function's documentation for the
    meaning of actuallyDelete and how the deletion method is chosen."""
    
    for itemPath in itemPaths:
        deleteItem(itemPath, actuallyDelete)


#-------------------------------------------
# Path and file functions
#-------------------------------------------

def getDirectoriesAndFiles(directoryPath):
    """Return a list of subdirectory paths and a dict of file paths by type."""

    ls = os.listdir(directoryPath)
    ls.sort()
    
    #filePaths = []
    subdirectoryPaths = []
    filePathsByType = {}
    
    for entry in ls:
        itemPath = os.path.join(directoryPath, entry)
        if os.path.isdir(itemPath):
            subdirectoryPaths.append(itemPath)
        elif os.path.isfile(itemPath):
            #filePaths.append(itemPath)
            fileType = configuration.extToType.get(ext(entry), "other")
            filePathsByType.setdefault(fileType, []).append(itemPath)
            
    return subdirectoryPaths, filePathsByType

def moveDiscsIntoFolders(discContents):
    """Create disc directories; move files into directories.
    
    Takes a list of lists of paths. Each sublist contains the paths of the
    files that should be moved into that disc directory. The lists should be
    in order."""

    directoryPath = os.path.dirname(discContents[0][0])
    numDiscs = len(discContents)
    numDigits = int(log10(numDiscs)+1)  # In case there are 10 (or more) discs
    
    for i in range(numDiscs):
        # Create disc directory
        discDirectoryName = "Disc " + str(i+1).rjust(numDigits, "0")
        discDirectoryPath = os.path.join(directoryPath, discDirectoryName)
        logger.log("Creating %s." % quote(discDirectoryPath), "Details")
        os.mkdir(discDirectoryPath)
        
        # Move files into disc directory
        for filePath in discContents[i]:
            newFilePath = filePath.replace(directoryPath, discDirectoryPath)
            logger.log("Moving %s to %s." % (quote(filePath), quote(newFilePath)), "Details")
            shutil.move(filePath, newFilePath)

def validatePath(itemPath, isDirectory=False, isFile=False):
    """Ensure the path exists and, if specified, is a file or directory."""

    logger.startSection()
    if not os.path.exists(itemPath):
        logger.log(quote(itemPath) + " does not exist or cannot be accessed.", "Failures")
        logger.endSection()
        return False
    elif isDirectory and not os.path.isdir(itemPath):
        logger.log(quote(itemPath) + " is not a directory.", "Failures")
        logger.endSection()
        return False
    elif isFile and not os.path.isfile(itemPath):
        logger.log(quote(itemPath) + " is not a file", "Failures")
        logger.endSection()
        return False
    else:
        return True

def filePathsByExt(filePaths):
    """Take a list of file paths; return a dictionary of extensions to paths."""
    
    filePathsByExt = {}
    for filePath in filePaths:
        filesByExt.setDefault(ext(filePath), []).append(filePath)
    return filePathsByExt

def findFiles(directoryPath):
    """Take a directory path and return a list of the file paths."""
    
    filePaths = []
    ls = os.listdir(directoryPath)
    ls.sort()
    for entry in ls:
        filePath = os.path.join(directoryPath, entry)
        if os.path.isfile(filePath):
            filePaths.append(filePath)
    return filePaths

def containingDir(filePath):
    """Return the name of the directory which contains filePath."""
    
    dirPath = os.path.dirname(filePath)
    dirName = os.path.split(dirPath)[1]
    return dirName

#-------------------------------------------
# Tagging functions
#-------------------------------------------

def isDate(date):
    if date < 1600 or date > datetime.date.today().year + 1:
        return False
    else:
        return True

def isTrackNumber(number):
    if number < 1 or number > 99:
        return False
    else:
        return True


