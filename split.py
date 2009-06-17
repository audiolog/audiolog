"""Support for splitting audio in which one disc of audio is in one file.

This file provides functions to split audio in one of two ways: based on a CUE
file or a wrapped audio file (AlbumWrap or MP3Wrap).
If there is one or more cues in a directory split is called to attempt to match
the cues to audio files and then to split them using the *nix command-line 
program mp3splt."""

import os
import shutil
from math import log10

import functions
from functions import quote
from LogFrame import log

def split(cuePaths, audioFilePaths):
    """Split audio files based on cue files.
    
    Takes a list of cue paths and a list of audio file paths.
    Rejects the folder if there are inequal numbers of audio and cue files.
    If there is one cue/audio pair, it is split using mp3splt. 
    If there are multiple pairs, they are moved into their own folders."""
    
    numCues = len(cuePaths)
    directoryPath = os.path.dirname(cuePaths[0])
    
    if numCues != len(audioFilePaths):
        log("There are unequal numbers of cues and audio files in " + quote(directoryPath), 3, "Errors")
        functions.rejectItem(directoryPath)
        return

    if numCues == 1:
        log("Splitting " + quote(os.path.basename(audioFilePaths[0])) + " based on " + quote(os.path.basename(cuePaths[0])), 3, "Details")
        splitCommand = 'mp3splt -d "%s" -c "%s" "%s"' % (directoryPath, cuePaths[0], audioFilePaths[0])
        log(splitCommand, 4, "Commands")
        result = os.system(splitCommand)        
        if result == 0:
            log("Successfully split " + quote(audioFilePaths[0]), 4, "Successes")
            functions.deleteItem(cuePaths[0])
            functions.deleteItem(audioFilePaths[0])
        else:
            log("Unable to split " + quote(audioFilePaths[0]), 4, "Failures")
            functions.rejectItem(cuePaths[0])
            functions.rejectItem(audioFilePaths[0])
                           
    else: 
        log("Multiple cue/audio pairs in " + quote(directoryName), 3, "Details")
        pairs = [(audioFilePaths[i], cuePaths[i]) for i in range(numCues)]
        functions.moveDiscsIntoFolders(pairs)

def unwrap(audioFilePaths):
    """Attempt to split possible AlbumWrap or MP3Wrap audio files.
    
    Takes a list of paths to audio files which are suspected to be AlbumWrap 
    or MP3Wrap files but may not be. We attempt to split these files using 
    "mp3splt -w". If this fails then this was not a wrapped file."""
    
    pass
    
    