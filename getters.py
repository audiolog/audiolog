# -*- coding: utf-8 -*-

"""High-level interface for accessing MusicBrainz.

fetchPUID runs the MusicDNS audio fingerprinter on a track and looks it up in their database.

getMBPUID verifies said PUID information with MusicBrainz

getMBData constructs and executes a MusicBrainz query based on previously known data and/or potentially useful data.
It takes the following parameters:
    field: The name of the field we are looking for. Note that this does not necessarily correspond to the
           MusicBrainz record that we use. For instance, looking for the "tracktotal" field still uses the
           Release record.
    match: The [potentially incorrect] string that field may be equal to. This is used for when mbQuery is
           used to verify found but questionable data.
    artist, release, ..., titles: Previously known (and correct) data used to filter down results. Not all
                                  fields use all filters, and mbQuery should be called accordingly.

Being the meat of data gathering, getMBData is broken down into four or five parts:
    - Query construction
    - Fuzzy matching (if applicable)
    - Query execution
    - Post processing
    - Data gathering

Queries are constructed based on the requested field. Four parameters (artist, release, tracktotal, title)
can be used directly in a Filter. The rest must be used in post processing.

A query is executed by first mapping Azul's standardized naming convention to MusicBrainz' (somewhat arbitrary)
naming convention, depending on the requested record. The query is executed with queryMB wrapper.

Dates, track numbers, and titles are verified in post processing. For titles specifically, the contents of each
release must be received and the titles must be verified one by one.

Finally, the requested field is extracted from the first found record, provided we got that far.


==MusicBrainz Interface==

The system for using MusicBrainz is designed with 3 goals:
    1. Create one clean, simple, consistent interface for all callers and calls
       to use. The function mbInterface meets these goals.
    2. Allow for the most powerful possible uses of MusicBrainz even if they
       are not provided for or intended by the MusicBrainz interface 
       designers. We meet this goal in part by doing powerful post-processing
       of queries, which allows callers to provide dates or Track objects in
       the same manner as any other type of filter data even though
       MusicBrainz does not directly support this.
    3. Separate each step of the MusicBrainz process into its own function
       for ease of understanding and maintenance.
       
       
==Illustration of MusicBrainz Process==

               mbInterface                  |
                    |                       |
             filterConstructor              |
              |            |                |
          mbMatcher   mbFuzzyMatcher        |
              |            |                |
           mbQueryConstructor               |
                    |                       |
              getMBFunction               Time
                    |                       |
              applyMBParams                 |
                    |                       |
              postProcessMB                 |
                    |                       |
                 queryMB                    |
                    |                       |
              parseMBResults                V
"""

import subprocess
import time
import re
import difflib

import musicbrainz2.model
import musicbrainz2.wsxml
import musicbrainz2.webservice as mb

import configuration
import functions
import logger
from utils import *

#-------------------------------------------
# Externally-called functions
#-------------------------------------------

def fetchPUID(filePath):
    """Try to find a PUID for the given file. 
    
    filePath must point to an MP3 or OGG audio file.
    If a PUID is found, it returns a tuple in the form of [Artist, Track, PUID]. 
    Otherwise, it returns None."""
    
    # Check that filetype is valid and that we are getting PUIDs
    if not configuration.SETTINGS["GET_PUID"]:
        return False
    elif ext(filePath) not in configuration.typeToExts["good_audio"]:
        logger.log("%s is not a supported filetype for getPUID. It must be MP3 or Ogg." % quote(filePath), "Failures")
        return False
    
    logger.log("Generating an audio fingerprint for %s, then searching for a match in the MusicDNS database." % quote(os.path.basename(filePath)), "Actions")
    command = os.path.join(os.getcwd(), "getPUID")
    p = subprocess.Popen([command, '""%s""' % filePath], stdout = subprocess.PIPE)
    output = p.communicate()[0]  # Gets the output from the command
    output = output.splitlines() # Turns it from a string to a tuple

    logger.startSection()
    if output and (output[0] == "Success."):
        logger.log("MusicDNS found a match.", "Successes")
        result = output[1:]
    else:
        logger.log("MusicDNS failed to find a match.", "Failures")
        result = None
    logger.endSection()
    return result
        
def getMBPUID(track, field):
    """Return the metainformation given from MusicBrainz via PUID."""

    if not track.PUID:
        logger.log("Cannot perform lookup because we never found a PUID.", "Failures")
        return None
    
    logger.log("Attempting to match the MusicDNS information with MusicBrainz.", "Actions")
    logger.startSection()
    
    query = mb.Query()
    params = [mb.TrackFilter(puid=track.PUID[2], limit=1)]
    result = queryMB(query.getTracks, params)
    
    logger.endSection()
    
    if not result:
        return None
    
    if field == "artist":
        return result[0].getTrack().getArtist().getName()
    elif field == "title":
        return result[0].getTrack().getTitle()

def mbInterface(field, match=None, track=None, relevantFields=[]):
    """Interface for Finders to access MusicBrainz."""
    
    logger.log("Constructing filter.", "Actions")
    prequeryFilter, postqueryFilter, match = filterConstructor(match, track, relevantFields, field)
    #logger.startSection()
    #logger.log("prequeryFilter: %s" % str(prequeryFilter), "Debugging")
    #logger.log("postqueryFilter: %s" % str(postqueryFilter), "Debugging")
    #logger.log("match: %s" % str(match), "Debugging")
    #logger.endSection()
    
    if match:
        logger.log("Attempting to fuzzily match the string %s on %s." % (quote(match), field), "Actions")
        logger.startSection()
        result = mbFuzzyMatcher(field, match, track, prequeryFilter, postqueryFilter)
        logger.endSection()
        return result
    else:
        logger.log("Attempting to match the string %s on %s." % (quote(match), field), "Actions")
        logger.startSection()
        result = mbMatcher(field, match, track, prequeryFilter, postqueryFilter)
        logger.endSection()
        return result


#-------------------------------------------
# Internally-called functions
#-------------------------------------------

def filterConstructor(match, track, relevantFields, field):
    """Construct prequery, postquery and match filters.
    
    The caller provides a list fields which would be helpful (or necessary) 
    for a successful query. If a consensus has already been found for these
    fields, then this data is included in the filter. 
  
    The match parameter is overloaded for two uses:
        1. For artist, release and title fields: Fuzzily match the suspect
           contents of the tag or filename.
        2. For date, tracktotal and tracknumber: These numerical fields do not
           make sense to fuzzily match. They should be used in the filter but
           they are not yet known (and hence are not stored in track.metadata).
           For these special cases we move this uncertain data into the filter
           from match and set match to None so no fuzzy matching occurs."""
    
    prequeryFields = ["match", "artist", "release", "tracktotal", "title"]
    postqueryFields = ["date", "tracknumber", "tracks"]
    
    prequeryFilter = {}
    postqueryFilter = {}
    
    for relevantField in relevantFields:
        if relevantField in prequeryFields:
            if relevantField == field == "tracktotal":
                prequeryFilter[field] = match
                match = None
            else:
                prequeryFilter[relevantField] = track.metadata.get(relevantField, None)
            
        elif relevantField in postqueryFields:
            if relevantField == field == "date":
                postqueryFilter[field] = match
                match = None
            elif relevantField == field == "tracknumber":
                postqueryFilter[field] = match
                match = None
            elif relevantField == "tracks":
                postqueryFilter[relevantField] = track.parent.tracks
            else:
                postqueryFilter[relevantField] = track.metadata.get(relevantField, None)
    
    return (prequeryFilter, postqueryFilter, match)

def mbMatcher(field, match, track, prequeryFilter, postqueryFilter):
    """Non-fuzzy matching is easy..."""
    
    return mbQueryConstructor(field, match, prequeryFilter, postqueryFilter)

def mbFuzzyMatcher(field, match, track, prequeryFilter, postqueryFilter):
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
    match and the search will succeed."""
    
    match = functions.restrictChars(match) # Remove special characters
    
    # First, try to fetch result with the full string.
    result = mbQueryConstructor(field, match, prequeryFilter, postqueryFilter)
    if result:
        logger.log("MB found a %s match for the full string %s." % (field, quote(match)), "Debugging")
        return result
    
    logger.log("MB did not find a %s match for the full string %s." % (field, quote(match)), "Debugging")
    logger.log("Searching for a match in substrings.", "Debugging")
    logger.startSection()
    
    # If that doesn't work, split string based on delimiters list
    delimiters = r"[/()\-~+\[\]\{\}*]"   # In regular expression format
    substrings = re.split(delimiters, match)
    
    # Strip whitespace and remove empty strings
    substrings = [string.strip() for string in substrings if string.strip()]
    logger.log("Substrings: " + str(substrings), "Debugging")

    matches = set()
    whatFromWhere = {}
    for substring in substrings:
        result = mbQueryConstructor(field, substring, prequeryFilter, postqueryFilter)
        if result:
            whatFromWhere[result] = substring
            matches.add(result)
    logger.endSection()
    
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
    
        logger.log("Attempting to remove bogus matches.", "Actions")
        logger.startSection()
        logger.log("Current matches: %s" % str(matches), "Debugging")
        logger.endSection()
        
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
        
        # If we have more than 1 result, than we want to remove probable false positives.
        # We'll look at the artist, album and title fields and remove those from the results.
        relatedFields = ["artist", "release", "title"]  # These are in the order we would prefer to remove them.
        relatedFields.remove(field)
        relatedData = []
        for field in relatedFields:
            if field in track.metadata:
                relatedData.append(track.metadata[field])
        
        # Remove matches which are the same as the already known artist, release or title intelligently.
        # TODO: Figure out how to make TODOs highlighted in yellow.
        if len(matches) > 1:
            for datum in relatedData:
                for equivalenceFunc in (lambda a, b: a==b, aboutEqual):
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
        logger.log("MB matched a substring to a " + field + ": " + quote(match), "Debugging")
        return match
    else:
        logger.log("%d substrings matched." % len(matches), "Debugging")
        if matches:
            logger.log("Unable to select one correct match.", "Debugging")
            logger.log("Matches: " + str(matches), "Debugging")
        logger.log("Unable to match a substring to a %s." % field, "Debugging")
        return ""

def mbQueryConstructor(field, match, prequeryFilter, postqueryFilter):
    """Runs a MusicBrainz query from start to finish.
    
    Starts with finding which query function to use and finishing with
    extracting the correct data."""
    
    logger.log("Creating query function and filter.", "Actions")
    query, queryFunction, queryFilter = getMBFunction(field, match)
    queryFilter = applyMBParams(queryFilter, prequeryFilter, match)
    
    results = queryMB(queryFunction, [queryFilter])
    
    if not results:
        return None
    
    logger.log("Applying postquery filter to MB results.", "Actions")
    logger.startSection()
    result = postProcessMB(results, **postqueryFilter)
    logger.endSection()
    
    if not result:
        return None
    
    logger.log("Parsing MB results.", "Actions")
    logger.startSection()
    result = parseMBResult(result, field)
    logger.endSection()
    return result

def getMBFunction(field, match):
    """Return proper query function and filter based on desired field and whether we are matching."""
    
    query = mb.Query()
    
    # A mapping to the applicable filters and functions based on requested field.
    filters = {
        "artist"     : mb.ArtistFilter,
        "release"    : mb.ReleaseFilter,
        "date"       : mb.ReleaseFilter,
        "tracktotal" : mb.ReleaseFilter,
        "title"      : mb.TrackFilter,
        "tracknumber": mb.TrackFilter
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
    
    if field == "artist" and not match:
        queryFilter = mb.ReleaseFilter
        queryFunction = query.getReleases
    
    if field == "title" and not match:
        queryFilter = mb.ReleaseFilter
        queryFunction = query.getReleases
    
    return (query, queryFunction, queryFilter)

def applyMBParams(queryFilter, params, match=None):
    """Construct params to MB standards then instantiate filter with params."""
    
    newParams = {}
    if queryFilter == mb.ArtistFilter:
        if match:
            newParams["name"] = match
        newParams["limit"] = 1
    
    elif queryFilter == mb.ReleaseFilter:
        if "release" in params and params["release"]:
            newParams["title"] = params["release"]
        if match:
            newParams["title"] = match
        if "artist" in params and params["artist"]:
            newParams["artistName"] = params["artist"]
        if "tracktotal" in params and params["tracktotal"]:
            newParams["trackCount"] = params["tracktotal"]
    
    elif queryFilter == mb.TrackFilter:
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

def postProcessMB(results, date=None, tracknumber=None, tracks=None):
    """Apply the postquery filter to the result returned by the MB query."""
    
    query = mb.Query()
    
    dateResult = None
    finalResult = results[0]
    
    # We have successfully retrieved a record, now we must post process it (potentially).
    
    if isinstance(results[0], musicbrainz2.wsxml.ReleaseResult):
        if date:
            success = False
            for result in results:
                if ((result.getRelease().getEarliestReleaseDate()
                 and result.getRelease().getEarliestReleaseDate().split("-")[0]) == date):
                    success = True
                    dateResult = result
                    break
            if not success:
                return None
        
        if tracknumber: # We have a release and track number and we want a track title.
            finalResult = o_o(dateResult, finalResult)
            releaseID = finalResult.getRelease().id
            release = queryMB(query.getReleaseById, [releaseID, mb.ReleaseIncludes(tracks = True)])
            return release.getTracks()[int(tracknumber) - 1]
        
        if tracks and "title" in tracks[0].metadata: # Only should be used for looking up releases.
            success = False
            for result in results:
                releaseID = result.getRelease().id
                release = queryMB(query.getReleaseById, [releaseID, mb.ReleaseIncludes(tracks = True)]) # You must query every release explicitly to get its tracks.
                if release.getTracksCount() != len(tracks): # The record must match the amount of titles we are matching against.
                    continue
                
                # Iterate over the tracks and compare them to our list.
                success = True
                for (knownTitle, mbTitle) in zip(tracks, release.getTracks()):
                    if not aboutEqual(knownTitle.metadata["title"], mbTitle.getTitle()):
                        success = False
                        break # One title was wrong. Next release.
                
                if success and (not dateResult or dateResult.getRelease().id == result.getRelease().id): # The dateResult and titlesResult need to be the same release.
                    finalResult = result # We did it.
                    break
                else:
                    success = False # Try the next release.
            if not success:
                return None
    
    elif isinstance(results[0], musicbrainz2.wsxml.TrackResult):
        if tracknumber:
            if finalResult.getTrack().getReleases()[0].getTracksOffset() + 1 != int(tracknumber):
                return None
    
    return o_o(dateResult, finalResult)

def queryMB(func, params, depth=1):
    """Query the MusicBrainz database robustly."""
    
    if depth == 1:
        logger.log("Querying MusicBrainz database.", "Details")
        logger.startSection()
    
    time.sleep(depth**2)
    
    try:
        result = func(*params)
    except mb.WebServiceError, e:
        if depth < 6:
            logger.log("Recieved WebServiceError: %s. Waiting, then trying again." % quote(e.__str__()), "Failures")
            result = queryMB(func, params, depth+1)
        else:
            logger.log("Recieved WebServiceError 5 times. Returning None.", "Errors")
            result = None

    if depth == 1:
        logger.endSection()
    return result

def parseMBResult(result, field):
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
            # TODO: Make sure it's the right release (if we know it)
            tracknumber = result.getTrack().getReleases()[0].getTracksOffset() + 1  # Track numbers are zero-indexed.
            finalResult = unicode(tracknumber).rjust(2, u"0")
            
    elif isinstance(result, musicbrainz2.wsxml.ArtistResult):
        if field == "artist":
            finalResult = result.getArtist().getName()
            
    elif isinstance(result, musicbrainz2.model.Track):
        finalResult = result.getTitle()
    
    if not finalResult:
        logger.log("Something went wrong in parseMBResults. Result type: %s  field: %s" % (result.__class__, field), "Errors")
    
    return finalResult

