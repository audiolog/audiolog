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

class DateFinder(AbstractReleaseFinder):
    """Gatherer of date data from all available sources.

    Applicable known data:
    - Artist
    - Release
    - Track total
    - Titles
    """
        
    fieldName = "date"
        
    def __init__(self):
        self.getters = [(self.getMusicDNS, 3),
                        (self.getTag, 2),                   # In AbstractFinder
                        (self.getMBKnownData, 4),
                        (self.getMBTagKnownData, 3)]
        
    @logfn("Looking in MusicDNS results.")
    def getMusicDNS(self, track):
        """Return year if MusicDNS provided one."""

        return track.musicDNS["year"]
    
    @logfn("Searching MusicBrainz with the currently known data.")
    def getMBKnownData(self, track):
        """Query MB using known data.
        
        To find a date we...
            Need: A release
            Can Use: An artist, a tracktotal
            Might Use: Tracknames"""
        
        if not "release" in track.metadata:
            log("The currently known data does not include the field we need --"
                " the release.")
            result = None
            
        else:
            result = mb.askMB("date", None, track, 
                              ["release", "artist", "tracktotal"])
        
        return result
    
    @logfn("Matching the current tag value with MusicBrainz using known data.")
    def getMBTagKnownData(self, track):
        """Query MB using known data and the current tag."""

        dateTag = tagging.getTag(track.filePath, "date")

        if not dateTag:
            log("The current tag is empty.")
            result = None
            
        elif not "release" in track.metadata:
            log("The currently known data does not include the field we need --"
                " the release.")
            result = None
            
        else:
            result = mb.askMB("date", dateTag, track, 
                              ["release", "artist", "tracktotal", "date"])
        
        return result
