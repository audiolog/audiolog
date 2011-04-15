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

"""Dialog box for viewing and editing HandleIt configuration.

This configuration dialog box uses to tabs to group and display related 
widgets. Currently there are two tabs: path and settings.

If there is a ".handleit" file in the working directory we use that to
initialize the dialog widgets, otherwise we use the defaults in configuration.
If the user makes any changes and clicks OK then the contents of the dialog
widgets are read into configuration and a new ".handleit" file is created.
If the user makes changes and clicks Cancel, the current values in 
configuration are read back into the dialog widgets."""

import os
from functools import partial

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from etc import configuration

class ConfigurationDialog(QDialog):
    """Dialog box for viewing and editing HandleIt configuration."""
    
    def __init__(self, parent):
        super(ConfigurationDialog, self).__init__(parent)
        self.setWindowTitle("Configure Audiolog")
        
        # Tabs
        self.pathsFrame = PathsFrame(self)
        self.optionsFrame = OptionsFrame(self)
        
        self.tabs = QTabWidget(self)
        self.tabs.addTab(self.pathsFrame, "&Paths")
        self.tabs.addTab(self.optionsFrame, "Optio&ns")     
       
        # Button Box
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok|QDialogButtonBox.Cancel)
        self.buttonBox.button(QDialogButtonBox.Ok).setDefault(True)
        
        self.connect(self.buttonBox, SIGNAL("accepted()"), self.applyChanges)
        self.connect(self.buttonBox, SIGNAL("rejected()"), self.cancel)
        
        # Dialog Layout
        layout = QVBoxLayout(self)
        layout.addWidget(self.tabs)
        layout.addWidget(self.buttonBox)
        
        self.readCurrent()

    def readCurrent(self):
        """Read the current values in configuration into dialog widgets."""
        
        configuration.loadConfigFile()
        
        # Actions
        self.optionsFrame.extractCheck.setChecked(configuration.ACTIONS["EXTRACT"])
        self.optionsFrame.imageCheck.setChecked(configuration.ACTIONS["IMAGE"])
        self.optionsFrame.cleanCheck.setChecked(configuration.ACTIONS["CLEAN"])
        self.optionsFrame.convertCheck.setChecked(configuration.ACTIONS["CONVERT"])
        self.optionsFrame.splitCheck.setChecked(configuration.ACTIONS["SPLIT"])
        self.optionsFrame.audioCheck.setChecked(configuration.ACTIONS["METADATA"])
        
        # Settings
        self.optionsFrame.recurseCheck.setChecked(configuration.SETTINGS["RECURSE"])
        self.optionsFrame.deleteCheck.setChecked(configuration.SETTINGS["DELETE"])
        self.optionsFrame.getPrintCheck.setChecked(configuration.SETTINGS["GET_PRINT"])
        
        # Paths
        self.pathsFrame.baseDirPath.setText(configuration.PATHS["BASE_DIR"])
        self.pathsFrame.rejectsPath.setText(configuration.PATHS["REJECTS"])
        self.pathsFrame.deletesPath.setText(configuration.PATHS["DELETES"])
        self.pathsFrame.sortedPath.setText(configuration.PATHS["SORTED"])
        self.pathsFrame.toScanPath.setText(configuration.PATHS["TO_SCAN"][0])

    def applyChanges(self):
        """Read the content of dialog widgets into configuration then hide dialog."""
        
        # Actions
        configuration.ACTIONS["EXTRACT"] = self.optionsFrame.extractCheck.isChecked()
        configuration.ACTIONS["IMAGE"] = self.optionsFrame.imageCheck.isChecked()
        configuration.ACTIONS["CLEAN"] = self.optionsFrame.cleanCheck.isChecked()
        configuration.ACTIONS["CONVERT"] = self.optionsFrame.convertCheck.isChecked()
        configuration.ACTIONS["SPLIT"] = self.optionsFrame.splitCheck.isChecked()
        configuration.ACTIONS["METADATA"] = self.optionsFrame.audioCheck.isChecked()        
        
        # Settings
        configuration.SETTINGS["RECURSE"] = self.optionsFrame.recurseCheck.isChecked()
        configuration.SETTINGS["DELETE"] = self.optionsFrame.deleteCheck.isChecked()
        configuration.SETTINGS["GET_PRINT"] = self.optionsFrame.getPrintCheck.isChecked()
        
        # Paths
        configuration.PATHS["BASE_DIR"] = str(self.pathsFrame.baseDirPath.text())
        configuration.PATHS["REJECTS"] = str(self.pathsFrame.rejectsPath.text())
        configuration.PATHS["DELETES"] = str(self.pathsFrame.deletesPath.text())
        configuration.PATHS["SORTED"] = str(self.pathsFrame.sortedPath.text())
        
        configuration.PATHS["TO_SCAN"][0] = str(self.pathsFrame.toScanPath.text())
        
        #toScanPath = str(self.pathsFrame.toScanPath.text())
        #if toScanPath and toScanPath not in self.parent().directoryPathsToScan:
            #self.parent().directoryPathsToScan.append(toScanPath)
            #configuration.PATHS["TO_SCAN"][0] = toScanPath
        
        configuration.saveConfigFile()
        
        self.hide()

    def cancel(self):
        """Hide dialog; read from configuration to roll back changes in widgets."""
        
        self.hide()
        self.readCurrent()
     

class PathsFrame(QFrame):
    """Frame containing widgets to set all paths."""

    def __init__(self, parent=None):
        super(PathsFrame, self).__init__(parent)

        folderIcon = QFileIconProvider().icon(QFileIconProvider.Folder)
        
        self.baseDirLabel = QLabel("&Base Directory")
        self.baseDirPath = QLineEdit()
        self.baseDirButton = QToolButton()
        self.baseDirButton.setIcon(folderIcon)
        
        self.rejectsLabel = QLabel("&Rejects Path")
        self.rejectsPath = QLineEdit()
        self.rejectsButton = QToolButton()
        self.rejectsButton.setIcon(folderIcon)
        
        self.deletesLabel = QLabel("&Deletes Path")
        self.deletesPath = QLineEdit()
        self.deletesButton = QToolButton()
        self.deletesButton.setIcon(folderIcon)
        
        self.sortedLabel = QLabel("&Sorted Path")
        self.sortedPath = QLineEdit()
        self.sortedButton = QToolButton()
        self.sortedButton.setIcon(folderIcon)
        
        self.toScanLabel = QLabel("&To Scan Path")
        self.toScanPath = QLineEdit()
        self.toScanButton = QToolButton()
        self.toScanButton.setIcon(folderIcon)
                
        self.baseDirLabel.setBuddy(self.baseDirPath)
        self.rejectsLabel.setBuddy(self.rejectsPath)
        self.sortedLabel.setBuddy(self.sortedPath)
        self.deletesLabel.setBuddy(self.deletesPath)
        self.toScanLabel.setBuddy(self.toScanPath)

        pathsLayout = QGridLayout(self)
        pathsLayout.addWidget(self.baseDirLabel, 0, 0, 1, 2)
        pathsLayout.addWidget(self.baseDirPath, 1, 0)
        pathsLayout.addWidget(self.baseDirButton, 1, 1)

        pathsLayout.addWidget(self.rejectsLabel, 2, 0, 1, 2)
        pathsLayout.addWidget(self.rejectsPath, 3, 0)
        pathsLayout.addWidget(self.rejectsButton, 3, 1)
        
        pathsLayout.addWidget(self.deletesLabel, 4, 0, 1, 2)
        pathsLayout.addWidget(self.deletesPath, 5, 0)
        pathsLayout.addWidget(self.deletesButton, 5, 1)
                
        pathsLayout.addWidget(self.sortedLabel, 6, 0, 1, 2)
        pathsLayout.addWidget(self.sortedPath, 7, 0)
        pathsLayout.addWidget(self.sortedButton, 7, 1)        

        pathsLayout.addWidget(self.toScanLabel, 8, 0, 1, 2)
        pathsLayout.addWidget(self.toScanPath, 9, 0)
        pathsLayout.addWidget(self.toScanButton, 9, 1)
        
        self.connect(self.baseDirButton, SIGNAL("clicked()"), partial(self.browse, self.baseDirPath))
        self.connect(self.rejectsButton, SIGNAL("clicked()"), partial(self.browse, self.rejectsPath))
        self.connect(self.deletesButton, SIGNAL("clicked()"), partial(self.browse, self.deletesPath))
        self.connect(self.sortedButton, SIGNAL("clicked()"), partial(self.browse, self.sortedPath))
        self.connect(self.toScanButton, SIGNAL("clicked()"), partial(self.browse, self.toScanPath))
        
        # If baseDirPath is changed, these will change relatively (if they are empty)
        self.relatedPaths = [("Rejects", self.rejectsPath), ("Deletes", self.deletesPath), ("Sorted", self.sortedPath)]


    def browse(self, lineEdit):
        """Open a file dialog to select a directory; place result in lineEdit."""
        
        # Start at the current path, if one, or at baseDir, if one, else at CWD
        startingDirPath = lineEdit.text()
        if not startingDirPath:
            startingDirPath = self.baseDirPath.text()
            
        directory = QFileDialog.getExistingDirectory(self, "Select Directory", startingDirPath, QFileDialog.ShowDirsOnly)
        if directory:
            lineEdit.setText(directory)
        
            # If baseDirPath has been changed, change other paths relatively (if they are empty)
            if lineEdit == self.baseDirPath:
                for (name, lineEdit) in self.relatedPaths:
                    if not lineEdit.text():
                        lineEdit.setText(os.path.join(str(directory), name, ""))
                        

class OptionsFrame(QFrame):
    """Frame containing checkboxes for actions and settings."""

    def __init__(self, parent=None):
        super(OptionsFrame, self).__init__(parent)
     
        # Actions
        self.actionsGroup = QGroupBox("Actions")
        self.extractCheck = QCheckBox("Extract archives")
        self.imageCheck = QCheckBox("Handle images")
        self.cleanCheck = QCheckBox("Delete miscellaneous files")
        self.convertCheck = QCheckBox("Convert unwanted audio formats")
        self.splitCheck = QCheckBox("Split one-file albums")
        self.audioCheck = QCheckBox("Identify, tag and rename audio")
        
        actionsLayout = QVBoxLayout(self.actionsGroup)
        actionsLayout.addWidget(self.extractCheck)
        actionsLayout.addWidget(self.imageCheck)
        actionsLayout.addWidget(self.cleanCheck)
        actionsLayout.addWidget(self.convertCheck)
        actionsLayout.addWidget(self.splitCheck)
        actionsLayout.addWidget(self.audioCheck)
        
        # Settings
        self.settingsGroup = QGroupBox("Settings")
        self.recurseCheck = QCheckBox("Recursively handle folders")
        self.deleteCheck = QCheckBox("Permanently delete unwanted items")
        self.getPrintCheck = QCheckBox("Generate audio fingerprints")
        
        settingsLayout = QVBoxLayout(self.settingsGroup)
        settingsLayout.addWidget(self.recurseCheck)
        settingsLayout.addWidget(self.deleteCheck)
        settingsLayout.addWidget(self.getPrintCheck)
        
        # Layout
        optionsLayout = QVBoxLayout(self)
        optionsLayout.addWidget(self.actionsGroup)
        optionsLayout.addWidget(self.settingsGroup)
        
