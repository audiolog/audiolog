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

class ArtistFinder(AbstractReleaseFinder):
    """Gatherer of artist data from all available sources.
    
    All the ways:
        - MusicDNS
        - MB-PUID
        - Tag
        - MB-Tag
        - MB via Previous Data
            - From Release AND (Year OR Tracks)
        - MB via Tag and Previous Data"""
    
    fieldName = "artist"
    
    def __init__(self):
        self.getters = [(self.getMusicDNS, 3),
                        (self.getMBPUID, 3),
                        (self.getTag, 1),                   # In AbstractFinder
                        (self.getMBTag, 3),                 # In AbstractFinder
                        (self.getMBKnownData, 2),
                        (self.getMBTagWithKnownData, 4),
                        (self.getMBFilename, 2)]
    
    @logfn("Looking in MusicDNS results.")
    def getMusicDNS(self, track):
        """Return artist if MusicDNS provided one."""

        return track.musicDNS["artist"]
    
    @logfn("Looking up the PUID provided by MusicDNS in MusicBrainz.")
    def getMBPUID(self, track):
        """If MusicDNS provided a PUID, look it up in MusicBrainz."""

        return mb.getMBPUID(track.musicDNS["puid"], "artist")
    
    @logfn("Searching MusicBrainz with the currently known data.")
    def getMBKnownData(self, track):
        """Query MB using known data.
            
        We can find the artist from the release.
        To do this we...
            Need: release
            Can Use: date, tracktotal
            Might Use: tracks"""
        
        if not "release" in track.metadata:
            log("The currently known data does not include the field we need --"
                " the release.")
            result = None
            
        else:
            result = mb.askMB(self.fieldName, None, track, 
                              ["release", "date", "tracktotal", "tracks"])
            
        return result
    
    @logfn("Matching the current tag value with MusicBrainz using known data.")
    def getMBTagWithKnownData(self, track):
        """Query MB using known data and the current tag."""
        
        artistTag = tagging.getTag(track.filePath, "artist")
        
        if not artistTag:
            log("The current tag is empty.")
            result = None
            
        elif not "release" in track.metadata:
            log("The currently known data does not include the field we need --"
                " the release.")
            result = None
            
        else:
            result = mb.askMB(self.fieldName, artistTag, track, 
                              ["release", "date", "tracktotal"])
        
        return result
    
    @logfn("Matching the filepath to a MusicBrainz artist.")
    def getMBFilename(self, track):
        """Try to match the file name to an artist using MB."""
        
        folderFilePath = self.getFilenameForMB(track)
        return mb.askMB(self.fieldName, folderFilePath, track)
    
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
