# -*- coding: utf-8 -*-

#  Azul Music Organizer
#  Copyright © 2009  Matt Hubert <matt@cfxnetworks.com> and Robert Nagle <rjn945@gmail.com>
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

from tagging:

    def printAudioInfo(filePath):
        """Takes a path to an OGG or MP3 and print the info we can find"""
        
        audioFile = openAudioFile(filePath)
        log("Info for " + quote(filePath) + ":", 
        for key in audioFile:
            print key
            print "\t", audioFile[key]
        print "Length:\n\t", audioFile.info.length
        print "Bitrate:\n\t", audioFile.info.bitrate
    
from traverse:
    
    # Display subdirectories
    if subdirectoryPaths:
        log("\tsubdirectoryPaths", "Debugging")
        for subdirectoryPath in subdirectoryPaths:
            log("\t\t" + quote(subdirectoryPath), "Debugging")
            
            
    # Display files
    if subdirectoryPaths:
        log("\nBack in " + quote(directoryPath), "Debugging")
            
    if filePaths:
        log("\tfilePaths", "Debugging")
        for filePath in filePaths:
            log("\t\t" + quote(filePath), "Debugging")
        
        log("\tfilePathsByType", "Debugging")
        for fileType in filePathsByType:
            log("\t\t" + fileType, "Debugging")
            for filePath in filePathsByType[fileType]:
                log("\t\t\t" + quote(filePath), "Debugging")
                

from extract:

    def makeDestDirectory(archivePath):
        directoryPath = os.path.splitext(archivePath)[0]
        if not os.path.exists(directoryPath): os.mkdir(directoryPath)
        return directoryPath

    def unzip(archivePath, destDirectoryPath):
        return os.system('unzip "' + archivePath + '" -d "' + destDirectoryPath + '"')

    def unrar(archivePath, destDirectoryPath):
        return os.system('unrar x "' + archivePath + '" "' + destDirectoryPath + '"')

    def untar(archivePath, destDirectoryPath):
        return os.system('tar -xf "' + archivePath + '" "' + destDirectoryPath + '"')

    def ungz(archivePath, destDirectoryPath):
        return os.system('tar -zxf "' + archivePath + '" "' + destDirectoryPath + '"')

    def unbz2(archivePath, destDirectoryPath):
        return os.system('tar -jxf "' + archivePath + '" "' + destDirectoryPath + '"')

    def unace(archivePath, destDirectoryPath):
        return os.system('unace x -y "' + archivePath + '" "' + destDirectoryPath + '/"') # unace is fucked up...

    def un7z(archivePath, destDirectoryPath):
        return -1

    def defaultExtractor(archivePath, destDirectoryPath):
        return -1

    extractorFunctions = {".zip": unzip, ".rar": unrar, ".tar": untar, ".gz": ungz,
                            ".bz2": unbz2, ".ace": unace, ".7z": un7z}


from convert:

    def convertWAV(filePath):
        command = 'oggenc -q ' + str(configuration.ENCODING_QUALITY["HIGH"]) + ' "%s.wav"' % filePath
        log(command, "Commands")
        return os.system(command)

    def convertFLAC(filePath):
        command = 'oggenc -q ' + str(configuration.ENCODING_QUALITY["HIGH"]) + ' "%s.flac"' % filePath
        log(command, "Commands")
        return os.system(command)

    def convertAPE(filePath):
        command = 'mac "$$.ape" "$$.wav" -d; \noggenc -q ' + str(configuration.ENCODING_QUALITY["HIGH"]) + ' "$$.wav"'
        command = command.replace("$$", filePath)
        log(command, "Commands")
        return os.system(command)

    def convertMPC(filePath):
        command = 'mpc123 -w "$$.wav" "$$.mpc"; \noggenc -q ' + str(configuration.ENCODING_QUALITY["MEDIUM"]) + ' "$$.wav"'
        command = command.replace("$$", filePath)
        log(command, "Commands")
        return os.system(command)

    def defaultConvertor(filePath):
        return

    convertorFunctions = {".ape": convertAPE, ".flac": convertFLAC, ".wav": convertWAV, ".mpc": convertMPC}



from the_old_getters.getFilename release:
        # Get a list of every possible release title
        results = re.split(delimiters, containingDirName) 
        for i in range(len(results)):
            results[i] = results[i].strip()
        results = [result for result in results if result] # Remove empty entires
        
        releases = []
        query = mb.Query()
        
        for result in results:
            params = mb.ReleaseFilter(title = result, artistName = track.track["artist"], limit = 1)
            result = getMB(query.getReleases, params)
            
            if len(result) > 0: # If result is found in MB
                releases.append(result[0].getRelease().getTitle())
        
        if len(releases) == 1: # We found a match
            return releases[0]
        elif len(releases) == 2: # We found a match, but one may be a false positive
            if functions.aboutEqual(track.track["artist"], releases[0]):
                print "Returning", releases[1]
                return releases[1] # Return the one that isn't self-titled
            elif functions.aboutEqual(track.track["artist"], releases[1]):
                print "Returning", releases[0]
                return releases[0]
            else:
                print "Two different non-artist release names found"
                return ""
        else:
            print len(releases), "possible releases found in filename."
            if releases:
                print "\tPossible releases:", releases
            print "Unable to determine a release from filename."
            return ""

from the_old_getters.getFilename title:
        # Get a list of every possible release title
        results = re.split(delimiters, baseName) 
        for i in range(len(results)):
            results[i] = results[i].strip()
        results = [result for result in results if result] # Remove empty entires
        
        titles = []
        query = mb.Query()
        
        for result in results:
            params = mb.TrackFilter(title = result, artistName = track.track["artist"], releaseTitle = track.track["release"], limit = 1)
            result = getMB(query.getTracks, params)
        
            if len(result) > 0:
                titles.append(result[0].getTrack().getTitle())
        
        if len(titles) == 1: # We found a match
            return titles[0]
        elif len(titles) == 2: # We found a match, but one may be a false positive
            if functions.aboutEqual(track.track["artist"], titles[0]):
                print "Returning", titles[1]
                return titles[1] # Return the one that isn't self-titled
            elif functions.aboutEqual(track.track["artist"], titles[1]):
                print "Returning", titles[0]
                return titles[0]
            else:
                print "Two different non-artist titles found"
                return ""
        else:
            print len(titles), "possible titles found in filename."
            if titles:
                print "\tPossible titles:", titles
            print "Unable to determine a title from filename."
            return ""

from the_old_getters:

    def getMB(track, field, filt):
        """Construct and execute a MusicBrainz query."""

        query = mb.Query()

        if field == "artist":
            params = mb.ArtistFilter(name = filt, limit = 1)
            result = getMB(query.getArtists, params)

            if len(result) > 0:
                return result[0].getArtist().getName()
            else:
                return ""

        elif field == "release":
            params = mb.ReleaseFilter(title = filt, artistName = track.track["artist"], limit = 1)
            result = getMB(query.getReleases, params)

            if len(result) > 0:
                return result[0].getRelease().getTitle()
            else:
                return ""

        elif field == "date":
            params = mb.ReleaseFilter(title = track.track["release"], artistName = track.track["artist"], limit = 1)
            result = getMB(query.getReleases, params)

            if len(result) > 0:
                if result[0].getRelease().getEarliestReleaseDate():
                    return result[0].getRelease().getEarliestReleaseDate().split("-")[0]
                else:
                    return ""
            else:
                return ""

        elif field == "tracktotal":
            params = mb.ReleaseFilter(title = track.track["release"], artistName = track.track["artist"], limit = 1)
            result = getMB(query.getReleases, params)

            if len(result) > 0:
                tracktotal = result[0].getRelease().getTracksCount()
                return unicode(tracktotal).rjust(2, u"0")
            else:
                return ""

        elif field == "title":
            params = mb.TrackFilter(title = tag, artistName = track.track["artist"], releaseTitle = track.track["release"])
            result = getMB(query.getTracks, params)

            if len(result) > 0:
                return result[0].getTrack().getTitle()
            else:
                return ""

        elif field == "tracknumber":
            params = mb.TrackFilter(title = track.track["title"], artistName = track.track["artist"], releaseTitle = track.track["release"])
            result = getMB(query.getTracks, params)

            if len(result) > 0:
                tracknumber = result[0].getTrack().getReleases()[0].getTracksOffset() + 1  # Track numbers are zero-indexed.
                return unicode(tracknumber).rjust(2, u"0")
            else:
                return ""

    def getMB(track, field, filt=None):
        """Construct and execute a MusicBrainz query."""

        query = mb.Query()
        queryFunctions = {"artist"     : query.getArtists,
                        "release"    : query.getReleases,
                        "date"       : query.getReleases,
                        "tracktotal" : query.getReleases,
                        "title"      : query.getTracks,
                        "tracknumber": query.getTracks}

        # Construct filter
        if field == "artist":
            params = mb.ArtistFilter(name=filt, limit=1)
        elif field == "release":
            params = mb.ReleaseFilter(title=filt, artistName=track.track["artist"], limit=1)
        elif field == "date" or field == "tracktotal":
            params = mb.ReleaseFilter(title=track.track["release"], artistName=track.track["artist"], limit=1)
        elif field == "title":
            params = mb.TrackFilter(title=filt, artistName=track.track["artist"], releaseTitle=track.track["release"])
        elif field == "tracknumber":
            params = mb.TrackFilter(title=track.track["title"], artistName=track.track["artist"], releaseTitle=track.track["release"])

        result = queryMB(queryFunctions[field], params)

        # Return results, if they are valid
        if len(result) > 0:
            if field == "artist":
                return result[0].getArtist().getName()
            elif field == "release":
                return result[0].getRelease().getTitle()
            elif field == "date":
                if result[0].getRelease().getEarliestReleaseDate():
                    return result[0].getRelease().getEarliestReleaseDate().split("-")[0]
            elif field == "tracktotal":
                tracktotal = result[0].getRelease().getTracksCount()
                return unicode(tracktotal).rjust(2, u"0")
            elif field == "title":
                return result[0].getTrack().getTitle()
            elif field == "tracknumber":
                tracknumber = result[0].getTrack().getReleases()[0].getTracksOffset() + 1  # Track numbers are zero-indexed.
                return unicode(tracknumber).rjust(2, u"0")
        return ""  # De facto else clause

    #-------------------------------------------
    # Getter Functions
    #-------------------------------------------

    def getMBPUID(track):
        """Return the metainformation given from MusicBrainz via PUID."""

        if not track.PUID[2]:
            log("Cannot perform lookup because we never found a PUID.", 7, "Failures")
            return ""

        query = mb.Query()
        params = mb.TrackFilter(puid = track.PUID[2], limit = 1)
        result = queryMB(query.getTracks, params)

        return result

    def getmbTag(track, field):
        """Return the metainformation for field by looking it up in MusicBrainz."""

        if field == "artist" or field == "release" or field == "title":
            tag = tagging.getTag(track.filePath, field)
            if not tag:
                log("Tag is empty. Unable to match against MusicBrainz.", 7, "Failures")
                return ""
            return matchMB(track, field, tag)
        else:
            return getMB(track, field)

    def getTag(track, field):
        """Return the value in the tags for field."""

        return tagging.getTag(track.filePath, field)

    def getFilename(track, field):
        """Return information pulled from the file name and path."""

        if field == "tracknumber":
            tracknum = re.compile("(?<!\d)\d{1,2}(?=\D)")  # One or two digits
            match = tracknum.search(track.baseName)
            if match:
                digits = match.group()
                return unicode(digits).rjust(2, u"0")

        elif field == "date":
            match = re.findall("\d{4}", track.filePath) # Four adjacent digits
            if match:
                return unicode(match[-1]) # Return the last match (closest to the end of the filePath)

        elif field == "tracktotal":
            return unicode(len(track.parentRelease.tracks)).rjust(2, u"0")

        elif field == "release":
            containingDirName = functions.containingDir(track.filePath)

            # Remove leftmost year, if one
            match = re.findall("\d{4}", containingDirName)
            if match:
                containingDirName = containingDirName.replace(match[0], "")

            return matchMB(track, "release", containingDirName)

        elif field == "title":
            baseName = os.path.splitext(track.baseName)[0]

            # Remove track number if one
            tracknum = re.compile("(?<!\d)\d{1,2}(?=\D)")
            match = tracknum.search(baseName)
            if match:
                baseName = baseName.replace(match.group(), "")

            return matchMB(track, "title", baseName)

        return ""



from track:

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



from release:

    # -*- coding: utf-8 -*-

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


from logger:

    def log(message, level, category):
        """Emit AppendToLog signal."""

        global lastLevel

        if level < 0:
        level = lastLevel-level
        else:
        lastLevel = level

        if message[0] == "\n":
        message = "\n" + "    "*level + message
        else:
        message = "    "*level + message

        if message[-1] != "." and message[-1] != "\n":
        message += "."

        emitter.emit(SIGNAL("AppendToLog"), message, level, category)



from audio:

    def handleAudio(directoryPath, audioFilePaths):
        "Create and run a Release object."

        album = release.Release(directoryPath, audioFilePaths)
        try:
            album.do()
        except release.ReleaseError:
            log("Attempt to identify and tag audio failed.\n", 3, "Errors")
            functions.rejectItem(directoryPath)
        else:
            log("Attempt to identify and tag audio succeeded.", 3, "Successes")
            log("Directory has been sorted successfully.\n", 2, "Successes")
            functions.acceptItem(directoryPath, album.getNewPath())


from the_new_getters.applyMBParams:

        convDict = {"release": "title"}
        for key in convDict:
            if key in params and params[key]:
                newParams[convDict[key]] = params[key]
                