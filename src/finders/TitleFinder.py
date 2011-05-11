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
from etc.logger import log, logfn, logSection
from etc.utils import *

from AbstractFinder import AbstractTrackFinder

class TitleFinder(AbstractTrackFinder):
    """Gatherer of title data from all available sources.

    Applicable known data:
    - Artist
    - Release
    - Date
    - Track total
    - Track number
    """
        
    fieldName = "title"
        
    def __init__(self):
        self.getters = [(self.getMusicDNS, 3),
                        (self.getMBPUID, 3),
                        (self.getTag, 1),                   # In AbstractFinder
                        (self.getMBTag, 3),                 # In AbstractFinder
                        (self.getMBKnownData, 2),
                        (self.getMBTagWithKnownData, 4),
                        (self.getMBFilename, 2),
                        (self.getMBFilenameWithKnownData, 3.5)]
    
    @logfn("Looking in MusicDNS results.")
    def getMusicDNS(self, track):
        """Return title if MusicDNS provided one."""
        
        return track.musicDNS["title"]

    @logfn("Looking up the PUID provided by MusicDNS in MusicBrainz.")
    def getMBPUID(self, track):
        """If MusicDNS provided a PUID, look it up in MusicBrainz."""

        return mb.getMBPUID(track.musicDNS["puid"], "title")
    
    @logfn("Searching MusicBrainz with the currently known data.")
    def getMBKnownData(self, track):
        """Query MB using known data.
            
        We can find the title from the release and a tracknumber.
        To do this we...
            Need: release, tracknumber
            Can Use: date, artist, tracktotal"""

        if not ("release" in track.metadata and "tracknumber" in track.metadata):
            log("The currently known data does not include the fields we need --"
                " the release and track number.")
            result = None
            
        else:
            # We can use these extra fields because we are searching for a 
            # release, not a track.
            result = mb.askMB(self.fieldName, None, track, 
                              ["release", "tracknumber", "date", "artist", 
                               "tracktotal"])
        
        return result
    
    @logfn("Matching the current tag value with MusicBrainz using known data.")
    def getMBTagWithKnownData(self, track):
        """Query MB using known data and the current tag."""
        
        titleTag = tagging.getTag(track.filePath, "title")

        if not titleTag:
            log("The current tag is empty.")
            result = None
            
        elif not ("release" in track.metadata and "tracknumber" in track.metadata):
            log("The currently known data does not include the fields we need --"
                " the release and track number.")
            result = None
            
        else:
            # Here we're searching for a track.
            result = mb.askMB(self.fieldName, titleTag, track, 
                              ["release", "tracknumber", "artist"])
        
        return result
    
    @logfn("Matching the filename to a title using MusicBrainz.")
    def getMBFilename(self, track):
        """Try to match the file name to a title using MB."""
        
        fileName = self.getFilenameForMB(track)
        return mb.askMB(self.fieldName, fileName, track)

    @logfn("Matching the filename with MusicBrainz using the known data.")
    def getMBFilenameWithKnownData(self, track):
        """Try to match the file name to a title using MB."""
                
        if not ("release" in track.metadata and "tracknumber" in track.metadata):
            log("The currently known data does not include the fields we need --"
                " the release and track number.")
            result = None
            
        else:
            fileName = self.getFilenameForMB(track)
            # Here we're searching for a track.
            result = mb.askMB(self.fieldName, fileName, track, 
                              ["release", "tracknumber", "artist"])
        
        return result
    
    def getFilenameForMB(self, track):
        """Return filename with track number removed."""
        
        fileName = os.path.splitext(track.fileName)[0]
        
        if "tracknumber" in track.metadata: # If we know the tracknumber, try to remove it...
            tracknumber = track.metadata["tracknumber"]
            regex = re.compile("(?<!\d)[ _]*" + tracknumber + "(([ _]+(-|\)|\.)?)|([ _]*(-|\)|\.)))")
        else: # ...otherwise, if the name starts with 1 or 2 digits, remove them plus the delimeter.
            regex = re.compile("(?<!\d)[ _]*\d{1,2}(([ _]+(-|\)|\.)?)|([ _]*(-|\)|\.)))")
        
        match = regex.search(fileName)
        if match:
            fileName = fileName.replace(match.group(), "")
        
        return toUnicode(fileName.strip())
