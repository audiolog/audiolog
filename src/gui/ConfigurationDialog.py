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
        self.optionsFrame = OptionsFrame(self)
        
        self.tabs = QTabWidget(self)
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
        """Read the current values of configuration into dialog widgets."""
        
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
                
        configuration.saveConfigFile()
        
        self.hide()

    def cancel(self):
        """Hide dialog; read from configuration to roll back changes in widgets."""
        
        self.hide()
        self.readCurrent()
        

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
