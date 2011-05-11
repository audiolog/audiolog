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
    
from metadata import tagging
from metadata import musicbrainz as mb
from etc.logger import log, logfn, logSection

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
                        (self.getMBTagKnownData, 4),
                        (self.getNumTracksInDir, 2),
                        (self.getMBNumTracksInDir, 6)]
    
    @logfn("Searching MusicBrainz with the currently known data.")
    def getMBKnownData(self, track):
        """Query MB using known data.
        
        To find a tracktotal we...
            Need: A release
            Can Use: A date, an artist"""
        
        if not "release" in track.metadata:
            log("The currently known data does not include the field we need --"
                " the release.")
            result = None
        else:
            result = mb.askMB(self.fieldName, None, track, 
                              ["release", "artist", "date"])
            if result:
                result = result.zfill(2)

        return result
    
    @logfn("Matching the current tag value with MusicBrainz using known data.")
    def getMBTagKnownData(self, track):
        """Query MB using known data and the current tag."""
        
        tracktotalTag = tagging.getTag(track.filePath, "tracktotal")
        
        if not tracktotalTag:
            log("The current tag is empty.")
            result = None
            
        elif not "release" in track.metadata:
            log("The currently known data does not include the field we need --"
                " the release.")
            result = None
            
        else:
            result = mb.askMB(self.fieldName, tracktotalTag, track, 
                              ["release", "artist", "date", "tracktotal"])
            if result:
                result = result.zfill(2)
            
        return result
    
    @logfn("Counting the number of tracks in the directory.")
    def getNumTracksInDir(self, track):
        """Return number of tracks in directory as left-zero-padded unicode string."""
        
        return unicode(len(track.parent.tracks)).zfill(2)
    
    @logfn("Matching the track count with MusicBrainz using the known data.")
    def getMBNumTracksInDir(self, track):
        """See if the number of tracks in the directory matches with MB."""
        
        if not "release" in track.metadata:
            log("The currently known data does not include the field we need --"
                " the release.")
            result = None
            
        else:
            numTracks = self.getNumTracksInDir(track)
            result = mb.askMB(self.fieldName, numTracks, track, 
                              ["release", "artist", "date", "tracktotal"])
            if result:
                result = result.zfill(2)

        return result
