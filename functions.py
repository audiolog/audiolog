"""A collection of commonly used functions.

This file contains functions which are not specific to one step of the handling
process but are used throughout. There are two main categories of functions
present: moving functions (such as acceptItem, rejectItem and deleteItem) and 
path functions (such as validatePath, filePathsByExt and findFiles)."""

import os
import shutil
import subprocess
import string

import configuration
from LogFrame import log

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
    
    if not validatePath(currentItemPath):
        log("Could not move with context" + quote(currentItemPath) + " -- not a valid path.", -2, "Failures")
        return
    else:
        log("Moving with context" + quote(currentItemPath), -2, "Actions")
    
    newItemPath = currentItemPath.replace(configuration.PATHS["CURRENT"], destDirectoryPath)
    newDirectoryPath = os.path.dirname(newItemPath)
    
    if not os.path.exists(newDirectoryPath):
        os.makedirs(newDirectoryPath)
    
    if not os.path.exists(newItemPath):
        log("Moving to" + quote(newItemPath), -3, "Details")
        shutil.move(currentItemPath, newItemPath)
    else:
        log("Could not move. Destination path " + quote(newItemPath) + " already exists", -3, "Failures")
    
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
    
    log("Accepting " + quote(itemPath), -depth, "Actions")

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
        log("Moving: " + quote(itemPath), -depth-1, "Details")
        log("Into directory: " + quote(destDirectoryPath), -depth-1, "Details")
        try:
            shutil.move(itemPath, destDirectoryPath)
        except:
            log("Move failed.", -depth-1, "Errors")


def rejectItem(itemPath):
    """Move a file or directory to the REJECTS folder."""
    
    log("Rejecting " + quote(itemPath), -1, "Actions")
    moveWithContext(itemPath, configuration.PATHS["REJECTS"])


def rejectItems(itemPaths):
    """Move a list of items to the REJECTS folder."""
    
    for itemPath in itemPaths:
        rejectItem(itemPath)


def actuallyDelete(itemPath):
    """Actually delete the item at itemPath."""
    
    if not validatePath(itemPath):
        log("Could not delete " + quote(itemPath) + " -- not a valid path.", -2, "Failures")
        return
    else:
        log("Actually deleting " + quote(itemPath), -2, "Actions")
    
    # Make sure we want to do this
    certainty = raw_input("Are you sure? (y) ")
    if certainty.lower() != "y":
        print "Deletion aborted"
        return
    
    if os.path.isdir(itemPath):                 # Directory
        try: 
            os.rmdir(itemPath)
        except OSError:                         # TODO: Handle non-empty dirs
            s = "Attempt to delete the folder " + quote(itemPath) + " failed. "
            s += "It's probably not empty."
            log(s, -3, "Errors")
    else:                                       # File
        try: 
            os.remove(itemPath)
        except OSError:
            log("Attempt to delete the file " + quote(itemPath) + " failed.", -3, "Errors")

def deleteItem(itemPath, actuallyDelete=None):
    """Either delete or move to DELETES the file or directory at itemPath.
    
    The deletion method is chosen as follows:
        If the optional actuallyDelete parameter is provided by the caller:
            True will cause the item to actually be deleted.
            False will cause the files to moved the the DELETES folder.
        If actuallyDelete is not provided:
            The global deletion mode stored at configuration.SETTINGS["DELETE"]
            is used, where True and False have the same meanings as above."""
    
    log("Deleting" + quote(itemPath), -1, "Actions")    
    
    if actuallyDelete is None: 
        actuallyDelete = configuration.SETTINGS["DELETE"]
        
    if actuallyDelete:
        actuallyDelete(itemPath)                
    else:
        moveWithContext(itemPath, configuration.PATHS["DELETES"])
                
def deleteItems(itemPaths, actuallyDelete=None):
    """Either delete or move to DELETES a list of items.
    
    This function calls deleteItem. See that function's documentation for the
    meaning of actuallyDelete and how the deletion method is chosen."""
    
    for itemPath in itemPaths:
        deleteItem(itemPath, actuallyDelete)


#-------------------------------------------
# Path and file functions
#-------------------------------------------

def directory(directoryPath):
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
        log("Creating " + quote(discDirectoryPath), -1, "Details")
        os.mkdir(discDirectoryPath)
        
        # Move files into disc directory
        for filePath in discContents[i]:
            newFilePath = filePath.replace(directoryPath, discDirectoryPath)
            log("Moving " + quote(filePath) + " to " + quote(newFilePath), -1, "Details")
            shutil.move(filePath, newFilePath)

def validatePath(itemPath, isDirectory=False, isFile=False):
    """Ensure the path exists and, if specified, is a file or directory."""
    
    if not os.path.exists(itemPath):
        log(quote(itemPath) + " does not exist or cannot be accessed.", -1, "Failures")
        return False
    elif isDirectory and not os.path.isdir(itemPath):
        log(quote(itemPath) + " is not a directory.", -1, "Failures")
        return False
    elif isFile and not os.path.isfile(itemPath):
        log(quote(itemPath) + " is not a file", -1, "Failures")
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
    
def ext(filePath, lower=True):
    """Return the extension of the file path or name, lowercased by default."""
    
    extension = os.path.splitext(filePath)[1]
    if lower: 
        extension = extension.lower()
    return extension

def quote(string):
    """Return the string in quotes.
    
    This is used on file names and paths whenever they are shown to the user."""
    
    return '"%s"' % string
    
def aboutEqual(str1, str2):
    """Return True if the strings are nearly or exactly equal, else False.
    
    To do this we lowercase both strings, strip them of punctuation and
    whitespace, then compare for equality."""
        
    str1 = restrictChars(str1.lower(), True, True, False, False)
    str2 = restrictChars(str2.lower(), True, True, False, False)
    
    return str1 == str2
    
def restrictChars(s, letters=True, digits=True, whitespace=True, punctuation=True, custom=None):
    """Take a string and return that string stripped of all non-valid characters.
    
    This function is called before queries to MusicBrainz because MB barfs
    when fed weird characters."""
    
    validChars = ""
    if letters: validChars += string.letters
    if digits: validChars += string.digits
    if whitespace: validChars += string.whitespace
    if punctuation: validChars += string.punctuation
    if custom: validChars += custom

    t = ""
    for ch in s:
        if ch in validChars:
            t += ch
    
    return t
    
    