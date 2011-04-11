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

import re

from metadata import tagging
from metadata import musicbrainz as mb
from etc import logger

from AbstractFinder import AbstractFinder
from AbstractFinder import AbstractTrackFinder

class TrackNumberFinder(AbstractTrackFinder):
    """Gatherer of track number data from all available sources.

    Applicable known data:
    - Artist
    - Title
    - Release
    - Date
    """
        
    fieldName = "tracknumber"
        
    def __init__(self):
        self.getters = [(self.getTag, 1), 
                        (self.getMBKnownData, 2), 
                        (self.getMBTagWithKnownData, 3),
                        (self.getFilename, 1.5)]
    
    def getMBKnownData(self, track):
        """Query MB using known data.
        
        To find a tracknumber we...
            Need: A track title
            Can Use: A release, an artist"""
        
        logger.log("Searching for tracknumber in MusicBrainz using the currently known data.", "Actions")
        logger.startSection()

        if not "title" in track.metadata:
            logger.log("Attempt failed because our currently known data does not include the field we need -- the track title.", "Failures")
            result = None
        else:
            result = mb.mbInterface(self.fieldName, None, track, ["title", "artist", "release"])
            if result:
                result = result.zfill(2)
            
        logger.endSection()
        return result
    
    def getMBTagWithKnownData(self, track):
        """Query MB using known data and the current tag."""
        
        logger.log("Attempting to match the current tracknumber tag value with MusicBrainz using the currently known data.", "Actions")
        logger.startSection()

        tracknumberTag = tagging.getTag(track.filePath, "tracknumber")

        if not tracknumberTag:
            logger.log("Attempt failed because current tag is empty.", "Failures")
            result = None
        elif not "title" in track.metadata:
            logger.log("Attempt failed because our currently known data does not include the field we need -- the track title.", "Failures")
            result = None
        else:
            result = mb.mbInterface(self.fieldName, tracknumberTag, track, ["title", "artist", "release", "tracknumber"])
            if result:
                result = result.zfill(2)
        
        logger.endSection()
        return result
    
    def getFilename(self, track):
        """Find one or two consecutive digits in the filename."""
        
        tracknum = re.compile("(?<!\d)\d{1,2}(?=\D)")  # One or two digits
        match = tracknum.search(track.fileName)
        if match:
            digits = match.group()
            return unicode(digits).zfill(2)
        else:
            return None

    def getTag(self, track):
        """Get tag and left-zero-pad it."""
        
        tag = AbstractFinder.getTag(self, track)
        if tag:
            tag.zfill(2)
        return tag
