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

"""Support for splitting audio in which one disc of audio is in one file.

This file provides functions to split audio in one of two ways: based on a CUE
file or a wrapped audio file (AlbumWrap or MP3Wrap).
If there is one or more cues in a directory split is called to attempt to match
the cues to audio files and then to split them using the *nix command-line 
program mp3splt."""

import os
import shutil
import subprocess
from math import log10

import etc.functions
import etc.logger
from etc.utils import *

def split(cuePaths, audioFilePaths):
    """Split audio files based on cue files.
    
    Takes a list of cue paths and a list of audio file paths.
    Rejects the folder if there are inequal numbers of audio and cue files.
    If there is one cue/audio pair, it is split using mp3splt. 
    If there are multiple pairs, they are moved into their own folders."""
    
    numCues = len(cuePaths)
    directoryPath = os.path.dirname(cuePaths[0])
    
    if numCues != len(audioFilePaths):
        logger.log("There are unequal numbers of cues and audio files in %s." % quote(directoryPath), "Errors")
        functions.rejectItem(directoryPath)
        return

    if numCues == 1:
        cuePath = cuePaths[0]
        audioFilePath = audioFilePaths[0]
        
        logger.log("Splitting %s based on %s." % (quote(os.path.basename(audioFilePath)), quote(os.path.basename(cuePath))), "Details")
        logger.startSection()
        
        splitCommand = ['mp3splt', '-d', directoryPath, '-c', cuePath, audioFilePath]
        logger.log(" ".join(splitCommand), "Commands")
        
        p = subprocess.Popen(splitCommand)
        p.wait()

        if p.returncode == 0:
            logger.log("Successfully split %s." % quote(audioFilePath), "Successes")
            logger.startSection()
            functions.deleteItem(cuePath)
            functions.deleteItem(audioFilePath)

        else:
            logger.log("Unable to split %s." % quote(audioFilePath), "Failures")
            logger.startSection()
            functions.rejectItem(cuePath)
            functions.rejectItem(audioFilePath)
            
        logger.endSection(2)
                           
    else: 
        logger.log("Multiple cue/audio pairs in %s." % quote(directoryName), "Details")
        logger.log("Moving each pair into its own folder.", "Details")
        pairs = [(audioFilePaths[i], cuePaths[i]) for i in range(numCues)]
        logger.startSection()
        functions.moveDiscsIntoFolders(pairs)
        logger.endSection()

def unwrap(audioFilePaths):
    """Attempt to split possible AlbumWrap or MP3Wrap audio files.
    
    Takes a list of paths to audio files which are suspected to be AlbumWrap 
    or MP3Wrap files but may not be. We attempt to split these files using 
    "mp3splt -w". If this fails then this was not a wrapped file."""
    
    pass
    
    