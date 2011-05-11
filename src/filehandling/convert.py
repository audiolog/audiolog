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

"""Audio conversion support for multiple audio formats.

The convert function is called by traverse if audio in an undesirable format
is found. The currently supported source formats are: wav, flac, ape and mpc.
These formats are currently always converted into Ogg Vorbis but MP3 encoding
support is certain to be a popular demand if we release this publicly."""

import os
import subprocess

from etc import functions
from etc import configuration as conf
from etc.utils import *
from etc.logger import log, logfn, logSection

convertorCommands = {
    ".wav" : [['oggenc', '-q', str(conf.ENCODING_QUALITY["HIGH"]), '$$.wav']],
    ".flac": [['oggenc', '-q', str(conf.ENCODING_QUALITY["HIGH"]), '$$.flac']],
    ".ape" : [['mac', '$$.ape', '$$.wav', '-d'],
              ['oggenc', '-q', str(conf.ENCODING_QUALITY["HIGH"]), '$$.wav']],
    ".mpc" : [['mpc123', '-w', '$$.wav', '$$.mpc'],
              ['oggenc', '-q', str(conf.ENCODING_QUALITY["MEDIUM"]), '$$.wav']],
    ".wv"  : [['wvunpack', '$$.wv', '-o', '$$.wav'],
              ['oggenc', '-q', str(conf.ENCODING_QUALITY["HIGH"]), '$$.wav']]
}

@logfn("\nConverting audio to Ogg.")
def convert(audioFilePaths):
    """Convert undesirable audio formats into ogg.
    
    Takes a list of audio files and converts each to ogg using appropriate
    commands. These commands (mac, oggenc, mpc123) must be present."""
    
    for audioFilePath in audioFilePaths:
        fileName = os.path.basename(audioFilePath)
        with logSection("Converting %s." % quote(fileName)):
            filePathWithoutExtension, extension = os.path.splitext(audioFilePath)
            commands = convertorCommands[extension]
            
            success = True
            for command in commands:
                cmd = [arg.replace("$$", filePathWithoutExtension)
                       for arg in command]
                
                log(" ".join(cmd))
                p = subprocess.Popen(cmd)
                p.wait()
                
                if p.returncode != 0:
                    success = False
                    break
            
            if not success:
                # FIXME: Should we reject this file or this entire directory?
                log("Unable to convert %s." % quote(fileName))
                functions.rejectItem(audioFilePath)
            else:
                functions.deleteItem(audioFilePath)
            
            if len(commands) > 1: # If we created an intermediate wav file
                functions.deleteItem(filePathWithoutExtension + ".wav", True)
        