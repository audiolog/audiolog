# -*- coding: utf-8 -*-

"""This file MAY BE DONE.
To-do:
    getMBTagWithKnownData (maybe, I don't think we want/need it)"""

import tagging
import getters
import logger

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
        self.getters = [(self.getTag, 2),                   # In AbstractFinder
                        (self.getMBKnownData, 4),
                        (self.getMBTagWithKnownData, 3)]
    
    def getMBKnownData(self, track):
        """Query MB using known data.
        
        To find a date we...
            Need: A release
            Can Use: An artist, a tracktotal
            Might Use: Tracknames"""
        
        logger.log("Searching for date in MusicBrainz using the currently known data.", "Actions")
        
        # Required condition
        if not "release" in track.metadata:
            return None
        
        logger.startSection()
        result = getters.mbInterface("date", None, track, ["release", "artist", "tracktotal"])
        logger.endSection()
        return result
    
    def getMBTagWithKnownData(self, track):
        """Query MB using known data and the current tag."""
        
        logger.log("Attempting to match the current date tag value with MusicBrainz using the currently known data.", "Actions")
        
        dateTag = tagging.getTag(track.filePath, "date")
        if not dateTag:
            return None
        
        # Required condition
        if not "release" in track.metadata:
            return None
        
        logger.startSection()
        result = getters.mbInterface("date", dateTag, track, ["release", "artist", "tracktotal", "date"])
        logger.endSection()
        return result
