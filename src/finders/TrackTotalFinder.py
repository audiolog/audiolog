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
    
import metadata.tagging
import metadata.getters
import etc.logger

from AbstractFinder import AbstractReleaseFinder

class TrackTotalFinder(AbstractReleaseFinder):
    """Gatherer of track total data from all available sources.

    Applicable known data:
    - Artist
    - Release
    - Date
    - Titles
    """
        
    fieldName = "tracktotal"
        
    def __init__(self):
        self.getters = [(self.getTag, 1),                   # In AbstractFinder
                        (self.getMBKnownData, 3),
                        (self.getMBTagWithKnownData, 4),
                        (self.getNumTracksInDir, 2),
                        (self.getMBNumTracksInDir, 6)]
    
    def getMBKnownData(self, track):
        """Query MB using known data.
        
        To find a tracktotal we...
            Need: A release
            Can Use: A date, an artist"""
        
        logger.log("Searching for tracktotal in MusicBrainz using the currently known data.", "Actions")
        logger.startSection()
        
        if not "release" in track.metadata:
            logger.log("Attempt failed because our currently known data does not include the field we need -- the release.", "Failures")
            result = None
        else:
            result = getters.mbInterface(self.fieldName, None, track, ["release", "artist", "date"])
            if result:
                result = result.zfill(2)

        logger.endSection()
        return result
    
    def getMBTagWithKnownData(self, track):
        """Query MB using known data and the current tag."""
        
        logger.log("Attempting to match the current tracktotal tag value with MusicBrainz using the currently known data.", "Actions")
        logger.startSection()
        
        tracktotalTag = tagging.getTag(track.filePath, "tracktotal")
        
        if not tracktotalTag:
            logger.log("Attempt failed because current tag is empty.", "Failures")
            result = None
        elif not "release" in track.metadata:
            logger.log("Attempt failed because our currently known data does not include the field we need -- the release.", "Failures")
            result = None
        else:
            result = getters.mbInterface(self.fieldName, tracktotalTag, track, ["release", "artist", "date", "tracktotal"])
            if result:
                result = result.zfill(2)
            
        logger.endSection()
        return result
    
    def getNumTracksInDir(self, track):
        """Return number of tracks in directory as left-zero-padded unicode string."""
        
        return unicode(len(track.parent.tracks)).zfill(2)
    
    def getMBNumTracksInDir(self, track):
        """See if the number of tracks in the directory matches with MB."""
        
        logger.log("Attempting to match the number of tracks in the directory with MusicBrainz using the currently known data.", "Actions")
        logger.startSection()
        
        if not "release" in track.metadata:
            logger.log("Attempt failed because our currently known data does not include the field we need -- the release.", "Failures")
            result = None
        else:
            numTracks = self.getNumTracksInDir(track)
            result = getters.mbInterface(self.fieldName, numTracks, track, ["release", "artist", "date", "tracktotal"])
            if result:
                result = result.zfill(2)

        logger.endSection()
        return result
