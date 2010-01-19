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

"""Extraction support for multiple archive formats.

This is file provides one function, extract, which takes a list of archive
paths and attempts to extract each. This function is called in traverse
if any archives are found in a directory.

The currently supported formats are: zip, rar, tar, gzip, bzip2, and ace."""

import os
import subprocess

import etc.functions
import etc.logger
from etc.utils import *

extractorCommands = {".zip": ['unzip', '$a', '-d', '$d'],
                     ".rar": ['unrar', 'x', '$a', '$d'],
                     ".tar": ['tar', '-xf', '$a', '$d'],
                     ".gz" : ['tar', '-zxf', '$a', '$d'],
                     ".bz2": ['tar', '-jxf', '$a', '$d'],
                     ".ace": ['unace', 'x', '-y', '$a', '$d/']}

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
        for (i, arg) in enumerate(command):
            if arg == "$a":
                command[i] = archivePath
            elif arg == "$d":
                command[i] = destDirectoryPath
        
        logger.log("Attempting to extract %s." % quote(os.path.basename(archivePath)), "Details")
        logger.startSection()
        logger.log(" ".join(command), "Commands")
        
        p = subprocess.Popen(command)
        p.wait()
        
        if p.returncode != 0:
            logger.log("Unable to extract " + quote(archivePath), "Errors")
            functions.deleteItem(destDirectoryPath)
            functions.rejectItem(archivePath)
        else:
            logger.log("Extraction succeeded.", "Successes")
            functions.deleteItem(archivePath)
            
        logger.endSection()
