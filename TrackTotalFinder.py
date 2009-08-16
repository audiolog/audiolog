# -*- coding: utf-8 -*-

"""This file is DONE."""
    
import tagging
import getters
import logger

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
        
        To find a date we...
            Need: A release
            Can Use: A date, an artist"""
        
        logger.log("Searching for tracktotal in MusicBrainz using the currently known data.", "Actions")
        
        # Required condition
        if not "release" in track.metadata:
            return None
        
        logger.startSection()
        result = getters.mbInterface(self.fieldName, None, track, ["release", "artist", "date"])
        logger.endSection()
        return result
    
    def getMBTagWithKnownData(self, track):
        """Query MB using known data and the current tag."""
        
        logger.log("Attempting to match the current tracktotal tag value with MusicBrainz using the currently known data.", "Actions")
        
        tracktotalTag = tagging.getTag(track.filePath, "tracktotal")
        
        if not tracktotalTag:
            return None
        
        # Required condition
        if not "release" in track.metadata:
            return None
        
        logger.startSection()
        result = getters.mbInterface(self.fieldName, tracktotalTag, track, ["release", "artist", "date", "tracktotal"])
        logger.endSection()
        return result
    
    def getNumTracksInDir(self, track):
        """Return number of tracks in directory as unicode."""
        
        return unicode(len(track.parent.tracks))
    
    def getMBNumTracksInDir(self, track):
        """See if the number of tracks in the directory matches with MB."""
        
        logger.log("Attempting to match the number of tracks in the directory with MusicBrainz using the currently known data.", "Actions")
        
        # Required condition
        if not "release" in track.metadata:
            return None
            
        numTracks = self.getNumTracksInDir(track)
        
        logger.startSection()
        result = getters.mbInterface(self.fieldName, numTracks, track, ["release", "artist", "date", "tracktotal"])
        logger.endSection()
        return result
