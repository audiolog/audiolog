# -*- coding: utf-8 -*-

"""This file is DONE."""

import os
import re

import tagging
import functions
import getters
import logger

from AbstractFinder import AbstractReleaseFinder

class ReleaseFinder(AbstractReleaseFinder):
    """Gatherer of release data from all available sources.

    Applicable known data:
    - Artist
    - Date
    - Track total
    - Titles
    """
        
    fieldName = "release"
        
    def __init__(self):
        self.getters = [(self.getTag, 1),                   # In AbstractFinder
                        (self.getMBTag, 3),                 # In AbstractFinder
                        (self.getMBKnownData, 3),
                        (self.getMBTagWithKnownData, 4),
                        (self.getMBFilename, 2),
                        (self.getMBFilenameWithKnownData, 3.5)]
    
    def getMBKnownData(self, track):
        """Query MB using known data.
        
        To find a date we...
            Need: Artist AND (Date OR Titles)
            Can Use: Tracktotal"""
        
        logger.log("Searching for release in MusicBrainz using the currently known data.", "Actions")
        
        # Required condition
        if not (("artist" in track.metadata) and 
                ("date" in track.metadata or "title" in track.metadata)):
            return None
        
        logger.startSection()
        result = getters.mbInterface(self.fieldName, None, track, ["artist", "date", "tracks", "tracktotal"])
        logger.endSection()
        return result
    
    def getMBTagWithKnownData(self, track):
        """Query MB using known data and the current tag."""
        
        logger.log("Attempting to match the current release tag value with MusicBrainz using the currently known data.", "Actions")
        
        releaseTag = tagging.getTag(track.filePath, "release")
        if not releaseTag:
            return None
        
        # Required condition
        if not ("artist" in track.metadata or "date" in track.metadata or "title" in track.metadata):
            return None
        
        logger.startSection()
        result = getters.mbInterface(self.fieldName, releaseTag, track, ["artist", "date", "tracks", "tracktotal"])
        logger.endSection()
        return result

    def getMBFilename(self, track):
        """Attempt to fuzzily match release name from filepath using MusicBrainz.
        
        We look for the release name in the folder and file name."""
        
        folderFilePath = self.getFilenameForMB(track)
        logger.log("Attempting to match the filepath with MusicBrainz.", "Actions")
        logger.startSection()
        result = getters.mbInterface(self.fieldName, folderFilePath, track)
        logger.endSection()
        return result

    def getMBFilenameWithKnownData(self, track):
        """Attempt to fuzzily match release name from filepath using MusicBrainz.
       
        We look for the release name in the folder and file name."""
        
        logger.log("Attempting to match the filepath release tag value with MusicBrainz using the currently known data.", "Actions")
        
        # Required condition
        if not ("artist" in track.metadata or "date" in track.metadata or "title" in track.metadata):
            return None
        
        folderFilePath = self.getFilenameForMB(track)
        logger.startSection()
        result = getters.mbInterface(self.fieldName, folderFilePath, track, ["artist", "date", "tracks", "tracktotal"])
        logger.endSection()
        return result
    
    def getFilenameForMB(self, track):
    
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
