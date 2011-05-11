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

import os
import re

from metadata import tagging
from metadata import musicbrainz as mb
from etc import functions
from etc.logger import log, logfn, logSection
from etc.utils import *

from AbstractFinder import AbstractReleaseFinder

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
    
    @logfn("Searching MusicBrainz with the currently known data.")
    def getMBKnownData(self, track):
        """Query MB using known data.
        
        To find a date we...
            Need: Artist AND (Date OR Titles)
            Can Use: Tracktotal"""
        
        if not (("artist" in track.metadata) and
                ("date" in track.metadata or "title" in track.metadata)):
            log("The currently known data does not include the fields we need --"
                " the artist and the (date or track titles).")
            result = None
            
        else:
            result = mb.askMB(self.fieldName, None, track, 
                              ["artist", "date", "tracks", "tracktotal"])
        
        return result
    
    @logfn("Matching the current tag value with MusicBrainz using known data.")
    def getMBTagWithKnownData(self, track):
        """Query MB using known data and the current tag."""
                
        releaseTag = tagging.getTag(track.filePath, "release")
        
        if not releaseTag:
            log("The current tag is empty.")
            result = None
            
        elif not ("artist" in track.metadata or
                  "date" in track.metadata or
                  "title" in track.metadata):
            log("The currently known data does not include the fields we need --"
                " the artist or the date or the track titles.")
            result = None
            
        else:
            result = mb.askMB(self.fieldName, releaseTag, track, 
                              ["artist", "date", "tracks", "tracktotal"])
        
        return result

    @logfn("Matching the filepath to a MusicBrainz release.")
    def getMBFilename(self, track):
        """Attempt to fuzzily match release name from filepath using MusicBrainz.
        
        We look for the release name in the folder and file name."""
        
        folderFilePath = self.getFilenameForMB(track)
        return mb.askMB(self.fieldName, folderFilePath, track)

    @logfn("Matching the filepath to a MusicBrainz release using known data.")
    def getMBFilenameWithKnownData(self, track):
        """Attempt to fuzzily match release name from filepath using MusicBrainz.
       
        We look for the release name in the folder and file name."""
        
        if not ("artist" in track.metadata or
                "date" in track.metadata or
                "title" in track.metadata):
            log("The currently known data does not include the fields we need --"
                " the artist or the date or the track titles.")
            result = None
            
        else:
            folderFilePath = self.getFilenameForMB(track)
            result = mb.askMB(self.fieldName, folderFilePath, track, 
                              ["artist", "date", "tracks", "tracktotal"])
        
        return result
    
    def getFilenameForMB(self, track):
        """Return filename and containing dir with year removed."""
        
        folderFilePath = os.path.join(functions.containingDir(track.filePath), 
                                      track.fileName)
        folderFilePath = os.path.splitext(folderFilePath)[0]
        
        if "date" in track.metadata: # If we know the date, try to remove it...
            date = track.metadata["date"]
            folderFilePath = folderFilePath.replace(date, "")
        else: # ...otherwise just remove the leftmost set of four digits, if any.
            match = re.findall("\d{4}", folderFilePath)
            if match:
                folderFilePath = folderFilePath.replace(match[0], "")
                
        return mb.FilepathString(toUnicode(folderFilePath))
