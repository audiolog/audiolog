# -*- coding: utf-8 -*-

"""This file is DONE."""

import re

import tagging
import getters
import logger

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
                        (self.getFilename, 1)]
    
    def getMBKnownData(self, track):
        """Query MB using known data.
        
        To find a tracknumber we...
            Need: A track title
            Can Use: A release, an artist"""
        
        logger.log("Searching for tracknumber in MusicBrainz using the currently known data.", "Actions")
        
        # Required condition
        if not "title" in track.metadata:
            return None
        
        logger.startSection()
        result = getters.mbInterface(self.fieldName, None, track, ["title", "artist", "release"])
        logger.endSection()
        return result
    
    def getMBTagWithKnownData(self, track):
        """Query MB using known data and the current tag."""
        
        logger.log("Attempting to match the current tracknumber tag value with MusicBrainz using the currently known data.", "Actions")
        tracknumberTag = tagging.getTag(track.filePath, "tracknumber")
        
        if not tracknumberTag:
            return None
        
        # Required condition
        if not "title" in track.metadata:
            return None
        
        logger.startSection()
        result = getters.mbInterface(self.fieldName, tracknumberTag, track, ["title", "artist", "release", "tracknumber"])
        logger.endSection()
        return result
    
    def getFilename(self, track):
        """Find one or two consecutive digits in the filename."""
        
        tracknum = re.compile("(?<!\d)\d{1,2}(?=\D)")  # One or two digits
        match = tracknum.search(track.fileName)
        if match:
            digits = match.group()
            return unicode(digits).rjust(2, u"0")
        else:
            return None
