# -*- coding: utf-8 -*-

"""This file is DONE."""

import os
import re

import tagging
import getters
import logger

from AbstractFinder import AbstractTrackFinder

class TitleFinder(AbstractTrackFinder):
    """Gatherer of title data from all available sources.

    Applicable known data:
    - Artist
    - Release
    - Date
    - Track total
    - Track number
    """
        
    fieldName = "title"
        
    def __init__(self):
        self.getters = [(self.getPUID, 3),
                        (self.getMBPUID, 3),
                        (self.getTag, 1),                   # In AbstractFinder
                        (self.getMBTag, 3),                 # In AbstractFinder
                        (self.getMBKnownData, 2),
                        (self.getMBTagWithKnownData, 4),
                        (self.getMBFilename, 2),
                        (self.getMBFilenameWithKnownData, 3.5)]
    
    def getPUID(self, track):
        """Return title if MusicDNS provided one."""

        logger.log("Looking in MusicDNS results.", "Actions")
        logger.startSection()
        if track.PUID:
            result = track.PUID[1]
        else:
            logger.log("MusicDNS results are empty.", "Failures")
            result = None
            
        logger.endSection()
        return result
    
    def getMBPUID(self, track):
        """If MusicDNS provided a PUID, look it up in MusicBrainz."""

        logger.log("Look up the PUID provided by MusicDNS in MusicBrainz.", "Actions")
        logger.startSection()
        result = getters.getMBPUID(track, "title")
        logger.endSection()
        return result
            
    def getMBKnownData(self, track):
        """Query MB using known data.
            
        We can find the title from the release and a tracknumber.
        To do this we...
            Need: release, tracknumber
            Can Use: date, artist, tracktotal"""

        logger.log("Searching for title in MusicBrainz using the currently known data.", "Actions")
        logger.startSection()
        
        if not ("release" in track.metadata and "tracknumber" in track.metadata):
            logger.log("Attempt failed because our currently known data does not include the fields we need -- the release and track number.", "Failures")
            result = None
        else:
            result = getters.mbInterface(self.fieldName, None, track, ["release", "tracknumber", "date", "artist", "tracktotal"]) # We can use these extra fields because we are searching for a release, not a track.
        
        logger.endSection()
        return result
    
    def getMBTagWithKnownData(self, track):
        """Query MB using known data and the current tag."""
        
        logger.log("Attempting to match the current title tag value with MusicBrainz using the currently known data.", "Actions")
        logger.startSection()

        titleTag = tagging.getTag(track.filePath, "title")

        if not titleTag:
            logger.log("Attempt failed because current tag is empty.", "Failures")
            result = None
        if not ("release" in track.metadata and "tracknumber" in track.metadata):
            logger.log("Attempt failed because our currently known data does not include the fields we need -- the release and track number.", "Failures")
            result = None
        else:
            result = getters.mbInterface(self.fieldName, titleTag, track, ["release", "tracknumber", "artist"]) # Here we're searching for a track.
        
        logger.endSection()
        return result
    
    def getMBFilename(self, track):
        """Try to match the file name to a title using MB."""
        
        fileName = self.getFilenameForMB(track)
        logger.log("Attempting to match the filepath with MusicBrainz.", "Actions")
        logger.startSection()
        result = getters.mbInterface(self.fieldName, fileName, track)
        logger.endSection()
        return result
    
    def getMBFilenameWithKnownData(self, track):
        """Try to match the file name to a title using MB."""
        
        logger.log("Attempting to match the filepath release tag value with MusicBrainz using the currently known data.", "Actions")
        logger.startSection()
        
        if not ("release" in track.metadata and "tracknumber" in track.metadata):
            logger.log("Attempt failed because our currently known data does not include the fields we need -- the release and track number.", "Failures")
            result = None
        else:
            fileName = self.getFilenameForMB(track)
            result = getters.mbInterface(self.fieldName, fileName, track, ["release", "tracknumber", "artist"]) # Here we're searching for a track.
        
        logger.endSection()
        return result
    
    def getFilenameForMB(self, track):
        
        fileName = os.path.splitext(track.fileName)[0]
        
        if "tracknumber" in track.metadata: # If we know the tracknumber, try to remove it...
            tracknumber = track.metadata["tracknumber"]
            regex = re.compile("(?<!\d)[ _]*" + tracknumber + "(([ _]+(-|\)|\.)?)|([ _]*(-|\)|\.)))")
        else: # ...otherwise, if the name starts with 1 or 2 digits, remove them plus the delimeter.
            regex = re.compile("(?<!\d)[ _]*\d{1,2}(([ _]+(-|\)|\.)?)|([ _]*(-|\)|\.)))")
        
        match = regex.search(fileName)
        if match:
            fileName = fileName.replace(match.group(), "")
        
        return fileName.strip()
