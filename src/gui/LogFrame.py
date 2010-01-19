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
        
        self.colorCode = False
        self.level = 4
        
        # Text Log
        self.entries = []
        self.textLog = QTextEdit()
        self.textLog.setReadOnly(True)
        self.textLog.setFontFamily("monospace")
        self.textLog.setAcceptRichText(True)
        self.textLog.setWordWrapMode(QTextOption.NoWrap)
        self.textLog.setMinimumHeight(360)
        self.setMinimumWidth(800)
        self.connect(logger.emitter, SIGNAL("AppendToLog"), self.appendToLog)
        self.connect(logger.emitter, SIGNAL("ClearLog"), self.clearLog)
        
        # Options Frame
        self.optionsFrame = QGroupBox("Logging Options", self)
        self.colorCodeCheck = QCheckBox("Color-Code by Category")
        self.connect(self.colorCodeCheck, SIGNAL("stateChanged(int)"), self.updateLog)
        self.levelLabel = QLabel("Depth:")
        self.levelCombo = QComboBox()
        self.levelCombo.addItem("1 (Almost Nothing)")
        self.levelCombo.addItem("2")
        self.levelCombo.addItem("3")
        self.levelCombo.addItem("4")
        self.levelCombo.addItem("5")
        self.levelCombo.addItem("6 (Recommended)")
        self.levelCombo.addItem("7")
        self.levelCombo.addItem("8")
        self.levelCombo.addItem("9")
        self.levelCombo.addItem("10 (Everything)")
        #self.levelCombo.addItem("11")
        #self.levelCombo.addItem("12 (Everything)")
        self.levelCombo.setCurrentIndex(5)
        self.connect(self.levelCombo, SIGNAL("currentIndexChanged(int)"), self.updateLog)
        optionsFrameLayout = QGridLayout(self.optionsFrame)
        optionsFrameLayout.addWidget(self.colorCodeCheck, 0, 0, 1, 2)
        optionsFrameLayout.addWidget(self.levelLabel, 1, 0)
        optionsFrameLayout.addWidget(self.levelCombo, 1, 1)
        self.level = 6
        
        # Control Frame
        self.controlFrame = QGroupBox("Categories to Display", self)
        self.controlFrame.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.MinimumExpanding)
        controlFrameLayout = QVBoxLayout(self.controlFrame)
        
        self.checkboxes = []
        # categories = configuration.LOGGING.keys()  <--- This would be more general (and require less hard-coding) but the order is arbitrary
        categories = ["Actions", "Successes", "Failures", "Errors", "Details", "Commands", "Debugging"]
        for category in categories:
            checkbox = QCheckBox(category, self.controlFrame)
            checkbox.setChecked(configuration.LOGGING[category])
            self.connect(checkbox, SIGNAL("stateChanged(int)"), self.updateLog)
            self.checkboxes.append(checkbox)
            controlFrameLayout.addWidget(checkbox, 0, Qt.AlignTop)
            
        self.displayAllButton = QPushButton("Display All", self.controlFrame)
        self.connect(self.displayAllButton, SIGNAL("clicked(bool)"), self.displayAll)
        controlFrameLayout.addWidget(self.displayAllButton)
        
        # Layout
        layout = QGridLayout(self)
        layout.addWidget(self.textLog, 0, 0, 2, 1)
        layout.addWidget(self.optionsFrame, 0, 1)
        layout.addWidget(self.controlFrame, 1, 1)

    def appendToLog(self, message, level, category):
        """Add message to entries; call addToLog."""
        
        self.entries.append([message, level, category])
        self.addToLog(message, level, category)
        
    def addToLog(self, message, level, category):
        """Add to end of log while filtering and color-coding."""
        
        colors = {"Actions"  : Qt.black,
                  "Successes": Qt.green,
                  "Failures" : Qt.yellow,
                  "Errors"   : Qt.red,
                  "Details"  : Qt.darkCyan,
                  "Commands" : Qt.gray,
                  "Debugging": Qt.magenta}
        
        if configuration.LOGGING[category] and self.level >= level:
            if self.colorCode:
                self.textLog.setTextColor(colors[category])
            self.textLog.append(message)
        
    def updateLog(self):
        """Read current state of checkboxes and filter log accordingly."""
        
        # Read widget data into configuration
        for checkbox in self.checkboxes:
            configuration.LOGGING[str(checkbox.text())] = checkbox.isChecked()
        self.colorCode = self.colorCodeCheck.isChecked()
        self.level = self.levelCombo.currentIndex() + 1
        if self.level == 10:
            self.level = 1000   # Show everything.
        self.textLog.setTextColor(Qt.black)
        
        # Clear log and append messages of the checked categories
        self.textLog.clear()
        for (message, level, category) in self.entries:
            self.addToLog(message, level, category)
        
    def clearLog(self):
        """Clear text edit and entries list."""
        
        self.entries = []
        self.textLog.clear()
        
    def readCurrent(self):
        """Read current category configuration into category checkboxes."""
        
        for checkbox in self.checkboxes:
            checkbox.setChecked(configuration.LOGGING[str(checkbox.text())])
            
    def displayAll(self):
        """Set all category checkboxes to True."""
        
        for checkbox in self.checkboxes:
            checkbox.setChecked(True)
