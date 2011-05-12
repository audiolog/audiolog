#! /usr/bin/env python
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

"""This file figures out if the system has the correct dependencies."""

import os
import subprocess

def checkDependencies():
    """Determine whether essential and non-essential dependencies are present."""
    
    error = False
    fatal = False
    
    # First, try all of the dependency commands.
    cmds = {"extract": ["tar", "unzip", "bunzip2", "gunzip", "unrar", "unace"],
            "decode":  ["oggenc", "oggdec", "mpc123", "mac", "lame", "wvunpack"]}
    
    for category in cmds:
        for cmd in cmds[category]:
            try:
                subprocess.Popen([cmd], 
                                 stdout = subprocess.PIPE, 
                                 stderr = subprocess.PIPE)
            except OSError:
                print "You do not have %s installed." % cmd
                print "You will not be able to %s some types of music." % category
                #if cmd == "mac":
                #    print "Because mac can be very difficult to find, we have",
                #    print "provided the source in the 'libs/mac-3.99' directory."
                #else:
                print 'Search your package manager or Google for',
                print '"%s" to install what you need.' % cmd
                error = True
                print
    
    try:
        import PyQt4
    except:
        print "You do not have PyQt installed."
        print "Without it, you cannot run Audiolog with a graphical interface."
        print "Run Audiolog from the command line with the --no-gui option"
        print "or download PyQt from:"
        print "http://www.riverbankcomputing.co.uk/software/pyqt/intro"
        print
        error = True
    
    try:
        import mutagen
    except:
        print "You do not have Mutagen installed."
        print "Without it you cannot tag your audio files."
        print "Download Mutagen from:"
        print "http://code.google.com/p/mutagen/"
        print
        error = True
        fatal = True
    
    try:
        import musicbrainz2
    except:
        print "You do not have MusicBrainz2 installed."
        print "You will not be able to gather metainformation from the Internet."
        print "Search for and install the python-musicbrainz2 package in your",
        print "package manager or download MusicBrainz2 from:"
        print "http://musicbrainz.org/doc/PythonMusicBrainz2"
        print
        error = True
        fatal = True
    
    try:
        if musicbrainz2 and musicbrainz2.__version__ < '0.7.0':
            print "Your copy of MusicBrainz2 is too old to work with Audiolog."
            print "Update your python-musicbrainz2 package using your package",
            print "manager or download the latest version from:"
            print "http://musicbrainz.org/doc/PythonMusicBrainz2"
            print
            error = True
            fatal = True
    except NameError:
        pass
    
    try:
        import musicdns
    except:
        print "You do not have pyofa installed."
        print "Without it, you cannot fingerprint audio files and search for"
        print "matches in the MusicDNS database."
        print "You can download pyofa from:"
        print "http://furius.ca/pyofa/"
        print
        error = True
        
    # TODO: Possibly test that pyofa works.
    
    if not error:
        print "Congratulations! Your system is ready to sort some music!"
        print "You can run Audiolog by typing:"
        print "`python audiolog.py`"
        print "or clicking on \"audiolog.py\" in the src/ folder."
        print "Happy sorting!"
        print
    else:
        print "Your system is missing some of the libraries that Audiolog uses."
        if fatal:
            print "Unfortunately, Audiolog will not run without these libraries."
            print "Please install them using the instructions above."
        else:
            print "Audiolog will still run but you will be not be able to",
            print "perform all of the actions that Audiolog provides."
            print "We recommend you install the missing libraries."
    
    return not fatal

if __name__ == '__main__':
    checkDependencies()