# -*- coding: utf-8 -*-

"""Provides the Track class represent one audio file.

Multiple Track objects are created by a Release object. Then, for each field
(artist, release, etc.), the tracks query the relevant metainformation sources,
which include MusicDNS, MusicBrainz using PUID, MusicBrainz using current tags,
the current tags themselves and information found in the filename. The Release
then gathers all the data found by all the tracks for one field, determines
what result has the most points and shares this information with all the 
tracks so that they can use it to refine later queries. 

A similar process plays out for track-specific fields (title and tracknumber) 
then when all information has been determined for all files, the Release asks
all tracks to write their tags with the info found and rename their filenames. 

If at any point we cannot determine a value for a field, a ReleaseError is
raised, which is caught in audio.handleAudio, and the directory is rejected."""

import os
import time
import shutil

import functions
import flowcontrol
import tagging
import release
import getters
from functions import quote
from LogFrame import log

class Track(object):
    """Represents one audio file."""

    fields = ["artist", "release", "date", "title", "tracknumber", "tracktotal", "genre"]
    
    sourceWeights = {"PUID":     3, 
                     "mb-PUID":  3, 
                     "mb-Tag":   2, 
                     "Tag":      1, 
                     "Filename": 0.5}
                     
    sources = {"artist":      ["mb-PUID", "mb-Tag", "Tag"],
               "release":     ["mb-Tag", "Tag", "Filename"],
               "date":        ["mb-Tag", "Tag", "Filename"],
               "title":       ["mb-PUID", "mb-Tag", "Tag", "Filename"],
               "tracknumber": ["mb-Tag", "Tag", "Filename"],
               "tracktotal":  ["mb-Tag", "Tag", "Filename"],
               "genre":       ["Tag"]}
    
    dataGetters = {"mb-PUID":  getters.getmbPUID,
                   "mb-Tag":   getters.getmbTag,
                   "Tag":      getters.getTag,
                   "Filename": getters.getFilename}
                   
    dataGetterDisplay = {"mb-PUID":  "MusicBrainz via PUID",
                         "mb-Tag":   "MusicBrainz via Tags",
                         "Tag":      "current tags",
                         "Filename": "the file name and path"}
               
    def __init__(self, parentRelease, filePath):
        self.parentRelease = parentRelease
        self.filePath = filePath
        self.baseName = os.path.basename(filePath)
        self.PUID = None
        self.track = {}
        self.dataFound = dict([(field, {}) for field in self.fields])
        self.runFetchPUID()

    def runFetchPUID(self):
        """Run getPUID on the track and store the data for later."""
        
        result = getters.fetchPUID(self.filePath)
        if result:
            self.dataFound["artist"]["PUID"] = result[0]
            self.dataFound["title"]["PUID"] = result[1]
            self.PUID = result[2]
    
    def find(self, field):
        """Gather data about field from all available sources."""
                
        log("Finding " + field + " info for " + quote(self.baseName), 5, "Details")
        for source in self.sources[field]:
            flowcontrol.checkpoint()
            log("Gathering info from " + self.dataGetterDisplay[source], 6, "Details")
            dataGetter = self.dataGetters[source]
            data = dataGetter(self, field)
            self.dataFound[field][source] = data

    def getConsensusData(self, field):
        """Return a list of (value, weight) pairs for use in findConsensus."""
        
        log("Getting " + field + " consensus info for " + quote(self.baseName), 6, "Details")
        consensusData = []
        for source in self.dataFound[field]:
            value = self.dataFound[field][source]
            if value:
                consensusData.append((value, self.sourceWeights[source]))
        return consensusData

    def writeTags(self):
        """Clear the current track tags and write what we've found."""
        
        log("Writing tags for " + quote(self.baseName), 4, "Actions")
        log("Clearing current tags", 5, "Details")
        tagging.clearTags(self.filePath)
        log("Writing these tags:", 5, "Details")
        for field in self.track:
            log("    " + field.ljust(20) + self.track[field], 5, "Details")
            tagging.setTag(self.filePath, field, self.track[field])

    def rename(self):
        """Rename the file to [tracknumber] - [title].[ext].""" 
               
        newBaseName = self.track["tracknumber"].rjust(2, u"0")
        newBaseName += " - " + self.track["title"]
        oldBaseName, ext = os.path.splitext(self.baseName)
        newPath = self.filePath.replace(oldBaseName, newBaseName)
        if not os.path.exists(newPath):
            log("Renaming " + quote(oldBaseName) + " to " + quote(newBaseName), 5, "Details")
            shutil.move(self.filePath, newPath)
        elif newBaseName == oldBaseName:
            log("Old filename is correct. No renaming necessary.", 5, "Details")
        else:
            log("Cannot rename " + quote(oldBaseName) + ". There already exists a file with the target filename.", 5, "Errors")
            log("Target filename: " + quote(newBaseName), 6, "Debugging")
            raise release.ReleaseError
