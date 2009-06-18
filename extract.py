# -*- coding: utf-8 -*-

"""Extraction support for multiple archive formats.

This is file provides one function, extract, which takes a list of archive
paths and attempts to extract each. This function is called in traverse
if any archives are found in a directory.

The currently supported formats are: zip, rar, tar, gzip, bzip2, and ace."""

import os

import functions
from functions import ext
from functions import quote
from LogFrame import log

extractorCommands = {".zip": 'unzip "$a" -d "$d"',
                     ".rar": 'unrar x "$a" "$d"',
                     ".tar": 'tar -xf "$a" "$d"',
                     ".gz" : 'tar -zxf "$a" "$d"',
                     ".bz2": 'tar -jxf "$a" "$d"',
                     ".ace": 'unace x -y "$a" "$d/"'}

def extract(archivePaths):
    """Extract archives using appropriate utility.
    
    Takes a list of paths to archives and for each:
    Creates a directory with the same name as the archive, without extension.
    Chooses the utility to use for extraction based on the archive's extension.
    Attempts to extract the archive into the newly created directory.
    If the extraction fails, the directory is deleted and the archive rejected.
    If the extraction succeeds, the archive is discarded."""
    
    for archivePath in archivePaths:
        destDirectoryPath = os.path.splitext(archivePath)[0]
        if not os.path.exists(destDirectoryPath):
            os.mkdir(destDirectoryPath)   
        
        command = extractorCommands[ext(archivePath)]
        command = command.replace("$a", archivePath)
        command = command.replace("$d", destDirectoryPath)
        log("Attempting to extract " + quote(os.path.basename(archivePath)), 3, "Details")
        log(command, 4, "Commands")
        result = os.system(command)
        
        if result != 0:
            log("Unable to extract " + quote(archivePath), 4, "Errors") 
            functions.deleteItem(destDirectoryPath)
            functions.rejectItem(archivePath)
        else:
            log("Extraction succeeded.", 4, "Successes")
            functions.deleteItem(archivePath)
