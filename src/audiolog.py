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

"""Audiolog program launcher.

This file has only one function: to start the program."""

import sys

from etc import configuration
from etc.logger import logOutputs
import traverse

if __name__ == "__main__":
    if len(sys.argv) > 1:
        logOutputs.append(sys.stdout)
        configuration.loadConfigFile()
        configuration.PATHS["TO_SCAN"] = [sys.argv[-1]]
        traverse.handleIt([sys.argv[-1]])        
    else:
        from PyQt4.QtGui import QApplication
        from gui.MainWindow import MainWindow
        
        app = QApplication(sys.argv)
        mainWindow = MainWindow()
        mainWindow.show()
        app.exec_()
