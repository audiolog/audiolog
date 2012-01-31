# -*- coding: utf-8 -*-

#  Audiolog Music Organizer
#  Copyright © 2011  Matt Hubert <matt@cfxnetworks.com> 
#                    Robert Nagle <rjn945@gmail.com>
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""ReleaseManager manages the gathering and writing of one release's metadata.

The Overview

The metadata gathering process is the most important and most complex task
that Audiolog performs. The goal of this process is simple: Find complete,
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
|              tagging                 |   musicbrainz   |   fingerprint     |
|--------------------------------------|-----------------|-------------------|
|              Mutagen                 |   MusicBrainz   |    MusicDNS       |
|--------------------------------------|-----------------|-------------------|

"""

import shutil
from collections import defaultdict

from etc import flowcontrol
from etc import functions
from etc import configuration
from etc.utils import *
from etc.logger import log, logfn, logSection

from finders.ArtistFinder import ArtistFinder
from finders.ReleaseFinder import ReleaseFinder
from finders.DateFinder import DateFinder
from finders.TrackTotalFinder import TrackTotalFinder
from finders.TitleFinder import TitleFinder
from finders.TrackNumberFinder import  TrackNumberFinder
from finders.GenreFinder import GenreFinder

import fingerprint
import tagging

class ReleaseManagerError(Exception):
    """Raised when a problem will keep the release from being tagged."""

    pass


class ReleaseManager(object):
    """Manages the gathering and writing of one release's metadata."""
    
    def __init__(self, directoryPath, audioFilePaths):
        self.release = Release(directoryPath, audioFilePaths)
        self.queue = [ArtistFinder(), ReleaseFinder(), DateFinder(), 
                      TrackTotalFinder(), TrackNumberFinder(), TitleFinder(), 
                      GenreFinder()]
        self.nextRoundQueue = []
        
    def run(self):
        """Fingerprint audio, find metadata, check sanity, write tags and filenames."""

        if configuration.SETTINGS["GET_PRINT"]:
            self.getMusicDNS()
        self.gatherMetadata()
        self.checkSanity()
        self.writeResults()
        
    def logInitialState(self):
        """Log the initial state of the filenames, tags and MusicDNS results.
        
        TODO: Complete this function and use it or remove it."""

        for track in self.release.tracks:
            log("File path: %s" % track.filePath, "Debugging")
            
    @logfn("\nFingerprinting audio files and searching for matches in MusicDNS.")
    def getMusicDNS(self):
        """Fingerprint each track and look for matches in MusicDNS."""
        
        import musicdns
        musicdns.initialize()
        for track in self.release.tracks:
            track.getMusicDNS()
        musicdns.finalize()

    @logfn("\nGathering metadata.")
    def gatherMetadata(self):
        """Iterate through Finders until success or stagnation."""

        while self.queue:
            for finder in self.queue:
                field = finder.fieldName
                
                with logSection("\nAttempting to determine the %s using %d sources." 
                                % (field, len(finder.getters))):
                    success = finder.run(self.release)
                
                if not success:
                    log("Failed to determine the %s. Will try again next round.\n"
                        % field)
                    self.nextRoundQueue.append(finder)
                else:
                    log("Successfully determined the %s.\n" % field)
            
            if self.queue == self.nextRoundQueue:
                log("No progress has been made. The metadata gathering process "
                    "has failed.\n")
                failedFields = [finder.fieldName for finder in self.queue]
                raise ReleaseManagerError, "Unable to determine: %s" % failedFields
            else:
                self.queue = self.nextRoundQueue
                self.nextRoundQueue = []
        
    @logfn("\nChecking for errors in the results.")
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
                raise ReleaseManagerError, "Year is not between 1600 and next year."
        
        # Check tracktotal is equal to number of tracks in the directory.
        for track in self.release.tracks:
            try:
                tracktotal = int(track.metadata["tracktotal"])
            except ValueError:
                raise ReleaseManagerError, "Tracktotal is not an integer."
            if tracktotal != len(track.parent.tracks):
                err = ("Tracktotal does not equal number of tracks in directory"
                       " indicating one or more tracks are missing.")
                raise ReleaseManagerError, err
                    
        # Check tracks are sequential -- none missing or repeated.
        tracknumbers = []
        for track in self.release.tracks:
            try:
                tracknumber = int(track.metadata["tracknumber"])
            except:
                raise ReleaseManagerError, "One or more tracknumber is not an integer."
            if not functions.isTrackNumber(tracknumber):
                raise ReleaseManagerError, "Track number is not between 1 and 99."
            tracknumbers.append(tracknumber)
        tracknumbers.sort()
        
        for i in range(tracknumbers[-1]):
            if not (i + 1) in tracknumbers:
                s = "The release is missing one or more tracks. "
                s += "Track numbers: " + str(tracknumbers)
                raise ReleaseManagerError, s

        if len(tracknumbers) > tracknumbers[-1]:
            # TODO: Choose the better version of the repeated track
            s = "The release has one or more repeated tracks. "
            s += "Track numbers: " + str(tracknumbers)
            raise ReleaseManagerError, s
                
        # TODO: One master MB sanity check, coming up... later.
        
    @logfn("\nWriting the results to tags and filenames.")
    def writeResults(self):
        """After tags have been found, write tags and filenames for all tracks."""

        flowcontrol.checkpoint()
        for track in self.release.tracks:
            flowcontrol.checkpoint(pauseOnly=True)
            track.writeTags()
            track.rename()
            log(" ")
            
    def getNewPath(self):
        """Return the new path to the album based on the metadata.

        Format: Genre/Artist/Year - Album/
        If no genre was found, "[None]" is used."""
        
        metadata = self.release.metadata
        genre = metadata.get("genre", "[None]")
        return os.path.join(translateForFilename(genre), 
                            translateForFilename(metadata["artist"]),
                            "%s - %s" % (metadata["date"], translateForFilename(metadata["release"])))

    
class Release(object):
    """Represents one audio release.

    Release's purpose is store:
        - the directory path of audio
        - the known release-specific metadata
        - the Track objects representing the tracks"""
    
    def __init__(self, directoryPath, audioFilePaths):
        tracks = [Track(self, filePath) for filePath in audioFilePaths]
        self.tracks = TrackList(tracks)
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
        - the results of getMusicDNS (if any)
        - the known metadata"""
    
    def __init__(self, parent, filePath):
        self.parent = parent
        self.metadata = {}
        self.filePath = filePath
        self.fileName = os.path.basename(filePath)
        self.musicDNS = defaultdict(lambda: None) # Returns None for all look-ups.

    def getMusicDNS(self):
        """Search for fingerprint match in MusicDNS and store the result."""
        
        result = fingerprint.askMusicDNS(self.filePath)
        if result:
            self.musicDNS = result

    def storeData(self, field, data):
        """Store found value in known metadata dict."""
        
        self.metadata[field] = data
    
    @logfn("Writing tags for {quote(self.fileName)}.")
    def writeTags(self):
        """Clear the current track tags and write what we've found."""

        log("Clearing current tags.")
        tagging.clearTags(self.filePath)
        log("Writing these tags:")
        for field in self.metadata:
            log("    %s%s" % (field.ljust(20), self.metadata[field]))
            tagging.setTag(self.filePath, field, self.metadata[field])

    @logfn("Writing filename for {quote(self.fileName)}.")
    def rename(self):
        """Rename the file to [tracknumber] - [title].[ext]."""

        newBaseName = self.metadata["tracknumber"].rjust(2, u"0")
        newBaseName += " - " + translateForFilename(self.metadata["title"])
        oldBaseName, ext = os.path.splitext(self.fileName)
        newPath = self.filePath.replace(oldBaseName, newBaseName)
        if not os.path.exists(newPath):
            log("Renaming %s to %s." % (quote(oldBaseName), quote(newBaseName)))
            shutil.move(self.filePath, newPath)
        elif newBaseName == oldBaseName:
            log("Old filename is correct. No renaming necessary.")
        else:
            log("Cannot rename %s." % quote(oldBaseName))
            log("There already exists a file with the target filename.")
            log("Target filename: %s" % quote(newBaseName))
            raise ReleaseManagerError, "Target filename already exists."

        
class TrackList(list):
    """Subclass of list to print list of tracks nicely."""
    
    def __repr__(self):
        return "<%d Tracks>" % len(self)

