"""Provides the Release class which oversees the tagging of one disc of audio.

The Release, along with the Track objects it contains, control the entirety of 
audio identification, tagging and renaming process. In general, Release tells 
the tracks what actions to take and shares the information found between them, 
while the tracks gather the actual metainformation."""

import os
import time
import datetime

import functions
import flowcontrol
import track
from LogFrame import log

class ReleaseError(Exception):
    """Raised when a problem is found which will keep the release from being tagged."""
    pass

class Release(object):
    """Represents one directory of audio and the tracks contained therein."""

    releaseFields = ["artist", "release", "date", "tracktotal", "genre"]
    trackFields = ["title", "tracknumber"]
    
    def __init__(self, directoryPath, audioFilePaths):
        log("Attempting to identify tracks using MusicDNS service.", 3, "Actions")
        self.tracks = [track.Track(self, filePath) for filePath in audioFilePaths]
        self.release = {}

    def do(self):
        """Find common release data, then track-specific data, then apply changes."""
        
        log("Gathering audio metainformation", 3, "Actions")
        # Handle common release data
        for field in self.releaseFields:
            log("Finding " + field + " info", 4, "Actions")
            for track in self.tracks:
                track.find(field)
            self.findConsensus(field)
            self.updateTracks(field)
        
        # Handle track-specific data
        for field in self.trackFields:
            log("Finding " + field + " info", 4, "Actions")
            for track in self.tracks:
                track.find(field)
                self.findConsensus(field, track)
        
        log("Writing audio metainformation to tracks", 3, "Actions")
        self.applyChanges()
        
    def findConsensus(self, field, track=None):
        """Gather relevant data; find the value with the highest score.
        
        If a track argument is provided, function works in track-specific mode"""
        
        flowcontrol.checkpoint()
        
        # Create a list of (value, weight) pairs
        if track:
            log("Finding a consensus for " + field + " on " + functions.quote(track.baseName), 5, "Details")
            consensusData = track.getConsensusData(field)
        else:
            log("Finding a consensus for " + field, 5, "Details")
            consensusData = []
            for track in self.tracks:
                consensusData += track.getConsensusData(field)
            track = None

        # Sanity-check date
        if field == "date":
            for (value, weight) in consensusData:
                year = int(value)
                if year < 1600 or year > datetime.date.today().year + 1:
                    consensusData.remove((value, weight))

        # Ensure that we have data for field, otherwise raise an error
        if not consensusData:
            if field == "genre":                    # A blank genre is acceptable
                self.release["genre"] = ""
                return
            else:                                   # Any other field is not
                log("Unable to find a consensus", 6, "Errors")
                log("Unable to find a " + field, 5, "Errors")
                raise ReleaseError
        
        # Create a dictionary of values to sums of weights
        scores = {}
        for (value, weight) in consensusData:
            scores[value] = scores.get(value, 0) + weight
        
        # Put the results in a list so we can sort
        listed = [(scores[value], value) for value in scores]
        listed.sort(reverse=True)
        
        # Display the results
        topScore, topValue = listed[0] 
        log(str(listed), 6, "Debugging")  
        log("topScore: " + str(topScore), 6, "Debugging")
        log("topValue: " + topValue, 6, "Debugging")
        
        # Store result
        if track:
            track.track[field] = topValue
        else:
            self.release[field] = topValue
    
    def updateTracks(self, field):
        """After a consensus has been reached, update appropriate field in tracks."""
        
        for track in self.tracks:
            track.track[field] = self.release[field]
        
    def applyChanges(self):
        """After tags have been found, write tags and filenames for all tracks."""
        
        for track in self.tracks:
            flowcontrol.checkpoint(pauseOnly=True)
            track.writeTags()
            track.rename()
    
    def getNewPath(self):
        """Return the new path to the album based on the ID3 tags.
        
        Format: Genre/Artist/Year - Album/
        If no genre was found, "[None]" is used."""
        
        if "genre" in self.release:
            genre = self.release["genre"]
        else:
            genre = "[None]"
        
        return os.path.join(genre, self.release["artist"], 
               (self.release["date"] + " - " + self.release["release"]))
            