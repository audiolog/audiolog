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

"""A collection of commonly used functions.

This file contains functions which are not specific to one step of the handling
process but are used throughout. There are two main categories of functions
present: moving functions (such as acceptItem, rejectItem and deleteItem) and 
path functions (such as validatePath and getFilePathsByType)."""

import os
import shutil
import subprocess
import string
import datetime

import configuration as conf
from utils import *
from logger import log, logfn, logSection

#-------------------------------------------
# Accepting, rejecting and deleting functions
#-------------------------------------------

@logfn("Moving with context {quote(currentItemPath)}.")
def moveWithContext(currentItemPath, destDirectoryPath):
    """Recreate full path relative to configuration.CURRENT in destDirectoryPath.
    
    Example:
    Current folder being scanned: "/media/Ext/Download/"
    Current file: "/media/Ext/Download/Rock/College Rock/Morrissey/disco.rar" 
    Destination directory: REJECTS folder "/media/Ext/Rejects/"
    Final path: "/media/Ext/Rejects/Rock/College Rock/Morissey/disco.rar" """

    if not validatePath(currentItemPath):
        log("Could not move with context %s -- not a valid path." % 
            quote(currentItemPath))
        return
        
    newItemPath = currentItemPath.replace(conf.PATHS["CURRENT"], 
                                          destDirectoryPath)
    newDirectoryPath = os.path.dirname(newItemPath)
    
    if not os.path.exists(newDirectoryPath):
        os.makedirs(newDirectoryPath)
    
    if not os.path.exists(newItemPath):
        log("Moving to %s." % quote(newItemPath))
        shutil.move(currentItemPath, newItemPath)
    else:
        log("Could not move. Destination %s already exists." % 
            quote(newItemPath))
    
    removeDirIfEmpty(os.path.dirname(currentItemPath))
    
@logfn("Accepting {quote(itemPath)}.")
def acceptItem(itemPath, destDirectoryRelPath):
    """Move a file or directory to the SORTED folder.
    
    Parameters:
        itemPath can point to a file or directory.
        destDirectoryRelPath is a path relative to the SORTED directory.
        depth is provided only when the function recursively calls itself."""

    # Create destination directory
    destDirectoryPath = os.path.join(conf.PATHS["SORTED"], destDirectoryRelPath)
    if not os.path.exists(destDirectoryPath):
        os.makedirs(destDirectoryPath)
    
    if os.path.isdir(itemPath):                         # Directory
        # Recursively accept items in this directory.
        for itemName in os.listdir(unicode(itemPath)):
            acceptItem(os.path.join(itemPath, itemName), destDirectoryRelPath)  
        removeDirIfEmpty(itemPath)

    else:                                               # File
        itemName = os.path.basename(itemPath)
        log("Moving %s into %s." % (quote(itemName), quote(destDirectoryPath)))
        try:
            shutil.move(itemPath, destDirectoryPath)
        except:
            log("Move failed.")


@logfn("Rejecting {quote(itemPath)}.")
def rejectItem(itemPath):
    """Move a file or directory to the REJECTS folder."""

    rejectsPath = os.path.join(conf.PATHS["CURRENT"], "Audiolog_Rejects")
    moveWithContext(itemPath, rejectsPath)

def rejectItems(itemPaths):
    """Move a list of items to the REJECTS folder."""
    
    for itemPath in itemPaths:
        rejectItem(itemPath)

@logfn("Actually deleting {quote(itemPath)}.")
def actuallyDelete(itemPath):
    """Actually delete the item at itemPath."""
    
    if not validatePath(itemPath):
        log("Could not delete %s -- not a valid path." % quote(itemPath))
        return

    if os.path.isdir(itemPath):                 # Directory
        if not removeDirIfEmpty(itemPath):
            # TODO: Handle non-empty dirs.
            s = "Attempt to delete the folder %s failed. " % quote(itemPath)
            s += "It's probably not empty."
            log(s)
    else:                                       # File
        try: 
            os.remove(itemPath)
        except OSError:
            log("Attempt to delete the file %s failed." % quote(itemPath))

@logfn("Removing {quote(itemPath)}.")
def deleteItem(itemPath, actuallyDeleteFlag=None):
    """Either delete or move to DELETES the file or directory at itemPath.
    
    The deletion method is chosen as follows:
        If the optional actuallyDelete parameter is provided by the caller:
            True will cause the item to actually be deleted.
            False will cause the files to moved the the DELETES folder.
        If actuallyDelete is not provided:
            The global deletion mode stored at configuration.SETTINGS["DELETE"]
            is used, where True and False have the same meanings as above."""

    if actuallyDeleteFlag is None:
        actuallyDeleteFlag = conf.SETTINGS["DELETE"]
        
    if actuallyDeleteFlag:
        actuallyDelete(itemPath)
    else:
        deletesPath = os.path.join(conf.PATHS["CURRENT"], "Audiolog_Deletes")
        moveWithContext(itemPath, deletesPath)
                
def deleteItems(itemPaths, actuallyDelete=None):
    """Either delete or move to DELETES a list of items.
    
    This function calls deleteItem. See that function's documentation for the
    meaning of actuallyDelete and how the deletion method is chosen."""
    
    for itemPath in itemPaths:
        deleteItem(itemPath, actuallyDelete)


#-------------------------------------------
# Path functions
#-------------------------------------------

def getValidSubdirectories(directoryPath):
    """Return a list paths to directories inside the given directory.
    
    This function filters out Audiolog system folders (rejects and deletes)
    that we should not attempt to traverse and sort."""
    
    paths = sorted([os.path.join(directoryPath, name) 
                    for name in os.listdir(unicode(directoryPath))])
    return [path for path in paths 
            if (os.path.isdir(path) and "Audiolog_" not in path)]
    

def getFilePathsByType(directoryPath):
    """Return a list of subdirectory paths and a dict of file paths by type."""
    
    if not validatePath(directoryPath, isDirectory=True):
        return {}

    filePathsByType = {}
    for entry in sorted(os.listdir(unicode(directoryPath))):
        itemPath = os.path.join(directoryPath, entry)
        if os.path.isfile(itemPath):
            fileType = conf.extToType.get(ext(entry), "other")
            filePathsByType.setdefault(fileType, []).append(itemPath)     
    return filePathsByType

def validatePath(itemPath, isDirectory=False, isFile=False):
    """Ensure the path exists and, if specified, is a file or directory."""
    
    result = False
    if not os.path.exists(itemPath):
        log(quote(itemPath) + " does not exist or cannot be accessed.")
    elif isDirectory and not os.path.isdir(itemPath):
        log(quote(itemPath) + " is not a directory.")
    elif isFile and not os.path.isfile(itemPath):
        log(quote(itemPath) + " is not a file.")
    else:
        result = True
        
    return result

def containingDir(filePath):
    """Return the name of the directory which contains filePath."""
    
    dirPath = os.path.dirname(filePath)
    dirName = os.path.split(dirPath)[1]
    return dirName


#-------------------------------------------
# Default path functions (used for initial configuration)
#-------------------------------------------

def getDefaultSortedPath(localOS):
    if localOS == "Windows":
        return os.path.expanduser(os.path.join("~", "My Documents", "My Music"))
    else:
        return os.path.expanduser(os.path.join("~", "Music"))
    
def getDefaultToScanPath(localOS):
    if localOS == "Windows":
        return os.path.expanduser(os.path.join("~", "My Documents", "Downloads"))
    else:
        return os.path.expanduser(os.path.join("~", "Downloads"))

#-------------------------------------------
# File functions
#-------------------------------------------

@logfn("Moving each cue/audio pair into its own folder.")
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
        discDirectoryName = "Disc " + str(i+1).zfill(numDigits)
        discDirectoryPath = os.path.join(directoryPath, discDirectoryName)
        log("Creating %s." % quote(discDirectoryPath))
        os.mkdir(discDirectoryPath)
        
        # Move files into disc directory
        for filePath in discContents[i]:
            newFilePath = filePath.replace(directoryPath, discDirectoryPath)
            log("Moving %s to %s." % (quote(filePath), quote(newFilePath)))
            shutil.move(filePath, newFilePath)
            
def removeDirIfEmpty(dirPath):
    """Delete the directory if it's empty."""
    
    try:
        os.rmdir(dirPath)  
    except OSError: 
        return False
    else:
        return True


#-------------------------------------------
# Tagging functions
#-------------------------------------------

def isDate(date):
    """Return true if between 1600 and current year + 1, inclusive."""

    if date < 1600 or date > datetime.date.today().year + 1:
        return False
    else:
        return True

def isTrackNumber(number):
    """Return true if between 1 and 99, inclusive."""
    
    if number < 1 or number > 99:
        return False
    else:
        return True
