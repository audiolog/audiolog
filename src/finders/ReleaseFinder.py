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

import os
import re

from metadata import tagging
from metadata import getters
from etc import logger
from etc import functions

from AbstractFinder import AbstractReleaseFinder
from AbstractFinder import FilepathString

class ReleaseFinder(AbstractReleaseFinder):
    """Gatherer of release data from all available sources.

    Applicable known data:
    - Artist
    - Date
    - Track total
    - Titles
    """
        
    fieldName = "release"
        
    def __init__(self):
        self.getters = [(self.getTag, 1),                   # In AbstractFinder
                        (self.getMBTag, 3),                 # In AbstractFinder
                        (self.getMBKnownData, 3),
                        (self.getMBTagWithKnownData, 4),
                        (self.getMBFilename, 2),
                        (self.getMBFilenameWithKnownData, 3.5)]
    
    def getMBKnownData(self, track):
        """Query MB using known data.
        
        To find a date we...
            Need: Artist AND (Date OR Titles)
            Can Use: Tracktotal"""
        
        logger.log("Searching for release in MusicBrainz using the currently known data.", "Actions")
        logger.startSection()
        
        if not (("artist" in track.metadata) and
                ("date" in track.metadata or "title" in track.metadata)):
            logger.log("Attempt failed because our currently known data does not include the fields we need -- the artist AND the (date OR track titles).", "Failures")
            result = None
        else:
            result = getters.mbInterface(self.fieldName, None, track, ["artist", "date", "tracks", "tracktotal"])
        
        logger.endSection()
        return result
    
    def getMBTagWithKnownData(self, track):
        """Query MB using known data and the current tag."""
        
        logger.log("Attempting to match the current release tag value with MusicBrainz using the currently known data.", "Actions")
        logger.startSection()
        
        releaseTag = tagging.getTag(track.filePath, "release")
        
        if not releaseTag:
            logger.log("Attempt failed because current tag is empty.", "Failures")
            result = None
        elif not ("artist" in track.metadata or
                  "date" in track.metadata or
                  "title" in track.metadata):
            logger.log("Attempt failed because our currently known data does not include the fields we need -- the artist or the date or the track titles.", "Failures")
            result = None
        else:
            result = getters.mbInterface(self.fieldName, releaseTag, track, ["artist", "date", "tracks", "tracktotal"])
        
        logger.endSection()
        return result

    def getMBFilename(self, track):
        """Attempt to fuzzily match release name from filepath using MusicBrainz.
        
        We look for the release name in the folder and file name."""
        
        folderFilePath = self.getFilenameForMB(track)
        logger.log("Attempting to match the filepath with MusicBrainz.", "Actions")
        logger.startSection()
        result = getters.mbInterface(self.fieldName, folderFilePath, track)
        logger.endSection()
        return result

    def getMBFilenameWithKnownData(self, track):
        """Attempt to fuzzily match release name from filepath using MusicBrainz.
       
        We look for the release name in the folder and file name."""
        
        logger.log("Attempting to match the filepath release tag value with MusicBrainz using the currently known data.", "Actions")
        logger.startSection()
        
        if not ("artist" in track.metadata or
                "date" in track.metadata or
                "title" in track.metadata):
            logger.log("Attempt failed because our currently known data does not include the fields we need -- the artist or the date or the track titles.", "Failures")
            result = None
        else:
            folderFilePath = self.getFilenameForMB(track)
            result = getters.mbInterface(self.fieldName, folderFilePath, track, ["artist", "date", "tracks", "tracktotal"])
        
        logger.endSection()
        return result
    
    def getFilenameForMB(self, track):
    
        folderFilePath = os.path.join(functions.containingDir(track.filePath), track.fileName)
        folderFilePath = os.path.splitext(folderFilePath)[0]
        
        folderFilePath = FilepathString(folderFilePath)
        
        if "date" in track.metadata: # If we know the date, try to remove it...
            date = track.metadata["date"]
            folderFilePath = folderFilePath.replace(date, "")
        else: # ...otherwise just remove the leftmost four digits.
            match = re.findall("\d{4}", folderFilePath)
            if match:
                folderFilePath = folderFilePath.replace(match[0], "")
                
        return folderFilePath
