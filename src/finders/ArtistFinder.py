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

import os
import re

from metadata import tagging
from metadata import musicbrainz as mb
from etc import logger
from etc import functions

from AbstractFinder import AbstractReleaseFinder
from AbstractFinder import FilepathString

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
    
    def getMusicDNS(self, track):
        """Return artist if MusicDNS provided one."""

        logger.log("Looking in MusicDNS results.", "Actions")
        return track.musicDNS["artist"]
    
    def getMBPUID(self, track):
        """If MusicDNS provided a PUID, look it up in MusicBrainz."""

        logger.log("Looking up the PUID provided by MusicDNS in MusicBrainz.", "Actions")
        logger.startSection()
        result = mb.getMBPUID(track.musicDNS["puid"], "artist")
        logger.endSection()
        return result
            
    def getMBKnownData(self, track):
        """Query MB using known data.
            
        We can find the artist from the release.
        To do this we...
            Need: release
            Can Use: date, tracktotal
            Might Use: tracks"""
        
        logger.log("Searching for an artist in MusicBrainz using the currently known data.", "Actions")
        logger.startSection()
        
        if not "release" in track.metadata:
            logger.log("Attempt failed because our currently known data does not include the field we need -- the release.", "Failures")
            result = None
        else:
            result = mb.mbInterface(self.fieldName, None, track, ["release", "date", "tracktotal", "tracks"])
            
        logger.endSection()
        return result
    
    def getMBTagWithKnownData(self, track):
        """Query MB using known data and the current tag."""
        
        logger.log("Attempting to match the current artist tag value with MusicBrainz using the currently known data.", "Actions")
        logger.startSection()
        
        artistTag = tagging.getTag(track.filePath, "artist")
        
        if not artistTag:
            logger.log("Attempt failed because current tag is empty.", "Failures")
            result = None
        elif not "release" in track.metadata:
            logger.log("Attempt failed because our currently known data does not include the field we need -- the release.", "Failures")
            result = None
        else:
            result = mb.mbInterface(self.fieldName, artistTag, track, ["release", "date", "tracktotal"])
        
        logger.endSection()
        return result
    
    def getMBFilename(self, track):
        """Try to match the file name to an artist using MB."""
        
        folderFilePath = self.getFilenameForMB(track)
        logger.log("Attempting to match the filepath to an artist using MusicBrainz.", "Actions")
        logger.startSection()
        result = mb.mbInterface(self.fieldName, folderFilePath, track)
        logger.endSection()
        return result
    
    def getFilenameForMB(self, track):
        """Return filename and containing dir with year removed."""
        
        folderFilePath = os.path.join(functions.containingDir(track.filePath), track.fileName)
        folderFilePath = os.path.splitext(folderFilePath)[0]
        
        folderFilePath = FilepathString(folderFilePath)
        
        if "date" in track.metadata: # If we know the date, try to remove it...
            date = track.metadata["date"]
            folderFilePath = folderFilePath.replace(date, "")
        else: # ...otherwise just remove the leftmost set of four digits, if any.
            match = re.findall("\d{4}", folderFilePath)
            if match:
                folderFilePath = folderFilePath.replace(match[0], "")
                
        return folderFilePath
