# -*- coding: utf-8 -*-

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

import tagging
import getters
import flowcontrol
import logger
from utils import *

class AbstractFinder(object):
    """Base class for all Finders."""
    
    def findConsensus(self, data):
        """Take data from getters and find the value with the highest score."""
        
        flowcontrol.checkpoint()
        
        # Create a dictionary of values to sums of weights while removing null results.
        scores = {}
        for (candidate, weight, name, track) in data:
            if candidate:
                scores[candidate] = scores.get(candidate, 0) + weight
        
        # Ensure that we have data, otherwise return None indicating failure
        if not scores:
            logger.log("Unable to find consensus -- no getters returned valid results.", "Failures")
            return None
        
        # Put the results in a list so we can sort.
        listed = [(scores[candidate], candidate) for candidate in scores]
        listed.sort(reverse=True)
        
        # TODO: Check that result meets some threshold.
        
        # Display the results.
        topScore, winningCandidate = listed[0]
        logger.log(str(listed), "Debugging")
        logger.log("Top Score: %d" % topScore, "Debugging")
        logger.log("Winning Candidate: %s" % winningCandidate, "Debugging")
        
        return winningCandidate
    
    def storeData(self, obj, consensus):
        """Add consensus data to a Release or Track's known metadata."""
        
        obj.storeData(self.fieldName, consensus)
        
    def getTag(self, track):
        """Return the current tag."""
        
        logger.log("Getting current value of tag.", "Actions")
        logger.startSection()
        result = o_o(tagging.getTag(track.filePath, self.fieldName))
        logger.endSection()
        return result
    
    def getMBTag(self, track):
        """Fuzzily match current value in tag using MusicBrainz."""

        logger.log("Matching current value of tag in MusicBrainz.", "Actions")
        logger.startSection()
        
        tag = tagging.getTag(track.filePath, self.fieldName)
        if not tag:
            logger.log("Unable to match because current tag is empty.", "Failures")
            result = None           
        else:
            result = getters.mbInterface(self.fieldName, tag, track)
        
        logger.endSection()
        return result


class AbstractReleaseFinder(AbstractFinder):
    """Base class for release-specific data Finders."""
    
    def run(self, release):
        """Gather release data and find a consensus."""

        logger.log("Gathering %s data from %d sources." % (self.fieldName, len(self.getters)), "Actions")
        logger.startSection()
        
        data = []
        for track in release.tracks:
            logger.log("\nActing on track %s." % quote(track.fileName), "Actions")
            logger.startSection()
            for (getter, weight) in self.getters:
                    flowcontrol.checkpoint()
                    logger.log(" ", "Actions")   # Acts as a newline
                    data.append((getter(track), weight, getter.__name__, quote(track.fileName)))
            #logger.log(" ", "Actions")
            logger.endSection()
        
        logger.log("\nResults:", "Debugging")
        for (candidate, weight, name, fileName) in data:
            logger.log("     %s%s%s" % (name.ljust(30), fileName.ljust(60), candidate) , "Debugging")
        logger.endSection()

        logger.log("\nFinding the result which recieved the most points.", "Actions")
        logger.startSection()
        consenus = self.findConsensus(data)
        logger.endSection()
        
        if consenus:
            self.storeData(release, consenus)
            return True
        else:
            return False


class AbstractTrackFinder(AbstractFinder):
    """Base class for track-specific data Finders."""
    
    def run(self, release):
        """Gather track-specific data and find a consensus."""
        
        results = []
        
        for track in release.tracks:
            logger.log("Attempting to determine %s for %s." % (self.fieldName, quote(track.fileName)), "Actions")
            logger.startSection()

            logger.log("Gathering data from %d sources." % len(self.getters), "Actions")
            logger.startSection()
            data = []
            for (getter, weight) in self.getters:
                flowcontrol.checkpoint()
                data.append((getter(track), weight, getter.__name__, quote(track.fileName)))
                logger.log(" ", "Actions")   # Acts as a newline
                
            logger.log("\nResults:", "Debugging")
            for (candidate, weight, name, fileName) in data:
                    logger.log("     %s%s%s" % (name.ljust(30), fileName.ljust(60), candidate) , "Debugging")
            logger.endSection()
            
            logger.log("\nFinding the result which recieved the most points.", "Actions")
            logger.startSection()
            consensus = self.findConsensus(data)
            logger.endSection(2)

            if consensus:
                results.append((track, consensus))
            else:
                return False
            
            logger.log(" ", "Actions")
                
        for (track, consensus) in results:
            self.storeData(track, consensus)
        return True

