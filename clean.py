# -*- coding: utf-8 -*-

"""Functions to apply filename standards and to handle images and misc files.

This file has two main purposes: to handle images and miscellaneous files and 
to apply filename conventions to audio files. The only convention applied
currently is to lowercase all file extensions but another high priority
feature to add is changing filenames which use periods or underscores in place
of spaces to use spaces instead."""

import os
import re
import shutil

import configuration
import functions
import logger
from utils import *

def handleImages(imagePaths):
    """Delete or rename images based on quantity.
    
    If there is one image, it will be renamed to cover.[ext].
    If there is more than one image, they will all be deleted."""
    
    if len(imagePaths) == 1:
        imagePath = imagePaths[0]
        imageName = os.path.basename(imagePath)
        root, ext = os.path.splitext(imageName)
        shutil.move(imagePath, imagePath.replace(root, "cover"))
    else:
        functions.deleteItems(imagePaths)

def cleanDir(filePaths):
    """Delete miscellaneous files."""
    
    functions.deleteItems(filePaths)
            
def standardizeFilenames(itemPaths, rename=True):
    """Take file or dir paths; rename them to meet standards; return new paths.
    
    The current standards being enforced in order of appearance:
        Spaces - not underscores or periods - should separate words.
        Filenames should contain no special characters.
        There should never be more than one consecutive space.
        Filenames should not begin or end in a space.
        All extensions should be lowercase.
    
    The only part of the process that is not very straight-forward is replacing
    underscores and periods with spaces. In particular, determining whether to 
    replace periods is more complicated because periods are acceptable in 
    acronyms, ellipses, etc.
    
    Here is the current method for handling this: 
    Determine whether we have an acronym by splitting the root by the period
    char, then checking if each substring is of length one (with the possible 
    exception of the last substring which will be empty if the root ends in a 
    period). If not, we then replace each "lone period" (a period not preceded
    or followed by another period) with a space."""
    
    for (i, itemPath) in enumerate(itemPaths):
        directoryPath, itemName = os.path.split(itemPath)
        root, extension = os.path.splitext(itemName)
        if not extension.lower() in configuration.typeToExts["good_audio"]:
            root += extension
            extension = ""
        
        if not " " in root:
            if "_" in root:
                root = root.replace("_", " ")
            elif "." in root:
                split = root.split(".")
                if not split[-1]: split.pop()
                if not all([len(substring) == 1 for substring in split]):
                    lonePeriodRegex = r"(?<!\.)\.(?!\.)"
                    root = " ".join(re.split(lonePeriodRegex, root))
        
        root = functions.restrictChars(root)
        root = re.sub(" {2,}", " ", root)   # Replace 2 or more spaces with 1
        root = root.strip()
        
        newItemName = root + extension.lower()
        newItemPath = os.path.join(directoryPath, newItemName)
        if newItemPath != itemPath:
            logger.log("Renaming %s to %s." % (quote(itemName), quote(newItemName)), "Debugging")
            if rename: shutil.move(itemPath, newItemPath)
            itemPaths[i] = newItemPath
            
    return itemPaths
