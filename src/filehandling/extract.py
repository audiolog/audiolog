# -*- coding: utf-8 -*-

#  Audiolog Music Organizer
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

from etc import functions
from etc.utils import *
from etc.logger import log, logfn, logSection

extractorCommands = {".zip": ['unzip', '$a', '-d', '$d'],
                     ".rar": ['unrar', 'x', '$a', '$d'],
                     ".tar": ['tar', '-xf', '$a', '$d'],
                     ".gz" : ['tar', '-zxf', '$a', '$d'],
                     ".bz2": ['tar', '-jxf', '$a', '$d'],
                     ".ace": ['unace', 'x', '-y', '$a', '$d/']}

@logfn("\nExtracting archives.")
def extract(archivePaths):
    """Extract archives using appropriate utility.
    
    Takes a list of paths to archives and for each:
    Creates a directory with the same name as the archive, without extension.
    Chooses the utility to use for extraction based on the archive's extension.
    Attempts to extract the archive into the newly created directory.
    If the extraction fails, the directory is deleted and the archive rejected.
    If the extraction succeeds, the archive is discarded."""
    
    for archivePath in archivePaths:
        fileName = os.path.basename(archivePath)
        with logSection("Attempting to extract %s." % quote(fileName)):
            destDirectoryPath, ext = os.path.splitext(archivePath)
            if not os.path.exists(destDirectoryPath):
                os.mkdir(destDirectoryPath)   
            
            command = extractorCommands[ext.lower()][:]
            for (i, arg) in enumerate(command):
                if arg == "$a":
                    command[i] = archivePath
                elif arg == "$d":
                    command[i] = destDirectoryPath
            
            log(" ".join(command))
            
            p = subprocess.Popen(command)
            p.wait()
            
            if p.returncode != 0:
                log("Unable to extract %s." % quote(archivePath))
                functions.deleteItem(destDirectoryPath)
                functions.rejectItem(archivePath)
            else:
                log("Extraction succeeded.")
                functions.deleteItem(archivePath)
