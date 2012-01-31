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

"""High-level interface for accessing MusicBrainz.

getMBPUID looks up PUID returned by MusicDNS in MusicBrainz.

askMB constructs and executes a MusicBrainz query based on previously known 
data and/or potentially useful data.

Querying MusicBrainz is broken down into four or five parts:
    - Query construction
    - Fuzzy matching (if applicable)
    - Query execution
    - Post processing
    - Data gathering

Queries are constructed based on the requested field. Four parameters 
(artist, release, tracktotal, title) can be used directly in a Filter. 
The rest must be used in post processing.

A query is executed by first mapping Audiolog's standardized naming convention 
to MusicBrainz' (somewhat arbitrary) naming convention, depending on the 
requested record. Actually connecting to MusicBrainz occurs in contactMB.

Dates, track numbers, and titles are verified in post processing. For titles 
specifically, the contents of each release must be received and the titles must 
be verified one by one.

Finally, the requested field is extracted from the first found (best match) 
record, if MusicBrainz returned one that made it through post-processing.


==MusicBrainz Interface==

The system for using MusicBrainz is designed with 3 goals:
    1. Create one clean, simple, consistent interface for all callers and calls
       to use. The function askMB meets these goals.
    2. Allow for the most powerful possible uses of MusicBrainz even if they
       are not provided for or intended by the MusicBrainz interface 
       designers. We meet this goal in part by doing powerful post-processing
       of queries, which allows callers to provide dates or Track objects in
       the same manner as any other type of filter data even though
       MusicBrainz does not directly support this.
    3. Separate each step of the MusicBrainz process into its own function
       for ease of understanding and maintenance.
       
       
==Illustration of MusicBrainz Process==

                 askMB                     |
                   |                       |
            constructFilter                |
              |          |                 |
    findExactMatch    findFuzzyMatch       |
              |          |                 |
              executeQuery                 |
                   |                       |
          getFunctionAndFilter           Time
                   |                       |
              applyParams                  |
                   |                       |
               contactMB                   |
                   |                       |
           requireDesiredInfo              |
                   |                       |
           postProcessResults              |
                   |                       |
              parseResults                 V
"""

import os.path
import subprocess
import time
import re
import difflib

import musicbrainz2.model
import musicbrainz2.wsxml
import musicbrainz2.webservice as mbws

from etc.cache import memoizeMB
from etc import configuration
from etc import functions
from etc.utils import *
from etc.logger import log, logfn, logSection

mbws.WebService._openUrl = memoizeMB(mbws.WebService._openUrl)

#-------------------------------------------
# Externally-called functions
#-------------------------------------------

def getMBPUID(puid, field):
    """Return the metainformation given from MusicBrainz via PUID."""

    if not puid:
        log("Cannot perform lookup because we never found a PUID.")
        return None
    
    query = mbws.Query()
    params = [mbws.TrackFilter(puid=puid, limit=1)]
    result = contactMB(query.getTracks, params)
    
    if not result:
        log("MusicBrainz did not recognize the PUID.") 
        return None
    
    if field == "artist":
        return result[0].getTrack().getArtist().getName()
    elif field == "title":
        return result[0].getTrack().getTitle()

def askMB(field, match=None, track=None, relevantFields=[]):
    """Interface for Finders to access MusicBrainz.
    
    Parameters
    field: The name of the field we are looking for. Note that this does not 
           necessarily correspond to the MusicBrainz record that we use. 
           For instance, looking for the "tracktotal" field still uses the 
           Release record.
    match: The [potentially incorrect] string that field may be equal to. 
           This is used for when mbQuery is used to verify found but 
           questionable data.
    track: Track object we are seeking metadata for. This allow us access to
           the already known [correct] data.
    relevantFields: A list of which (previously known, correct) data fields
                    would be helpful in performing the current query."""
    
    pre, post, match = constructFilter(field, match, track, relevantFields)
    matcher = findFuzzyMatch if match else findExactMatch
    return matcher(field, match, track, pre, post)

#-------------------------------------------
# Internally-called functions
#-------------------------------------------

#@logfn("Constructing MusicBrainz filter.")
def constructFilter(field, match, track, relevantFields):
    """Construct prequery, postquery and match filters.
    
    The caller provides a list fields which would be helpful (or necessary) 
    for a successful query. If a consensus has already been found for these
    fields, then this data is included in the filter. 
  
    The match parameter is overloaded for two uses:
        1. For artist, release and title fields: Fuzzily match the questionable
           contents of the tag or filename.
        2. For date, tracktotal and tracknumber: These numerical fields do not
           make sense to fuzzily match. They should be used in the filter but
           they are not yet known (and hence are not stored in track.metadata).
           For these special cases we move this uncertain data into the filter
           from match and set match to None so no fuzzy matching occurs."""
    
    prequeryFields = ["match", "artist", "release", "tracktotal", "title"]
    postqueryFields = ["date", "tracknumber", "tracks"]
    
    preFilter = {}
    postFilter = {}
    
    for relevantField in relevantFields:
        if relevantField in prequeryFields:
            if relevantField == field == "tracktotal":
                preFilter[field] = match
                match = None
            else:
                preFilter[relevantField] = track.metadata.get(relevantField)
            
        elif relevantField in postqueryFields:
            if relevantField == field == "date":
                postFilter[field] = match
                match = None
            elif relevantField == field == "tracknumber":
                postFilter[field] = match
                match = None
            elif relevantField == "tracks":
                postFilter[relevantField] = track.parent.tracks
            else:
                postFilter[relevantField] = track.metadata.get(relevantField)
    
    return (preFilter, postFilter, match)

@logfn("Matching the string {quote(match)} on {field}.")
def findExactMatch(field, match, track, preFilter, postFilter):
    """Non-fuzzy matching is easy..."""
    
    return executeQuery(field, match, preFilter, postFilter)

@logfn("Fuzzily matching the string {quote(match)} on {field}.")
def findFuzzyMatch(field, match, track, preFilter, postFilter):
    """Fuzzily match unreliable data (from tags and filename) to MusicBrainz.

    Tags and filenames especially may contain special characters or extraneous
    data which will make a MusicBrainz search fail. This function removes 
    special characters and, if the full string does not match, splits it
    based on a delimiters list and tries the substrings.

    Example:

    Filename: "2000 -*- The Better Life (Advance) -[[EAK-group]]-"
    Initial search for full string fails. String is broken into substrings.
    Substrings: "2000", "The Better Life", "Advance", "EAK", "group"
    Without any other filters "The Better Life" and "Advance" will both match
    and unable to choose one over the other, we will fail.
    With a filter (like the artist or date) then only "The Better Life" will
    match and the search will succeed.
    
    Fuzzy matching is only used for artist, release and title fields, because
    these are the only fields with strings to fuzzily match against."""
    
    if isinstance(match, FilepathString):
        log("Splitting path into directory and file name, then trying each.")
        dirName, fileName = os.path.split(match)
        
        dirResult = executeQuery(field, dirName, preFilter, postFilter)
        if dirResult:
            # We won't look to see if the filename matches, because even if it
            # did, the directory generally has better odds of containing 
            # an artist or release anyway. (We know we are looking for an 
            # artist or release, because only requests for those fields pass in 
            # a filepath. Track title requests just pass in the file name.)
            return dirResult
        
        fileResult = executeQuery(field, fileName, preFilter, postFilter)
        if fileResult:
            return fileResult
    
    else:
        result = executeQuery(field, match, preFilter, postFilter)
        if result:
            return result
    
    delimiters = r"[/()\-~+_\[\]\{\}*]"
    substrings = re.split(delimiters, match)
    substrings = [string.strip() for string in substrings if string.strip()]
    
    log("MB did not find a match for the full string.")    
    log("Searching for a match in substrings.")
    log("Substrings: %s\n" % substrings)

    matches = set()
    whatFromWhere = {}
    for substring in substrings:
        result = executeQuery(field, substring, preFilter, postFilter)
        if result:
            whatFromWhere[result] = substring
            matches.add(result)
    
    if len(matches) > 1:
        # If we have more than one result, attempt to remove matches which 
        # probably are not correct until we have only one match left or we run
        # out of methods for removing bogus results.
        # Potentially bogus results are removed in the order of the likelihood that
        # they are incorrect.
        #
        # The current filters (in order):
        #   - result is very different from substring
        #   - result looks like tracknumber or year
        #   - result is digits
        #   - result is (about) equal to already known artist, release or title
        #   - substring was digits
        
        # TODO:
        #   Order tests correctly.
        #   Use difflib in addition to aboutEqual.
        #   Use two levels of delimiters.
        #   Add filter to remove results which are (about) equal to one another.
        # 
        #   Order #1 (filter all results, filter all substring)
        #   - result looks like tracknumber or year
        #   - result is digits
        #   - result is (about) equal to already known artist, release or title
        #
        #   - substring looked like tracknumber or year
        #   - substring was digits
        #   - substring was (about) equal artist, release, title
        #
        #   Order #2 (filter result then substring, then next filter)
        #   - result looks like tracknumber or year
        #   - substring looked like tracknumber or year    
        #
        #   - result is digits
        #   - substring was digits    
        #
        #   - result is (about) equal to already known artist, release or title
        #   - substring was ... artist, release, title
    
        log("Multiple substrings matched: %s" % matches)
        log("Removing matches which are probably wrong.")
        
        # Remove matches which are either a tracknumber or a year.
        # Tracknumbers are identified by being one or two digits (possibly with
        # leading zero) under 99.
        # Years are four consecutive digits between 1600 and current year + 1.
        for match in matches.copy():
            if len(matches) > 1:        
                if match.isdigit():
                    num = int(match)
                    if functions.isTrackNumber(num) or functions.isDate(num):
                        matches.remove(match)
            else:
                break
        
        # Remove matches which are just digits.
        for match in matches.copy():
            if len(matches) > 1:        
                if match.isdigit():
                    matches.remove(match)
            else:
                break
        
        # Remove results which came from strings of digits.
        for match in matches.copy():
            if len(matches) > 1:
                if whatFromWhere[match].isdigit():
                    matches.remove(match)
            else:
                break
        
        # If we still have more than one result, than we will remove values that
        # are known to be correct for a different field. In particular, we'll
        # look at the artist, album and title fields and remove matches
        # equivalent to those fields - in that order.
        relatedFields = ["artist", "release", "title"]
        relatedFields.remove(field)
        relatedData = []
        for field in relatedFields:
            if field in track.metadata:
                relatedData.append(track.metadata[field])
        
        # Remove matches which are the same as the already known artist, 
        # release or title intelligently.
        # TODO: Figure out how to make TODOs highlighted in yellow.
        def equal(match, datum):
            return match == datum
        
        def inside(match, datum):
            return datum.lower() in match.lower()
        
        if len(matches) > 1:
            for datum in relatedData:
                for equivalenceFunc in (equal, aboutEqual, inside):
                    for match in matches.copy():
                        if len(matches) > 1:
                            if equivalenceFunc(match, datum):
                                matches.remove(match)
                        else:
                            break
                            
        
        # Remove matches which are signficantly different than the substring
        # they came from.
        for match in matches.copy():
            if len(matches) > 1:
                diff = difflib.get_close_matches(whatFromWhere[match], [match])
                if not diff:
                    matches.remove(match)
            else:
                break
    
    if len(matches) == 1:
        match = matches.pop()
        log("MB matched a string to a %s: %s" % (field, quote(match)))
        return match
    else:
        log("%d substrings matched." % len(matches))
        if matches:
            log("Unable to select between them.")
            log("Filtered matches: %s" % matches)
        log("Fuzzy matching failed.")
        return u""

@logfn("Querying MusicBrainz.")
def executeQuery(field, match, preFilter, postFilter):
    """Runs a MusicBrainz query from start to finish.
    
    Starts with finding which query function to use and finishing with
    extracting the correct data."""

    query, queryFunction, queryFilter = getFunctionAndFilter(field, match)
    queryFilter = applyParams(queryFilter, preFilter, match)
    log("Field:  %s" % field)
    if preFilter:  log("Pre:    %s" % preFilter)
    if postFilter: log("Post:   %s" % postFilter)
    if match:      log("Match:  %s" % match)
    
    finalResult = None
    results = contactMB(queryFunction, [queryFilter])
    results = requireDesiredInfo(field, results)
    if results:
        result = postProcessResults(results, field, **postFilter)
        if result:
            finalResult = parseResult(result, field)
    
    log("Result: %s\n" % finalResult)
    return finalResult

def getFunctionAndFilter(field, match):
    """Return proper query function & filter based on field & whether we are matching."""
    
    query = mbws.Query()
    
    # A mapping to the applicable filters and functions based on requested field.
    filters = {
        "artist"     : mbws.ArtistFilter,
        "release"    : mbws.ReleaseFilter,
        "date"       : mbws.ReleaseFilter,
        "tracktotal" : mbws.ReleaseFilter,
        "title"      : mbws.TrackFilter,
        "tracknumber": mbws.TrackFilter
    }
    
    functions = {
        "artist"     : query.getArtists,
        "release"    : query.getReleases,
        "date"       : query.getReleases,
        "tracktotal" : query.getReleases,
        "title"      : query.getTracks,
        "tracknumber": query.getTracks
    }
    
    queryFilter = filters[field]
    queryFunction = functions[field]
    
    # TODO: Document why whether we are matching changes the record type.
    if field == "artist" and not match:
        queryFilter = mbws.ReleaseFilter
        queryFunction = query.getReleases
    
    if field == "title" and not match:
        queryFilter = mbws.ReleaseFilter
        queryFunction = query.getReleases
    
    return (query, queryFunction, queryFilter)

def applyParams(queryFilter, params, match=None):
    """Construct params to MB standards then instantiate filter with params."""
    
    newParams = {}
    if queryFilter == mbws.ArtistFilter:
        if match:
            newParams["name"] = match
        newParams["limit"] = 1
    
    elif queryFilter == mbws.ReleaseFilter:
        if "release" in params and params["release"]:
            newParams["title"] = params["release"]
        if match:
            newParams["title"] = match
        if "artist" in params and params["artist"]:
            newParams["artistName"] = params["artist"]
        if "tracktotal" in params and params["tracktotal"]:
            newParams["trackCount"] = params["tracktotal"]
    
    elif queryFilter == mbws.TrackFilter:
        if "title" in params and params["title"]:
            newParams["title"] = params["title"]
        if match:
            newParams["title"] = match
        if "artist" in params and params["artist"]:
            newParams["artistName"] = params["artist"]
        if "release" in params and params["release"]:
            newParams["releaseTitle"] = params["release"]
        newParams["limit"] = 1
    
    return queryFilter(**newParams)

#@logfn("Accessing MusicBrainz web service.")
def contactMB(func, params, depth=0):
    """Robustly connect to MusicBrainz through the MB WebService."""

    time.sleep(depth*2)

    try:
        result = func(*params)
    except Exception, e:
        if depth < 3:
            log("Received error: %s." % quote(str(e)))
            log("Waiting, then trying again.")
            result = contactMB(func, params, depth+1)
        else:
            log("Failed 3 times. Returning None.")
            result = None

    return result
    
def requireDesiredInfo(field, results):
    """Filter results that don't have the necessary information."""
    
    # Currently the only filtering we do is if we're looking for a date.
    if field == "date":
        for result in results:
            if not result.getRelease().getEarliestReleaseDate():
                results.remove(result)
    
    return results

#@logfn("Applying postquery filter to MB results.")
def postProcessResults(results, field, date=None, tracknumber=None, tracks=None):
    """Apply the postquery filter to the result returned by the MB query."""
        
    dateResult = None
    finalResult = results[0]
    
    if isinstance(results[0], musicbrainz2.wsxml.ReleaseResult):
        if date:
            # FIXME: Should this return all the results that match this date
            # instead of just one? There may be multiple releases with a 
            # year that matches and the filters below could help us choose
            # between them.
            success = False
            for result in results:
                earliestDate = result.getRelease().getEarliestReleaseDate()
                if (earliestDate and (earliestDate.split("-")[0] == date)):
                    success = True
                    dateResult = result
                    break
            if not success:
                return None
        
        if tracknumber: 
            # We have a release and track number and we want a track title.
            if not dateResult:
                for result in results:
                    release = getReleaseWithTracks(result.getRelease())
                    if len(release.getTracks()) >= int(tracknumber):
                        return release.getTracks()[int(tracknumber) - 1]
            else:
                release = getReleaseWithTracks(dateResult.getRelease())
                if len(release.getTracks()) >= int(tracknumber):
                    return release.getTracks()[int(tracknumber) - 1]
            
            return None
        
        if tracks and "title" in tracks[0].metadata: 
            # This should only be used for looking up releases.
            success = False
            for result in results:
                release = getReleaseWithTracks(result.getRelease())
                if release.getTracksCount() != len(tracks):
                    continue
                
                # Iterate over the tracks and compare them to our list.
                success = True
                for track, mbTrack in zip(tracks, release.getTracks()):
                    if not aboutEqual(track.metadata["title"], mbTrack.getTitle()):
                        success = False
                        break # One title was wrong. Next release.
                
                # The dateResult and titlesResult need to be the same release.
                if (success and (not dateResult or 
                    dateResult.getRelease().id == result.getRelease().id)): 
                    finalResult = result # We did it.
                    break
                else:
                    success = False # Try the next release.
            if not success:
                return None
    
    elif isinstance(results[0], musicbrainz2.wsxml.TrackResult):
        if tracknumber:
            for result in results:
                for release in result.getTrack().getReleases():
                    if release.getTracksOffset() + 1 == int(tracknumber):
                        if field == "tracknumber":
                            return release  # HACK: Returning a mb2.model.Release!
                        else:
                            return result
            return None
    
    return dateResult or finalResult

def getReleaseWithTracks(release):
    """Given a release, look up that release with track info.
    
    MusicBrainz requires you explictly ask for track info when requesting a 
    release to get that info. So, when applying post-processing that requires
    track info, this function is used."""
    
    return contactMB(mbws.Query().getReleaseById, 
                     [release.id, mbws.ReleaseIncludes(tracks=True)])

#@logfn("Parsing MB results.")
def parseResult(result, field):
    """Pull from the result the data field and return it.
    
    We have successfully conquered all of the dungeons.
    Below is the key to the final castle."""
    
    finalResult = None
    
    if isinstance(result, musicbrainz2.wsxml.ReleaseResult):
        if field == "artist":
            finalResult = result.getRelease().getArtist().getName()
        elif field == "release":
            finalResult = result.getRelease().getTitle()
        elif field == "date":
            if result.getRelease().getEarliestReleaseDate():
                finalResult = result.getRelease().getEarliestReleaseDate().split("-")[0]
        elif field == "tracktotal":
            tracktotal = result.getRelease().getTracksCount()
            finalResult = unicode(tracktotal).rjust(2, u"0")
            
    elif isinstance(result, musicbrainz2.wsxml.TrackResult):
        if field == "title":
            finalResult = result.getTrack().getTitle()
        elif field == "tracknumber":
            # Track numbers are zero-indexed.
            tracknumber = result.getTrack().getReleases()[0].getTracksOffset()+1
            finalResult = unicode(tracknumber).rjust(2, u"0")
            
    elif isinstance(result, musicbrainz2.wsxml.ArtistResult):
        if field == "artist":
            finalResult = result.getArtist().getName()
            
    # Why we would we ever get a Track here instead of a TrackResult?
    elif isinstance(result, musicbrainz2.model.Track):
        finalResult = result.getTitle()
        
    # HACK: This is used when matching tracknumbers, because if this function
    # recieved a TrackResult it would look only at the 0-th release, which may
    # not be correct.
    elif isinstance(result, musicbrainz2.model.Release):
        if field == "tracknumber":
            finalResult = unicode(result.getTracksOffset()+1).rjust(2, u"0")
    
    if not finalResult:
        log("Something went wrong in parseResult. Result type: %s  field: %s"
            % (result.__class__, field))
    
    return toUnicode(finalResult)


class FilepathString(unicode):
    """Marks a string as being a filepath.
    
    This class is a hack. It's purpose it to allow the Finders to mark a string
    as being a filepath (as opposed to a tag value or a filename) because later 
    the MusicBrainz fuzzy matcher treats these differently. Explicitly passing 
    this metadata would muck up multiple function interfaces, hence this class."""
    
    pass
