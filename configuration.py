"""All the global settings which affect how the program runs.

These settings are accessed throughout the program to determine what to do,
how to do it and on what. Currently present: dictionaries of types to extensions
and extensions to types; paths specifying what to scan and where to put the 
results; settings indicating whether to: scan recursively, permanently delete 
files, and use the (time-consuming) getPUID program; actions that may or may 
not be taken; the categories of messages which the LogFrame is currently
displaying; and multiple audio encoding qualities on a scale of 1 to 10."""

import os

# Types to Extensions
typeToExts = {"archive"   : [".zip", ".rar", ".tar", ".gz", ".bz2", ".ace", ".7z"],
              "good_audio": [".ogg", ".mp3"],
              "bad_audio" : [".ape", ".flac", ".wav", ".mpc"],
              "image"     : [".jpg", ".jpeg", ".png"], 
              "cue"       : [".cue"]}

# Extensions to Types
extToType = {}
for fileType in typeToExts:
    for extension in typeToExts[fileType]:
        extToType[extension] = fileType

# Paths
PATHS = {
    "BASE_DIR": "",
    "REJECTS" : "",
    "DELETES" : "",
    "SORTED"  : "",
    "TO_SCAN" : [""],
    "CURRENT" : ""
}

# Settings
SETTINGS = {
    "RECURSE" : True,
    "DELETE"  : False,
    "GET_PUID": True
}

# Traverse Actions
ACTIONS = {
    "EXTRACT": True,
    "IMAGE"  : True,
    "CLEAN"  : True,
    "CONVERT": True,
    "SPLIT"  : True,
    "AUDIO"  : True
}

# Logging 
LOGGING = {
    "Actions"  : True,
    "Successes": False,
    "Failures" : True,
    "Errors"   : True,
    "Details"  : False,
    "Commands" : False,
    "Debugging": False
}

# Encoding Qualities
ENCODING_QUALITY = {
    "HIGH"  : 9,
    "MEDIUM": 6,
    "LOW"   : 3
}
