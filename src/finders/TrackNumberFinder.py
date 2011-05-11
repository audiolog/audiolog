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

import re

from metadata import tagging
from metadata import musicbrainz as mb
from etc.logger import log, logfn, logSection

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
        self.getters = [(self.getTag, 2), 
                        (self.getMBKnownData, 4), 
                        (self.getMBTagKnownData, 6),
                        (self.getFilename, 3)]
    
    @logfn("Searching MusicBrainz with the currently known data.")
    def getMBKnownData(self, track):
        """Query MB using known data.
        
        To find a tracknumber we...
            Need: A track title
            Can Use: A release, an artist"""
        
        if not "title" in track.metadata:
            log("The currently known data does not include the field we need --"
                " the track title.")
            result = None
        else:
            result = mb.askMB(self.fieldName, None, track, 
                              ["title", "artist", "release"])
            if result:
                result = result.zfill(2)
            
        return result
    
    @logfn("Matching the current tag value with MusicBrainz using known data.")
    def getMBTagKnownData(self, track):
        """Query MB using known data and the current tag."""
        
        tracknumberTag = tagging.getTag(track.filePath, "tracknumber")

        if not tracknumberTag:
            log("The current tag is empty.")
            result = None
            
        elif not "title" in track.metadata:
            log("The currently known data does not include the fields we need --"
                " the track title.")
            result = None
            
        else:
            result = mb.askMB(self.fieldName, tracknumberTag, track, 
                              ["title", "artist", "release", "tracknumber"])
            if result:
                result = result.zfill(2)
        
        return result
    
    def getFilename(self, track):
        """Find one or two consecutive digits in the filename."""
        
        tracknum = re.compile("(?<!\d)\d{1,2}(?=\D)") # One or two digits, but
        matches = tracknum.findall(track.fileName)    # not more. No years.
        if matches:
            # If there is more than one match, prefer 2-digit matches over 
            # 1-digit matches.
            for match in matches:
                if len(match) == 2:
                    return match
                
            # All the matches are 1 digit. Take the leftmost.
            return unicode(matches[0]).zfill(2)
        else:
            return None

    def getTag(self, track):
        """Get tag and left-zero-pad it."""
        
        tag = AbstractFinder.getTag(self, track)
        if tag:
            tag = tag.zfill(2)
        return tag
