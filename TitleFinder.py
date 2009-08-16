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
            logger.log("Returning: %s" % result, "Successes")
        else:
            result = None
            logger.log("MusicDNS results are empty. Returning: None", "Failures")
        
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
        
        if not ("release" in track.metadata and "tracknumber" in track.metadata):
            return None
        
        logger.startSection()
        result = getters.mbInterface(self.fieldName, None, track, ["release", "tracknumber", "date", "artist", "tracktotal"]) # We can use these extra fields because we are searching for a release, not a track.
        logger.endSection()
        
        return result
    
    def getMBTagWithKnownData(self, track):
        """Query MB using known data and the current tag."""
        
        logger.log("Attempting to match the current title tag value with MusicBrainz using the currently known data.", "Actions")
        titleTag = tagging.getTag(track.filePath, "title")
        if not titleTag:
            return None

        if not ("release" in track.metadata and "tracknumber" in track.metadata):
            return None
        
        logger.startSection()
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
        if not ("release" in track.metadata and "tracknumber" in track.metadata):
            return None
        
        fileName = self.getFilenameForMB(track)

        logger.startSection()
        result = getters.mbInterface(self.fieldName, fileName, track, ["release", "tracknumber", "artist"]) # Here we're searching for a track.
        logger.endSection()
        return result
    
    def getFilenameForMB(self, track):
        
        fileName = os.path.splitext(track.fileName)[0]
        
        if "tracknumber" in track.metadata: # If we know the tracknumber, try to remove it...
            tracknumber = track.metadata["tracknumber"]
            fileName = fileName.replace(tracknumber, "")
        else: # ...otherwise, if the name starts with 1 or 2 digits, remove them.
            tracknum = re.compile("(?<!\d)\d{1,2}(?=\D)")
            match = tracknum.search(fileName)
            if match:
                fileName = fileName.replace(match.group(), "")
        
        return fileName
