# -*- coding: utf-8 -*-

#  Audiolog Music Organizer
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

"""Base class for audio field Finders.

Class hierarchy:

AbstractFinder
    |
    |---AbstractReleaseFinder
    |       |---ArtistFinder
    |       |---ReleaseFinder
    |       |---DateFinder
    |       |---TracktotalFinder
    |       |---GenreFinder
    |     
    |---AbstractTrackFinder
            |---TitleFinder
            |---TrackNumberFinder"""

from metadata import tagging
from metadata import musicbrainz as mb

from etc import flowcontrol
from etc.utils import *
from etc.logger import log, logfn, logSection

class AbstractFinder(object):
    """Base class for all Finders."""

    def logResults(self, results):
        """Logs the results in a tabular format."""
        
        log("\nResults:")
        for (candidate, weight, name, fileName) in results:
            log("     %s%s%s" % (name.ljust(30), fileName.ljust(80), candidate))
    
    @logfn("\nFinding the result which recieved the most points.")
    def findConsensus(self, data):
        """Take data from getters and find the value with the highest score."""
        
        flowcontrol.checkpoint()
        
        # Create a dict of values to sums of weights while removing null results.
        scores = {}
        for (candidate, weight, name, track) in data:
            if candidate:
                scores[candidate] = scores.get(candidate, 0) + weight
        
        # Ensure that we have data, otherwise return None indicating failure
        if not scores:
            log("Unable to find consensus -- no getters returned valid results.")
            return None
        
        # Put the results in a list so we can sort.
        listed = [(scores[candidate], candidate) for candidate in scores]
        listed.sort(reverse=True)
        
        # TODO: Check that result meets some threshold.
        
        # Display the results.
        topScore, winningCandidate = listed[0]
        log("Candidates: %s" % listed)
        log("Top Score: %d" % topScore)
        log("Winning Candidate: %s" % winningCandidate)
        
        return winningCandidate
        
    @logfn("Getting current value of tag.")
    def getTag(self, track):
        """Return the current tag."""
        
        return tagging.getTag(track.filePath, self.fieldName) or None
    
    @logfn("Matching current value of tag in MusicBrainz.")
    def getMBTag(self, track):
        """Fuzzily match current value in tag using MusicBrainz."""

        tag = tagging.getTag(track.filePath, self.fieldName)
        if not tag:
            log("Unable to match because current tag is empty.")
            result = None           
        else:
            result = mb.askMB(self.fieldName, tag, track)
        
        return result


class AbstractReleaseFinder(AbstractFinder):
    """Base class for release-specific data Finders."""
    
    def run(self, release):
        """Gather release data and find a consensus."""
        
        data = []
        for track in release.tracks:
            with logSection("\nActing on track %s." % quote(track.fileName)):
                for (getter, weight) in self.getters:
                        flowcontrol.checkpoint()
                        log(" ") 
                        data.append((getter(track), 
                                     weight, 
                                     getter.__name__, 
                                     quote(track.fileName)))
        
        self.logResults(data)
        
        consenus = self.findConsensus(data)
        log(" ")
        
        if consenus:
            release.storeData(self.fieldName, consenus)
            return True
        else:
            return False


class AbstractTrackFinder(AbstractFinder):
    """Base class for track-specific data Finders."""
    
    def run(self, release):
        """Gather track-specific data and find a consensus."""
        
        results = []
        
        for track in release.tracks:
            with logSection("Attempting to determine %s for %s." % 
                            (self.fieldName, quote(track.fileName))):
                data = []
                for (getter, weight) in self.getters:
                    flowcontrol.checkpoint()
                    log(" ")
                    data.append((getter(track), 
                                 weight, 
                                 getter.__name__, 
                                 quote(track.fileName)))
                                    
                self.logResults(data)
                
                consensus = self.findConsensus(data)
    
                if consensus:
                    results.append((track, consensus))
                else:
                    return False
                
            log(" ")
                
        for (track, consensus) in results:
            track.storeData(self.fieldName, consensus)
        return True
