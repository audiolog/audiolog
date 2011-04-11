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

"""Functions for reading and writing MP3 and Ogg Vorbis tags.

This file provides only three functions which are called from other files:
getTag, setTag and clearTags. All the other functions all called by these
three to help in those tasks.

A set of these helper functions are dedicated to making reading and writing 
track numbers and track totals to MP3s work like performing those actions on
Ogg Vorbis files. These behave differently because Ogg Vorbis, preferably, 
stores the tracknumber and tracktotal as two separate fields, whereas MP3
stores them as a combined "tracknumber" field which might look like "08/12", 
for example. The MP3 helper functions work be reading the combined track
field; splitting based on the "/" character into track number and total;
then, in the case of reading, returning the relevant part; or, in the case of
writing, by writing the relevant part while keeping the other part constant."""

import os
from pprint import pprint

import mutagen.id3
from mutagen.mp3 import MP3
from mutagen.oggvorbis import OggVorbis as Ogg
from mutagen.easyid3 import EasyID3

from etc import functions
from etc import logger
from etc.utils import *

#-------------------------------------------
# MP3 Track Number and Total Helper Functions
#-------------------------------------------

def getMP3TrackTotal(filePath):
    combinedTrackData = getTag(filePath, "tracknumber", False)
    listed = combinedTrackData.split("/")
    if len(listed) == 2:
        return listed[1]
    else:
        return u""

def getMP3TrackNumber(filePath):
    combinedTrackData = getTag(filePath, "tracknumber", False)
    listed = combinedTrackData.split("/")
    if len(listed[0]) == 2:
        return listed[0]
    else:
        return u""

def setMP3TrackTotal(filePath, value):
    combinedTrackData = getTag(filePath, "tracknumber", False)
    listed = combinedTrackData.split("/")
    if listed:
        trackData = u"/".join([listed[0], value])
        setTag(filePath, "tracknumber", trackData, False)
    else:
        logger.startSection()
        logger.log("Failed to write tracktotal to %s." % quote(os.path.basename(filePath)), "Failures")
        logger.endSection()
        
def setMP3TrackNumber(filePath, value):
    combinedTrackData = getTag(filePath, "tracknumber", False)
    listed = combinedTrackData.split("/")
    if len(listed) == 2:
        trackData = u"/".join([value, listed[1]])
        setTag(filePath, "tracknumber", trackData, False)
    else:
        setTag(filePath, "tracknumber", value, False)

#-------------------------------------------
# General Helper Functions
#-------------------------------------------

def validField(field):
    """Convert MusicBrainz terminology to valid Mutagen terminology."""
    
    if field == "release": 
        return "album"
    else: 
        return field

def openAudioFile(filePath):
    """Return, based on extension, an MP3 or Ogg Mutagen object."""
    
    extension = ext(filePath)    
    try:
        if extension == ".mp3":
            return MP3(filePath, ID3=EasyID3)
        elif extension == ".ogg":
            return Ogg(filePath)
        else:
            #logger.startSection()
            logger.log("Attempt to open %s failed. File must be an MP3 or Ogg." % quote(filePath), "Errors")
            #logger.endSection()
            raise NotImplementedError
    except HeaderNotFoundError:
        logger.log("Attempt to open %s failed. File seems corrupted." % quote(filePath), "Errors")

#-------------------------------------------
# Public Functions
#-------------------------------------------

def getTag(filePath, field, infiniteLoop=True):
    """Return the specific tag for filePath."""
    
    if field == "tracktotal" and ext(filePath) == ".mp3":
        return getMP3TrackTotal(filePath)
    elif field == "tracknumber" and ext(filePath) == ".mp3" and infiniteLoop:
        return getMP3TrackNumber(filePath)
    else:
        field = validField(field)
        audioFile = openAudioFile(filePath)
        return audioFile.get(field, [u""])[0]

def setTag(filePath, field, value, infiniteLoop=True):
    """Set the specified field to value for filePath."""
    
    if field == "tracktotal" and ext(filePath) == ".mp3":
        setMP3TrackTotal(filePath, value)
    elif field == "tracknumber" and ext(filePath) == ".mp3" and infiniteLoop:
        setMP3TrackNumber(filePath, value)
    else:
        field = validField(field)
        audioFile = openAudioFile(filePath)
        audioFile[field] = unicode(value)
        audioFile.save()
    
def clearTags(filePath):
    """Remove all tags from file."""
    
    audioFile = openAudioFile(filePath)
    audioFile.delete()
    
    if ext(filePath) == ".ogg":
        return # If this is an Ogg, then we've done everything we need to do.
    
    audioFile = openAudioFile(filePath)
    try:
        audioFile.add_tags(ID3=EasyID3)
        audioFile["tracknumber"] = u"00"
        audioFile.save()
    except mutagen.id3.error:
        #logger.startSection()
        logger.log("There was an error clearing the old ID3 tags.", "Errors")
        #logger.endSection()
