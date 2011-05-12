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

"""Audiolog program launcher."""

import os
import sys
from optparse import OptionParser

from filehandling import traverse
from etc import configuration
from etc.logger import logOutputs
from etc.utils import *

def run(argv):
    """Parse command-line options and start Audiolog."""
    
    parser = OptionParser(usage="audiolog [OPTIONS] [INPUT_DIR]...")
    parser.add_option("--no-gui", action="store_false", dest="showGUI",
                      default=True, help="run program without GUI (on by default)")
    parser.add_option("-s", metavar="SORTED_DIR", dest="sortedPath", 
                      help="the directory correctly sorted music should be moved to")
    options, inputPaths = parser.parse_args(argv)
    
    configuration.loadConfigFile()
    if options.sortedPath:
        configuration.PATHS["SORTED"] = toUnicode(options.sortedPath)
    if inputPaths:
        configuration.PATHS["TO_SCAN"] = [toUnicode(path) for path in inputPaths]
    
    if options.showGUI:
        from PyQt4.QtGui import QApplication
        from gui.MainWindow import MainWindow
        
        app = QApplication(sys.argv)
        mainWindow = MainWindow()
        mainWindow.show()
        if inputPaths: 
            mainWindow.start()
        app.exec_()
       
    elif not options.showGUI and inputPaths:
        logOutputs.append(sys.stdout)
        traverse.handleIt()

if __name__ == "__main__":
    run(sys.argv[1:])
