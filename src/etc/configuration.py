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

"""All the global settings which affect how the program runs.

These settings are accessed throughout the program to determine what to do,
how to do it and on what. Currently present: dictionaries of types to extensions
and extensions to types; paths specifying what to scan and where to put the 
results; settings indicating whether to: scan recursively, permanently delete 
files, and use the (time-consuming) audio fingerprinter; actions that may or may 
not be taken; the categories of messages which the LogFrame is currently
displaying; and multiple audio encoding qualities on a scale of 1 to 10."""

import pickle
import platform

import functions

acoustidAppKey = "TaHHkbR5"
acoustidUserKey = "GlVp11l7"

LOCAL_OS = platform.system()

if LOCAL_OS == "Windows":
    configFileName = "audiolog.conf"
else:
    configFileName = ".audiolog"

# Types to Extensions
typeToExts = {"archive"   : [".zip", ".rar", ".tar", ".gz", ".bz2", ".ace", ".7z"],
              "good_audio": [".ogg", ".mp3"],
              "bad_audio" : [".ape", ".flac", ".wav", ".mpc", ".wv"],
              "image"     : [".jpg", ".jpeg", ".png", ".bmp"], 
              "cue"       : [".cue"]}

# Extensions to Types
extToType = {}
for fileType in typeToExts:
    for extension in typeToExts[fileType]:
        extToType[extension] = fileType

# Paths
PATHS = {
    "SORTED"  : functions.getDefaultSortedPath(LOCAL_OS),
    "TO_SCAN" : [functions.getDefaultToScanPath(LOCAL_OS)],
    "CURRENT" : ""
}

# Settings
SETTINGS = {
    "DELETE"   : False,
    "GET_PRINT": True
}

# Traverse Actions
ACTIONS = {
    "EXTRACT"   : True,
    "IMAGE"     : True,
    "CLEAN"     : True,
    "CONVERT"   : True,
    "SPLIT"     : True,
    "METADATA"  : True
}

# Encoding Qualities
ENCODING_QUALITY = {
    "HIGH"  : 9,
    "MEDIUM": 6,
    "LOW"   : 3
}

def loadConfigFile():
    """Unserialize the configuration at fileName and return it."""
    
    global ACTIONS, SETTINGS, PATHS

    try:
        f = open(configFileName, "r")
    except: # File probably doesn't exist yet.
        return False
    
    config = pickle.load(f)
    f.close()
    
    ACTIONS = config["ACTIONS"]
    SETTINGS = config["SETTINGS"]
    PATHS = config["PATHS"]
    
    return True
   
def saveConfigFile():
    """Serialize configuration and save it to fileName."""
    
    f = open(configFileName, "w")
    pickle.dump({"ACTIONS": ACTIONS, "SETTINGS": SETTINGS, "PATHS": PATHS}, f)
    f.close()
