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

"""Functions to apply filename standards and to handle images and misc files.

This file has two main purposes: to handle images and miscellaneous files and 
to apply filename conventions to audio files. The only convention applied
currently is to lowercase all file extensions but another high priority
feature to add is changing filenames which use periods or underscores in place
of spaces to use spaces instead."""

import os
import re
import shutil

from etc import configuration
from etc import functions
from etc.utils import *
from etc.logger import log, logfn, logSection

@logfn('\nRenaming cover image to "cover" and deleting other images.')
def handleImages(imagePaths):
    """Delete or rename images based on quantity.
    
    If there is one image, it will be renamed to cover.[ext].
    If there is more than one image, they will all be deleted."""
    
    if len(imagePaths) == 1:
        makeImageCover(imagePaths[0])
    else:
        # Look for "front" in image name. If there is only one "front",
        # that is the cover. Otherwise we can't decide.
        nonfronts = [ip for ip in imagePaths 
                     if not "front" in os.path.basename(ip).lower()]        
        functions.deleteItems(nonfronts)
        
        fronts = [ip for ip in imagePaths 
                  if "front" in os.path.basename(ip).lower()]
        if len(fronts) == 1:
            makeImageCover(fronts[0])
        else:
            functions.deleteItems(fronts)

def makeImageCover(imagePath):
    """Rename the given image to cover.[ext]."""
    
    dirPath, name = os.path.split(imagePath)
    root, ext = os.path.splitext(name)
    shutil.move(imagePath, os.path.join(dirPath, "cover" + ext))
        
@logfn("\nDeleting miscellaneous files.")
def cleanDir(filePaths):
    """Delete miscellaneous files."""
    
    functions.deleteItems(filePaths)

@logfn("\nCleaning up filenames.")
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
        
        root = re.sub(" {2,}", " ", root)   # Replace 2 or more spaces with 1
        root = root.strip()
        
        newItemName = root + extension.lower()
        newItemPath = os.path.join(directoryPath, newItemName)
        if newItemPath != itemPath:
            log("Renaming %s to %s." % (quote(itemName), quote(newItemName)))
            if rename: shutil.move(itemPath, newItemPath)
            itemPaths[i] = newItemPath
            
    return itemPaths


def canonicalName(name):
"""Rules:

==Featuring==
All equal:
    "Song"
    "Song ft Artist"
    "Song ft. Artist"
    "Song feat Artist"
    "Song feat. Artist"
    "Song featuring Artist"
    "Song (ft Artist)"
    "Song (ft. Artist)"
    "Song (feat Artist)"
    "Song (feat. Artist"
    "Song (featuring Artist)" 
    "Song Ft Artist"
    "Song Ft. Artist"
    "Song Feat Artist"
    "Song Feat. Artist"
    "Song Featuring Artist"
    "Song (Ft Artist)"
    "Song (Ft. Artist)"
    "Song (Feat Artist)"
    "Song (Feat. Artist"
    "Song (Featuring Artist)" 
Canonical:
    "Song (feat. Artist)"
Note:
    The featuring section of song title is optional. It's inclusion is 
inconsistent so not having the featuring section should not cause track to be 
rejected. 

==Part X==
All equal:
    "Song part 1"
    "Song part I"
    "Song part one"
    "Song Part 1"
    "Song Part I"
    "Song Part one"
    "Song (part 1)"
    "Song (part I"
    "Song (part one)"
    "Song (Part 1)"
    "Song (Part I)"
    "Song (Part one)"
    "Song [part 1]"
    "Song [part I"
    "Song [part one]"
    "Song [Part 1]"
    "Song [Part I]"
    "Song [Part one]"
    "Song, part 1"
    "Song, part I"
    "Song, part one"
    "Song, Part 1"
    "Song, Part I"
    "Song, Part one"
Canonical:
    "Song, Part 1"
Notes:
    All other numbers are, of course, all right.
    TODO: Consider allowing "Part X of Y" 

==Multi-Part Titles==
All equal:
    "Song A/Song B"
    "Song A / Song B"
    "Song A-Song B"
    "Song A - Song B"
Canonical:
    "Song A / Song B"

==EP==
All equal:
    "Release"
    "Release ep"
    "Release (ep)"
    "Release [ep]"
    "Release EP"
    "Release (EP)"
    "Release [EP]"
Canonical:
    "Release" 

==Single==
All equal:
    "Release"
    "Release single"
    "Release (single)"
    "Release [single]"
    "Release Single"
    "Release (Single)"
    "Release [Single]"
Canonical:
    "Release" 

==Soundtrack Releases==
All equal:
    "Release"
    "Release OST"
    "Release (OST)"
    "Release [OST]"
    "Release Soundtrack"
    "Release (Soundtrack)"
    "Release [Soundtrack]"
Canonical:
    "Release" ??

==Special Characters==
Special/foreign characters are preferred but not required.

==Capitalization==
TODO!!

==Etc==
- "and", "&", and "+" are equivalent; "and" is preferred
- Most messages in parentheses or square brackets at the end of titles are optional; TODO: Clarify
  - "(Live)" and "(Remix)" are required
  - "(Original Mix)" and its ilk are definitely not required, possible dispreferred
- TODO: Commas in lists and other places
- TODO: Backticks and weird quotes become apostrophes 
- TODO: Question marks?

"""
