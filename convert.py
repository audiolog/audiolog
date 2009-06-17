"""Audio conversion support for multiple audio formats.

The convert function is called by traverse if audio in an undesirable format
is found. The currently supported source formats are: wav, flac, ape and mpc.
These formats are currently always converted into Ogg Vorbis but MP3 encoding
support is certain to be a popular demand if we release this publicly."""

import os

import functions
import configuration as c
from LogFrame import log

convertorCommands = {
    ".wav" : 'oggenc -q ' + str(c.ENCODING_QUALITY["HIGH"]) + ' "$$.wav"',
    ".flac": 'oggenc -q ' + str(c.ENCODING_QUALITY["HIGH"]) + ' "$$.flac"',
    ".ape" : 'mac "$$.ape" "$$.wav" -d; \noggenc -q ' + str(c.ENCODING_QUALITY["HIGH"]) + ' "$$.wav"',
    ".mpc" : 'mpc123 -w "$$.wav" "$$.mpc"; \noggenc -q ' + str(c.ENCODING_QUALITY["MEDIUM"]) + ' "$$.wav"'
}

def convert(audioFilePaths):
    """Convert undesirable audio formats into ogg.
    
    Takes a list of audio files and converts each to ogg using appropriate
    commands. These commands (mac, oggenc, mpc123) must be present."""
    
    for audioFilePath in audioFilePaths:
        filePathWithoutExtension, extension = os.path.splitext(audioFilePath)
        command = convertorCommands[extension]
        command = command.replace("$$", filePathWithoutExtension)
        log("Attempting to convert " + quote(os.path.basename(audioFilePath)), 3, "Details")
        log(command, 4, "Commands")
        result = os.system(command)
        
        if result == 0:
            log("Attempt to convert succeeded.", 4, "Successes")
            functions.deleteItem(audioFilePath)
        else:
            log("Attempt to convert failed.", 4, "Errors")
            functions.rejectItem(audioFilePath)
        
        if extension == ".ape" or extension == ".mpc":
            functions.deleteItem(filePathWithoutExtension + ".wav", True)
        