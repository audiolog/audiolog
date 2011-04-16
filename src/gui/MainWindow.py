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

"""The Audiolog GUI main window.

This file contains two classes: MainWindow, which subclasses QMainWindow, and 
MenuBar, which subclasses QMenuBar. All other GUI files - currently LogFrame
and ConfigurationDialog - are accessed through the main window."""

import os
import threading
from functools import partial

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from etc import configuration
from etc import flowcontrol

import traverse
from LogFrame import LogFrame

from ConfigurationDialog import ConfigurationDialog

class MainWindow(QMainWindow):
    """The Audiolog GUI main window."""

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.setWindowTitle("Audiolog Music Organizer")
        self.confDialog = ConfigurationDialog(self)
        
        self.directoryPathsToScan = []
        self.running = False
        
        # Load icons
        iconsPath = os.path.join(os.path.dirname(__file__), "..", "..", "icons")
        playIcon = QIcon(os.path.join(iconsPath, "play.png"))
        pauseIcon = QIcon(os.path.join(iconsPath, "pause.png"))
        stopIcon = QIcon(os.path.join(iconsPath, "stop.png"))
        confIcon = QIcon(os.path.join(iconsPath, "configure.png"))
        logIcon = QIcon(os.path.join(iconsPath, "log.png"))
        
        # Menu and Status Bars
        self.setMenuBar(MenuBar(self))
        self.statusBar = self.statusBar()   
        
        # Top-Level Frame
        self.topLevelFrame = QFrame(self)
        
        # Graphics Frame
        self.graphicsFrame = GraphicsFrame(self.topLevelFrame)
        
        # Paths Frame
        self.pathsFrame = PathsFrame(self.topLevelFrame)
        
        # Button Frame
        self.buttonFrame = QFrame(self.topLevelFrame)
        self.flowButton = QPushButton("Start", icon=playIcon)
        self.stopButton = QPushButton("Stop", icon=stopIcon)
        self.confButton = QPushButton("Configure...", icon=confIcon)
        self.logButton = QPushButton("Show Log", icon=logIcon, checkable=True)
        self.stopButton.setEnabled(False)
        
        self.connect(self.flowButton, SIGNAL("clicked(bool)"), self.manageFlow)
        self.connect(self.stopButton, SIGNAL("clicked(bool)"), self.stop)
        self.connect(self.confButton, SIGNAL("clicked(bool)"), self.confDialog.show)
        self.connect(self.logButton, SIGNAL("clicked(bool)"), self.toggleLog)
        self.connect(flowcontrol.emitter, SIGNAL("RunEnded"), self.runEnded)
        
        buttonLayout = QHBoxLayout(self.buttonFrame)
        buttonLayout.addStretch(1)
        buttonLayout.addWidget(self.flowButton, 3)
        buttonLayout.addStretch(1)
        buttonLayout.addWidget(self.stopButton, 3)
        buttonLayout.addStretch(1)
        buttonLayout.addWidget(self.confButton, 3)
        buttonLayout.addStretch(1)
        buttonLayout.addWidget(self.logButton, 3)
        buttonLayout.addStretch(1)
        
        # Stop Button Menu (Now and Cleanly)
        stopNow = QAction("Now", self.stopButton)
        stopCleanly = QAction("After Current Directory", self.stopButton)
        self.connect(stopNow, SIGNAL("triggered()"), self.stop)
        self.connect(stopCleanly, SIGNAL("triggered()"), partial(self.stop, True))
        
        stopMenu = QMenu(self.stopButton)
        stopMenu.addAction(stopNow)
        stopMenu.addAction(stopCleanly)
        self.stopButton.setMenu(stopMenu)
        
        # Log Frame
        self.logFrame = LogFrame(self.topLevelFrame)
        self.logFrame.setSizePolicy(QSizePolicy.MinimumExpanding, 
                                    QSizePolicy.MinimumExpanding)
        self.logFrame.hide()
        
        # Top-Level Frame Layout
        layout = QVBoxLayout(self.topLevelFrame)
        layout.addWidget(self.graphicsFrame)
        layout.addWidget(self.pathsFrame)
        layout.addWidget(self.buttonFrame)
        layout.addWidget(self.logFrame)
        
        # Makes window shrink back down again after log is hidden.
        layout.setSizeConstraint(QLayout.SetFixedSize)
        self.layout().setSizeConstraint(QLayout.SetFixedSize)
        
        self.setCentralWidget(self.topLevelFrame)
        
    def manageFlow(self):
        """Start a thread if one is not running; toggle pause if one is."""
        
        if not self.running:             # Not running, start a new thread
            self.start()
        elif not flowcontrol.PAUSED:     # Currently running, pause
            self.pause()
        else:                            # Currently paused, unpause  
            self.unpause()
            
    def start(self):
        if not configuration.PATHS["TO_SCAN"]:
            self.confDialog.show()
            return
        
        self.running = True
        self.logFrame.clearLog()
        
        self.handlerThread = threading.Thread(target=traverse.handleIt)
        self.handlerThread.setDaemon(True)
        self.handlerThread.start()
        
        self.statusBar.showMessage("Audiolog running...")
        self.flowButton.setText("Pause")
        self.stopButton.setEnabled(True)
        
    def pause(self):
        flowcontrol.pause()
        self.flowButton.setText("Unpause")
        self.statusBar.showMessage("Current run paused.")
        
    def unpause(self):
        flowcontrol.unpause()
        self.flowButton.setText("Pause")
        self.statusBar.showMessage("Audiolog running...")
    
    def stop(self, cleanly=False):
        """Stop the currently running handler thread."""
        
        if not self.running:
            self.statusBar.showMessage("Audiolog isn't running.", 5)
            return
        
        if cleanly:
            self.statusBar.showMessage("Stopping after current directory is complete...")
        else:
            self.statusBar.showMessage("Stopping immediately.")
        
        flowcontrol.stop(cleanly)

    def runEnded(self, status="complete"):
        """Initialize GUI; display run status in status bar.
        
        This function is bound to the RunEnded signal which is emitted when the 
        handler thread ends, either from completion, error or being stopped."""
        
        flowcontrol.initialize()
        self.running = False
        self.flowButton.setText("Start")
        self.stopButton.setEnabled(False)
        self.statusBar.showMessage("Run %s." % status)
        
    def showConfDialog(self):
        """Display the configuration dialog box."""
        
        self.confDialog.show()
        
    def toggleLog(self):
        """Toggle the visiblity of the log."""
        
        if self.logFrame.isVisible():
            self.logFrame.hide()
        else:
            self.logFrame.show()
        

class MenuBar(QMenuBar):
    """Menu bar for the HandleIt main window."""

    def __init__(self, parent):
        super(MenuBar, self).__init__(parent)
        
        # File Menu
        start = QAction("Start", self)
        start.setStatusTip("Run Audiolog on the To Scan directory")
        self.connect(start, SIGNAL("triggered()"), self.parent().manageFlow)
        
        exit = QAction("Exit", self)
        exit.setShortcut("Ctrl+Q")
        exit.setStatusTip("Exit application")
        parent.connect(exit, SIGNAL("triggered()"), SLOT("close()"))
        
        fileMenu = self.addMenu('&File')
        fileMenu.addAction(start)
        fileMenu.addSeparator()
        fileMenu.addAction(exit)
        
        # Settings
        configure = QAction("Configure Audiolog...", self)
        self.connect(configure, SIGNAL("triggered()"), 
                     self.parent().showConfDialog)
        
        settingsMenu = self.addMenu("&Settings")
        settingsMenu.addAction(configure)


class GraphicsFrame(QFrame):
    """Frame for displaying message and visualizing process to user."""

    def __init__(self, parent=None):
        super(GraphicsFrame, self).__init__(parent)
        
        # Load images
        iconsPath = os.path.join(os.path.dirname(__file__), "..", "..", "icons")
        mgPixmap = QPixmap(os.path.join(iconsPath, "magnifying_glass.png"))
        
        self.view = QGraphicsView()
        self.view.setFrameShape(QFrame.NoFrame)
        self.view.setFrameStyle(QFrame.Plain)
        self.scene = QGraphicsScene(self)
        self.scene.setSceneRect(-100, -100, 200, 200)
        item = QGraphicsPixmapItem(mgPixmap)
        item.setPos(-128/2, -128/2)
        self.scene.addItem(item)
        self.view.setScene(self.scene)
        
        layout = QVBoxLayout(self)
        layout.addWidget(self.view)
        
        
class PathsFrame(QFrame):
    """Frame containing widgets to set all paths."""

    def __init__(self, parent=None):
        super(PathsFrame, self).__init__(parent)
        self.setMinimumWidth(500)

        folderIcon = QFileIconProvider().icon(QFileIconProvider.Folder)
        
        self.toScanLabel = QLabel("&From:")# Where?")
        self.toScanPath = QLineEdit()
        self.toScanButton = QToolButton()
        self.toScanButton.setIcon(folderIcon)
        self.toScanLabel.setBuddy(self.toScanPath)
        
        self.sortedLabel = QLabel("&To:")# Where?")
        self.sortedPath = QLineEdit()
        self.sortedButton = QToolButton()
        self.sortedButton.setIcon(folderIcon)
        self.sortedLabel.setBuddy(self.sortedPath)

        pathsLayout = QGridLayout(self)
        pathsLayout.addWidget(self.toScanLabel, 0, 0)
        pathsLayout.addWidget(self.toScanPath, 0, 1)
        pathsLayout.addWidget(self.toScanButton, 0, 2)

        pathsLayout.addWidget(self.sortedLabel, 1, 0)
        pathsLayout.addWidget(self.sortedPath, 1, 1)
        pathsLayout.addWidget(self.sortedButton, 1, 2)
        
        self.connect(self.toScanButton, SIGNAL("clicked()"), 
                     partial(self.browse, self.toScanPath))
        self.connect(self.sortedButton, SIGNAL("clicked()"), 
                     partial(self.browse, self.sortedPath))
        
        self.readCurrent()
        
    def readCurrent(self):
        """Read the current values in configuration into line edits."""
        
        self.toScanPath.setText(configuration.PATHS["TO_SCAN"][0])
        self.sortedPath.setText(configuration.PATHS["SORTED"])
        
    def applyChanges(self):
        """Read the content of line edits into configuration."""
        
        configuration.PATHS["TO_SCAN"][0] = str(self.toScanPath.text())
        configuration.PATHS["SORTED"] = str(self.sortedPath.text())
                
        configuration.saveConfigFile()

    def browse(self, lineEdit):
        """Open a file dialog to select a directory; place result in lineEdit."""
        
        # Start at the current path, if one, or at user's home directory.
        startingDirPath = lineEdit.text() or os.path.expanduser("~")            
        dirPath = QFileDialog.getExistingDirectory(self, "Select Directory", 
                                                   startingDirPath, 
                                                   QFileDialog.ShowDirsOnly)
        if dirPath:
            lineEdit.setText(dirPath)
            self.applyChanges()
                        