# -*- coding: utf-8 -*-

"""ReleaseManager manages the gathering and writing of one release's metadata.

The Overview

The metadata gathering process is the most important and most complex task
that Azul performs. The goal of this process is simple: Find complete,
accurate metadata for every track without any human intervention.

We begin with whatever (potentially incomplete and inaccurate) data currently
exists in the tags and filepaths. We attempt to match this data to entries in
the online music metadata datbase MusicBrainz. As we find results we are
confident are correct we use this "known data" to find the data that we do
not know yet.

The design of the ReleaseManager + Finders architecture is intended to
maximize our chances of finding all needed metadata. One of the key method
is to use a queue of Finder objects, one for each field that we do not yet
know. If a Finder fails to find the metadata for that field, then that
Finder is placed at the end of the queue to be tried again. The hope is that
by that time other fields will become known and this known data will allow
us to determine the field which we previously could not. 


The Picture

The relations between the classes and files used in this process are
illustrated below. Each component uses the component(s) in the box below it.

|----------------------------------------------------------------------------|
|                               ReleaseManager                               |
|----------------------------------------------------------------------------|
|   Finders (Artist, Release, Date, TrackTotal, Title, TrackNumber, Genre)   |
|----------------------------------------------------------------------------|
|              tagging                 |              getters                |
|--------------------------------------|-------------------------------------|
|              Mutagen                 |    MusicBrainz  |    MusicDNS       |
|--------------------------------------|-----------------|-------------------|

"""

import shutil

import flowcontrol
import logger
import getters
import functions
import tagging
import configuration
from utils import *

from ArtistFinder import ArtistFinder
from ReleaseFinder import ReleaseFinder
from DateFinder import DateFinder
from TrackTotalFinder import TrackTotalFinder
from TitleFinder import TitleFinder
from TrackNumberFinder import  TrackNumberFinder
from GenreFinder import GenreFinder

class ReleaseManagerError(Exception):
    """Raised when a problem is found which will keep the release from being tagged."""
    pass

class ReleaseManager(object):
    """Manages the gathering and writing of one release's metadata."""
    
    def __init__(self, directoryPath, audioFilePaths):
        self.release = Release(directoryPath, audioFilePaths)
        self.queue = [ArtistFinder(), ReleaseFinder(), DateFinder(), TrackTotalFinder(), TrackNumberFinder(), TitleFinder(), GenreFinder()]
        self.nextRoundQueue = []
        
    def run(self):
        """Find data, check sanity, write tags and filenames."""

        logger.log("Gathering metadata.", "Actions")
        logger.startSection()
        self.gatherMetadata()
        logger.endSection()

        logger.log("Checking for errors in the results.", "Actions")
        logger.startSection()
        self.checkSanity()
        logger.endSection()

        logger.log("Writing the results to tags and filenames.", "Actions")
        logger.startSection()
        self.writeResults()
        logger.endSection()
        
    def logInitialState(self):
        """Log the initial state of the filenames, tags and MusicDNS results."""

        for track in self.release.tracks:
            logger.log("File path: %s" % track.filePath, "Debugging")

    def gatherMetadata(self):
        """Iterate through Finders until success or stagnation."""

        while self.queue:
            for finder in self.queue:
                field = finder.fieldName
                
                logger.log("Attempting to determine the %s." % field, "Actions")
                logger.startSection()
                success = finder.run(self.release)
                logger.endSection()
                
                if not success:
                    logger.log("\nFailed to determine the %s. Will try again next round.\n\n" % field, "Failures")
                    self.nextRoundQueue.append(finder)
                else:
                    logger.log("\nSuccessfully determined the %s.\n\n" % field, "Successes")
            
            if self.queue == self.nextRoundQueue:
                logger.log("No progress has been made. The metadata gathering process has failed.\n", "Errors")
                failedFields = [finder.fieldName for finder in self.queue]
                raise ReleaseManagerError, "Unable to determine: %s" % failedFields
            else:
                self.queue = self.nextRoundQueue
                self.nextRoundQueue = []
        
    def checkSanity(self):
        """Apply field-specific checks to eliminate bogus results.

        The current checks:
            - date is an int between 1600 and current year + 1
            - tracktotal is an int equal to the number of tracks in directory
            - tracknumbers are sequential ints -- none are missing or repeated
        
        Possible checks:
            - master MB check (what exactly does this mean?)"""
        
        # Check date is an int between 1600 and current year + 1.
        for track in self.release.tracks:
            try:
                year = int(track.metadata["date"])
            except ValueError:
                raise ReleaseManagerError, "Year is not an integer."
            if not functions.isDate(year):
                raise ReleaseManagerError, "Year is not between 1600 and current year + 1."
        
        # Check tracktotal is equal to number of tracks in the directory.
        for track in self.release.tracks:
            try:
                tracktotal = int(track.metadata["tracktotal"])
            except ValueError:
                raise ReleaseManagerError, "Tracktotal is not an integer."
            if tracktotal != len(track.parent.tracks):
                raise ReleaseManagerError, "Tracktotal does not equal number of tracks in directory indicating one or more tracks are missing."
                    
        # Check tracks are sequential -- none missing or repeated.
        tracknumbers = []
        for track in self.release.tracks:
            try:
                tracknumber = int(track.metadata["tracknumber"])
            except:
                raise ReleaseManagerError, "One or more tracknumber is not an integer."
            if not functions.isTrackNumber(tracknumber):
                raise ReleaseManagerError, "Track number is not between 1 and 40."
            tracknumbers.append(tracknumber)
        tracknumbers.sort()
        
        for i in range(tracknumbers[-1]):
            if not (i + 1) in tracknumbers:
                raise ReleaseManagerError, "The release is missing one or more tracks."

        if len(tracknumbers) > tracknumbers[-1]:
            # TODO: Choose the better version of the repeated track
            raise ReleaseManagerError, "The release has one or more repeated and missing tracks."
                
        # One master MB sanity check, coming up... later.
        # Coming up next week.
        
    def writeResults(self):
        """After tags have been found, write tags and filenames for all tracks."""

        flowcontrol.checkpoint()
        
        for track in self.release.tracks:
            flowcontrol.checkpoint(pauseOnly=True)
            
            logger.log("Writing tags for %s." % quote(track.fileName), "Actions")
            logger.startSection()
            track.writeTags()
            logger.endSection()

            logger.log("Writing filename for %s." % quote(track.fileName), "Actions")
            logger.startSection()
            track.rename()
            logger.endSection()
            
    def getNewPath(self):
        """Return the new path to the album based on the metadata.

        Format: Genre/Artist/Year - Album/
        If no genre was found, "[None]" is used."""
        
        metadata = self.release.metadata
        genre = metadata.get("genre", "[None]")
        return os.path.join(translateForFilename(genre), translateForFilename(metadata["artist"]),
            "%s - %s" % (metadata["date"], translateForFilename(metadata["release"])) )

class Release(object):
    """Represents one audio release.

    Release's purpose is store:
        - the directory path of audio
        - the known release-specific metadata
        - the Track objects representing the tracks"""
    
    def __init__(self, directoryPath, audioFilePaths):
        getPUID = configuration.SETTINGS["GET_PUID"]
        if getPUID:
            logger.log("Fingerprinting audio files and searching for matches in MusicDNS database.", "Actions")
            logger.startSection()
        
        self.tracks = [Track(self, filePath) for filePath in audioFilePaths]
        
        if getPUID:
            logger.endSection()
        self.metadata = {}
        self.directoryPath = directoryPath
        self.directoryName = os.path.basename(directoryPath)
        
    def storeData(self, field, data):
        """Store found value in known metadata dict and in tracks."""
        
        self.metadata[field] = data
        for track in self.tracks:
            track.storeData(field, data)


class Track(object):
    """Represents one audio track.

    Track's purpose is to store:
        - the track's file name and path
        - the results of getPUID (if any)
        - the known metadata"""
    
    def __init__(self, parent, filePath):
        self.parent = parent
        self.metadata = {}
        self.filePath = filePath
        self.fileName = os.path.basename(filePath)
        self.PUID = getters.fetchPUID(self.filePath)

    def storeData(self, field, data):
        """Store found value in known metadata dict."""
        
        self.metadata[field] = data
    
    def writeTags(self):
        """Clear the current track tags and write what we've found."""

        logger.log("Clearing current tags.", "Details")
        tagging.clearTags(self.filePath)
        logger.log("Writing these tags:", "Details")
        for field in self.metadata:
            logger.log("    %s%s" % (field.ljust(20), self.metadata[field]), "Details")
            tagging.setTag(self.filePath, field, self.metadata[field])

    def rename(self):
        """Rename the file to [tracknumber] - [title].[ext]."""

        newBaseName = self.metadata["tracknumber"].rjust(2, u"0")
        newBaseName += " - " + translateForFilename(self.metadata["title"])
        oldBaseName, ext = os.path.splitext(self.fileName)
        newPath = self.filePath.replace(oldBaseName, newBaseName)
        if not os.path.exists(newPath):
            logger.log("Renaming " + quote(oldBaseName) + " to " + quote(newBaseName), "Details")
            shutil.move(self.filePath, newPath)
        elif newBaseName == oldBaseName:
            logger.log("Old filename is correct. No renaming necessary.", "Details")
        else:
            logger.log("Cannot rename %s. There already exists a file with the target filename." % quote(oldBaseName), "Errors")
            logger.log("Target filename: %s" % quote(newBaseName), "Debugging")
            raise ReleaseManagerError, "Target filename already exists."