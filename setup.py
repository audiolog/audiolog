#! /usr/bin/env python
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

"""
This file figures out if the system has the correct dependencies and is able to
run getPUID.
"""

import os
import subprocess

# First, try all of the dependency commands.

dependencies = {"extract":  ["tar", "unzip", "bunzip2", "gunzip", "unrar", "unace"],
                "decode":   ["oggenc", "oggdec", "mpc123", "mac", "lame"]}

error = False
fatal = False

for category in dependencies:
    for dependency in dependencies[category]:
        try:
            subprocess.Popen([dependency], stdout = subprocess.PIPE, stderr = subprocess.PIPE)
        except OSError:
            print "You do not have %s installed. You will not be able to %s some types of music." % (dependency, category)
            print "Try going to http://www.google.com/search?q=%s to install what you need." % dependency
            if dependency == "mac":
                print "Because mac can be very difficult to find, we have provided the source under the 'libs/mac-3.99' directory."
            error = True
            print

try:
    import PyQt4
except:
    print "You do not have PyQt installed. You will not be able to run Audiolog."
    print "Download it from:"
    print "http://www.riverbankcomputing.co.uk/software/pyqt/intro"
    print
    error = True
    fatal = True

try:
    import mutagen
except:
    print "You do not have Mutagen installed. You will not be able to tag your audio files."
    print "Download it from:"
    print "http://code.google.com/p/mutagen/"
    print
    error = True
    fatal = True

try:
    import musicbrainz2
except:
    print "You do not have MusicBrainz2 installed. You will not be able to gather metainformation from the Internet."
    print "Install it by running `python setup.py install` in the 'libs/python-musicbrainz2' folder included with Audiolog."
    print "Alternatively, you can check it out from MusicBrainz's Subversion repository:"
    print "svn checkout http://svn.musicbrainz.org/python-musicbrainz2/trunk python-musicbrainz2"
    print "DO NOT download the python-musicbrainz2 0.6.0 library from their website or install it using your package manager."
    print "0.6.0 is too out of date and will not work with Audiolog."
    print
    error = True
    fatal = True

try:
    if musicbrainz2 and musicbrainz2.__version__ < '0.7.0':
        print "Your copy of MusicBrainz2 is too old and will not work with Audiolog."
        print "Please install the copy provided with Audiolog in the 'libs/python-musicbrainz2' folder and run `python setup.py install`."
        print
        error = True
        fatal = True
except NameError:
    pass

try:
    
    command = os.path.join(os.getcwd(), "getPUID")
    p = subprocess.Popen([command, "tests/test.mp3"], stdout = subprocess.PIPE)
    output = p.communicate()[0]  # Gets the output from the command
    output = output.splitlines() # Turns it from a string to a tuple
    
    if not output or (output[0] != "Success."):
        print "getPUID does not work on your system, potentially because of an error message above."
        print "You will not be able to use the MusicDNS service, and can disable \"Fetch PUIDs\" from Audiolog's configuration."
        print "You will, however, still be able to sort most music."
        print
        error = True
except:
    pass # This happened because we didn't have musicbrainz2, but that was already handled earlier.

if not error:
    print "Congratulations! Your system is ready to sort some music!"
    print "You can run Audiolog by typing:"
    print "`python audiolog.py`"
    print "or clicking on \"audiolog.py\" in the src/ folder."
    print "Happy sorting!"
    print
else:
    print "Your system is missing some required libraries."
    if fatal:
        print "Unfortunately, Audiolog will not run correctly without these libraries, so please install them using the instructions above before running this program."
    else:
        print "Audiolog will still run, however depending on what you are missing, you may have substantially lower performance."
        print "We highly recommend you install the missing libraries."
