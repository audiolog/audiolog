# -*- coding: utf-8 -*-

"""Logging is DONE."""

import os
import re

import getters
import tagging
import logger
import functions

from AbstractFinder import AbstractReleaseFinder

class ArtistFinder(AbstractReleaseFinder):
    """Gatherer of artist data from all available sources.
    
    All the ways:
        - PUID
        - MB-PUID
        - Tag
        - MB-Tag
        - MB via Previous Data
            - From Release AND (Year OR Tracks)
        - MB via Tag and Previous Data"""
    
    fieldName = "artist"
    
    def __init__(self):
        self.getters = [(self.getPUID, 3),
                        (self.getMBPUID, 3),
                        (self.getTag, 1),                   # In AbstractFinder
                        (self.getMBTag, 3),                 # In AbstractFinder
                        (self.getMBKnownData, 2),
                        (self.getMBTagWithKnownData, 4),
                        (self.getMBFilename, 2)]
    
    def getPUID(self, track):
        """Return artist if MusicDNS provided one."""

        logger.log("Looking in MusicDNS results.", "Actions")
        logger.startSection()
        if track.PUID:
            result = track.PUID[0]
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
        result = getters.getMBPUID(track, "artist")
        logger.endSection()
        return result
            
    def getMBKnownData(self, track):
        """Query MB using known data.
            
        We can find the artist from the release.
        To do this we...
            Need: release
            Can Use: date, tracktotal
            Might Use: tracks"""
        
        logger.log("Searching for an artist in MusicBrainz using the currently known data.", "Actions")
        if not "release" in track.metadata:
            return None
        
        logger.startSection()
        result = getters.mbInterface(self.fieldName, None, track, ["release", "date", "tracktotal", "tracks"])
        logger.endSection()
        return result
    
    def getMBTagWithKnownData(self, track):
        """Query MB using known data and the current tag."""
        
        logger.log("Attempting to match the current artist tag value with MusicBrainz using the currently known data.", "Actions")    
        artistTag = tagging.getTag(track.filePath, "artist")
        if not artistTag:
            return None

        if not "release" in track.metadata:
            return None
        
        logger.startSection()
        result = getters.mbInterface(self.fieldName, artistTag, track, ["release", "date", "tracktotal"])
        logger.endSection()
        return result
    
    def getMBFilename(self, track):
        """Try to match the file name to an artist using MB."""
        
        folderFilePath = self.getFilenameForMB(track)
        logger.log("Attempting to match the filepath to an artist using MusicBrainz.", "Actions")
        logger.startSection()
        result = getters.mbInterface(self.fieldName, folderFilePath, track)
        logger.endSection()
        
        return result
    
    def getFilenameForMB(self, track):
        """Return filename and containing dir with year removed."""
    
        folderFilePath = os.path.join(functions.containingDir(track.filePath), track.fileName)
        folderFilePath = os.path.splitext(folderFilePath)[0]
        
        if "date" in track.metadata: # If we know the date, try to remove it...
            date = track.metadata["date"]
            folderFilePath = folderFilePath.replace(date, "")
        else: # ...otherwise just remove the leftmost four digits.
            match = re.findall("\d{4}", folderFilePath)
            if match:
                folderFilePath = folderFilePath.replace(match[0], "")
                
        return folderFilePath
