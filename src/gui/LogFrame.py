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

"""Log designed to be highly configurable and readable.

The currently primary method of filtering messages is by category.
The current message categories are:
    Actions
    Successes
    Failures
    Errors
    Commands (to be run at console)
    Debugging"""

from functools import partial

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from etc import configuration
from etc import logger

class LogFrame(QFrame):
    """A versatile TextEdit for displaying program messages."""
    
    def __init__(self, parent=None):
        super(LogFrame, self).__init__(parent)
        
        # Text Log
        self.textLog = QTextEdit()
        self.textLog.setReadOnly(True)
        self.textLog.setFontFamily("monospace")
        self.textLog.setFontPointSize(self.textLog.font().pointSizeF()-2)
        self.textLog.setAcceptRichText(True)
        self.textLog.setWordWrapMode(QTextOption.NoWrap)
        self.textLog.setMinimumHeight(440)
        self.setMinimumWidth(900)
        self.connect(logger.emitter, SIGNAL("AppendToLog"), self.appendToLog)
        self.connect(logger.emitter, SIGNAL("ClearLog"), self.clearLog)
        
        # Layout
        layout = QHBoxLayout(self)
        layout.addWidget(self.textLog)

    def appendToLog(self, message):
        """Add message to entries; call addToLog."""
        
        self.textLog.append(message[:-1]) # Remove trailing newline.
        
    def clearLog(self):
        """Clear text edit and entries list."""
        
        self.textLog.clear()
