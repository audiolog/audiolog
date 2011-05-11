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
        maxGetter = max([len(getter) for _, _, getter, _ in results])
        maxFilename = max([len(filename) for _, _, _, filename in results])
        for (candidate, weight, getter, fileName) in results:
            log("     %s%s%s" % (getter[3:].ljust(maxGetter), 
                                 fileName.ljust(maxFilename+3), 
                                 candidate if candidate else ""))
    
    @logfn("\nFinding the result which received the most points.")
    def findConsensus(self, data):
        """Take data from getters and find the value with the highest score.
        
        Candidates that differ by only capitalization and punctuation are
        grouped together for scoring.
        
        Example:
        If the scores come back
            5  Chick Corea
            4  Song of Singing
            3  Song Of Singing
        then the "song of singing" group will win with 7 points and the
        "Song of Singing" candidate will be chosen because it is the highest
        scoring candidate of that group."""
    
        flowcontrol.checkpoint()
        
        # Create a dict of values to sums of weights while removing null results.
        scores = {}
        groupScores = {}
        for (candidate, weight, name, track) in data:
            if candidate:
                group = restrictChars(candidate, punctuation=False).lower()
                scores[candidate] = scores.get(candidate, 0) + weight
                groupScores[group] = groupScores.get(group, 0) + weight
                
        # Ensure that we have data, otherwise return None indicating failure
        if not scores:
            log("Unable to find consensus -- no getters returned valid results.")
            return None
        
        # Rank the groups and the candidates
        groups = [(score, group) for group, score in groupScores.items()]
        groups.sort(reverse=True)
        candidates = [(score, candidate) for candidate, score in scores.items()]
        candidates.sort(reverse=True)
        
        # Display candidates (and groups, if different).
        log("Candidates:")
        for score, candidate in candidates:
            log("  %s  %s" % (str(score).rjust(4), candidate))
            
        if len(groups) != len(candidates):
            log("\nGroups:")
            for score, group in groups:
                log("  %s  %s" % (str(score).rjust(4), group))
        
        # Pick the highest member of the winning group.
        topGroupScore, topGroup = groups[0]
        for score, candidate in candidates:
            if restrictChars(candidate, punctuation=False).lower() == topGroup:
                return candidate
        
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
