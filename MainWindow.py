# -*- coding: utf-8 -*-

"""The HandleIt GUI main window.

This file contains two classes: MainWindow, which subclasses QMainWindow, and 
MenuBar, which subclasses QMenuBar. All other GUI files - currently LogFrame
and ConfigurationDialog - are accessed through the main window. """

import threading
from functools import partial

from PyQt4.QtCore import *
from PyQt4.QtGui import *

import configuration
import traverse
import flowcontrol

from ConfigurationDialog import ConfigurationDialog
from LogFrame import LogFrame

class MainWindow(QMainWindow):
    """The HandleIt GUI main window."""

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.setWindowTitle("Azul Music Organizer")
        self.confDialog = ConfigurationDialog(self)
        
        self.directoryPathsToScan = []
        self.running = False
        
        # Menu and Status Bars
        self.setMenuBar(MenuBar(self))
        self.statusBar = self.statusBar()
        self.statusBar.showMessage("Azul launched.")      
        
        # Top-Level Frame
        self.topLevelFrame = QFrame(self)
        self.logFrame = LogFrame(self.topLevelFrame)
        self.logFrame.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
        
        # Button Frame
        self.buttonFrame = QFrame(self.topLevelFrame)
        self.flowButton = QPushButton("Start")
        self.stopButton = QPushButton("Stop")
        self.confButton = QPushButton("Configure...")
        self.stopButton.setEnabled(False)
        
        self.connect(self.flowButton, SIGNAL("clicked(bool)"), self.manageFlow)
        self.connect(self.stopButton, SIGNAL("clicked(bool)"), self.stop)
        self.connect(self.confButton, SIGNAL("clicked(bool)"), self.confDialog.show)
        self.connect(flowcontrol.emitter, SIGNAL("RunEnded"), self.runEnded)
        
        buttonLayout = QHBoxLayout(self.buttonFrame)
        buttonLayout.addWidget(self.flowButton)
        buttonLayout.addWidget(self.stopButton)
        buttonLayout.addWidget(self.confButton)
        
        # Stop Button Menu (Now and Cleanly)
        stopNow = QAction("Now", self.stopButton)
        stopCleanly = QAction("After Current Directory", self.stopButton)
        self.connect(stopNow, SIGNAL("triggered()"), self.stop)
        self.connect(stopCleanly, SIGNAL("triggered()"), partial(self.stop, True))
        
        stopMenu = QMenu(self.stopButton)
        stopMenu.addAction(stopNow)
        stopMenu.addAction(stopCleanly)
        self.stopButton.setMenu(stopMenu)
        
        # Top-Level Frame Layout
        layout = QVBoxLayout(self.topLevelFrame)
        layout.addWidget(self.logFrame)
        layout.addWidget(self.buttonFrame)
        
        self.setCentralWidget(self.topLevelFrame)
        
    def manageFlow(self):
        """Start a thread if one is not running; toggle pause if one is."""

        if not self.directoryPathsToScan:
            self.confDialog.show()
            return
        
        if not self.running:                                # Not running, start a new thread
            self.running = True
            self.logFrame.clearLog()

            args = {"directoryPathsToScan": self.directoryPathsToScan}
            self.handlerThread = threading.Thread(target=traverse.handleIt, kwargs=args)
            self.handlerThread.setDaemon(True)
            self.handlerThread.start()
            
            self.statusBar.showMessage("Azul running...")
            self.flowButton.setText("Pause")
            self.stopButton.setEnabled(True)
            
        elif not flowcontrol.PAUSED:                        # Currently running, pause
            flowcontrol.pause()
            self.flowButton.setText("Unpause")
            self.statusBar.showMessage("Current run paused.")
            
        else:                                               # Currently paused, unpause  
            flowcontrol.unpause()
            self.flowButton.setText("Pause")
            self.statusBar.showMessage("Azul running...")

    def stop(self, cleanly=False):
        """Stop the currently running handler thread."""
        
        if not self.running:
            self.statusBar.showMessage("Azul isn't running.", 5)
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
        self.statusBar.showMessage("Run " + status + ".")
        
    def showConfDialog(self):
        """Display the configuration dialog box."""
        
        self.confDialog.show()
        

class MenuBar(QMenuBar):
    """Menu bar for the HandleIt main window."""

    def __init__(self, parent):
        super(MenuBar, self).__init__(parent)
        
        # File Menu
        start = QAction("Start", self)
        start.setStatusTip("Run Azul on the To Scan directory")
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
        configure = QAction("Configure Azul...", self)
        self.connect(configure, SIGNAL("triggered()"), self.parent().showConfDialog)
        
        settingsMenu = self.addMenu("&Settings")
        settingsMenu.addAction(configure)
