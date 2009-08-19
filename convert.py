# -*- coding: utf-8 -*-

#  Azul Music Organizer
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

"""Audio conversion support for multiple audio formats.

The convert function is called by traverse if audio in an undesirable format
is found. The currently supported source formats are: wav, flac, ape and mpc.
These formats are currently always converted into Ogg Vorbis but MP3 encoding
support is certain to be a popular demand if we release this publicly."""

import os

import functions
import logger
import configuration as c

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
        logger.log("Attempting to convert %s." % quote(os.path.basename(audioFilePath)), "Details")
        logger.startSection()
        logger.log(command, "Commands")
        result = os.system(command)
        
        if result == 0:
            logger.log("Attempt to convert succeeded.", "Successes")
            functions.deleteItem(audioFilePath)
        else:
            logger.log("Attempt to convert failed.", "Errors")
            functions.rejectItem(audioFilePath)
        
        if extension == ".ape" or extension == ".mpc":
            functions.deleteItem(filePathWithoutExtension + ".wav", True)

        logger.endSection()
        