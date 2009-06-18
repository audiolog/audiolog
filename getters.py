# -*- coding: utf-8 -*-

"""Functions for accessing various audio metainformation sources.

This file contains functions for gather audio metainformation from MusicDNS,
MusicBrainz, the current file tags and filenames. If a result cannot be found
in any case an empty string is returned."""

import os
import subprocess
import time
import re

import musicbrainz2.webservice as mb

import configuration
import tagging
import functions

from functions import ext
from functions import quote
from LogFrame import log

#-------------------------------------------
# Helper Functions
#-------------------------------------------

def fetchPUID(filePath):
    """Try to find a PUID for the given file. 
    
    filePath must point to an MP3 or OGG audio file.
    If a PUID is found, it returns a tuple in the form of [Artist, Track, PUID]. 
    Otherwise, it returns False."""
    
    # Check that filetype is valid and that we are getting PUIDs
    if not configuration.SETTINGS["GET_PUID"]:
        return False
    elif ext(filePath) not in configuration.typeToExts["good_audio"]:
        log(quote(filePath) + " is not a supported filetype for getPUID. It must be MP3 or Ogg.", "Failures")
        return False
    
    log("Running getPUID on " + quote(os.path.basename(filePath)), -1, "Actions")
    command = os.path.join(os.getcwd(), "getPUID")
    p = subprocess.Popen([command, '""' + filePath + '""'], stdout = subprocess.PIPE)
    output = p.communicate()[0]  # Gets the output from the command
    output = output.splitlines() # Turns it from a string to a tuple

    if output and (output[0] == "Success."):
        log("We got a PUID.", -2, "Successes")
        return output[1:]
    else:
        log("We failed to get a PUID.", -2, "Failures")
        return False

def queryMB(func, params, depth=1):
    """Query the MusicBrainz database robustly."""
    
    if depth == 1:
        log("Querying MusicBrainz database.", -1, "Details")
    
    time.sleep(depth**2)
        
    try:
        result = func(params)
    except mb.WebServiceError:
        if depth < 6:
            log("Recieved WebServiceError. Waiting, then trying again.", -2, "Failures")
            result = queryMB(func, params, depth+1)
        else:
            log("Recieved WebServiceError 5 times. Returning empty string.", -2, "Errors")
            return ""                
    return result
            
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

def matchMB(track, field, string):
    """Match to MusicBrainz."""

    string = functions.restrictChars(string)  # Remove special characters
    
    # First, try to match the full string
    result = getMB(track, field, string)
    if result:
        log("MB found a " + field + " match for the full string " + quote(string), -1, "Debugging")
        return result
    else:
        log("MB did not find a " + field + " match for the full string " + quote(string), -1, "Debugging")
        log("Searching for a match in substrings.", -1, "Debugging")
        
    # If that doesn't work, split string based on delimiters list
    delimiters = r"[()\-~+\[\]\{\}]"   # In regular expression format
    substrings = re.split(delimiters, string)
    
    # Strip whitespace and remove empty strings
    substrings = [string.strip() for string in substrings if string.strip()]
    log("Substrings: " + str(substrings), -2, "Debugging")
    
    # See if MusicBrainz recognizes any substrings 
    matches = set()
    for substring in substrings:
        result = getMB(track, field, substring)
        if result:
            matches.add(result)
    
    # Remove matches which are the same as the artist intelligently
    # TODO: Document this better.
    for equivalenceFunc in (lambda a, b: a==b, functions.aboutEqual):
        if len(matches) > 1:
            if all([equivalenceFunc(track.track["artist"], match) for match in matches]):
                matches = set([matches.pop()])
            else:
                for match in matches.copy():
                    if equivalenceFunc(track.track["artist"], match):
                        matches.remove(match)
    
    if len(matches) == 1:
        match = matches.pop()
        log("MB matched a substring to a " + field + ": " + quote(match), -1, "Debugging") 
        return match
    else:
        log(str(len(matches)) + " possible %ss found." % field, -2, "Debugging")
        if matches:
            log("Possible " + field + "s: " + str(matches), -2, "Debugging")
        log("Unable to match a substring to a %s." % field, -1, "Debugging")
        return ""


#-------------------------------------------
# Getter Functions
#-------------------------------------------

def getmbPUID(track, field):
    """Return the metainformation given from MusicBrainz via PUID."""
    
    if not track.PUID:
        log("Cannot perform lookup because we never found a PUID.", 7, "Failures") 
        return ""
    
    query = mb.Query()
    params = mb.TrackFilter(puid = track.PUID, limit = 1)
    result = queryMB(query.getTracks, params)
    
    if len(result) > 0:
        track = result[0].getTrack()
        
        if field == "artist" and track.getArtist() != None:
            return track.getArtist().getName()
        elif field == "title":
            return track.getTitle()
    else:
        return ""

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
