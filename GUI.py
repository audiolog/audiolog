import threading
import pickle
from functools import partial

from PyQt4.QtCore import *
from PyQt4.QtGui import *

import constants
import traverse

class MainWindow(QMainWindow):

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.setWindowTitle("HandleIt Music Manager")
        self.confDialog = ConfigurationDialog(self)
        
        self.directoryPathsToScan = []
        self.running = False
        self.paused = False
        
        self.statusBar = self.statusBar()
        self.statusBar.showMessage("HandleIt launched.")
        
        # Top-Level Frame
        self.topLevelFrame = QFrame(self)
        self.topLevelFrame.setFrameStyle(QFrame.StyledPanel)
        self.logFrame = LogFrame(self.topLevelFrame)
        
        # Button Frame
        self.buttonFrame = QFrame(self.topLevelFrame)
        self.flowButton = QPushButton("Start New Run")
        self.stopButton = QPushButton("End Current Run")
        self.confButton = QPushButton("Configure...")
        self.stopButton.setEnabled(False)
        
        self.connect(self.flowButton, SIGNAL("clicked(bool)"), self.manageFlow)
        self.connect(self.stopButton, SIGNAL("clicked(bool)"), self.stop)
        self.connect(self.confButton, SIGNAL("clicked(bool)"), self.confDialog.show)
        self.connect(constants.emitter, SIGNAL("RunEnded"), self.runEnded)
        
        buttonLayout = QHBoxLayout(self.buttonFrame)
        buttonLayout.addWidget(self.flowButton)
        buttonLayout.addWidget(self.stopButton)
        buttonLayout.addWidget(self.confButton)
        
        # Top-Level Frame Layout
        layout = QVBoxLayout(self.topLevelFrame)
        layout.addWidget(self.logFrame)
        layout.addWidget(self.buttonFrame)
        
        self.setCentralWidget(self.topLevelFrame)
        
    def manageFlow(self):
        """Start a thread if one is not running or toggle pause if there is"""

        if not self.directoryPathsToScan:
            self.confDialog.show()
            return
        
        
        if not self.running:                                # Not running, start a new thread
            self.running = True

            args = {"directoryPathsToScan": self.directoryPathsToScan}
            self.handlerThread = threading.Thread(target=traverse.handleIt, kwargs=args)
            self.handlerThread.setDaemon(True)
            self.handlerThread.start()
            
            self.statusBar.showMessage("HandleIt running...")
            self.flowButton.setText("Pause")
            self.stopButton.setEnabled(True)
            
        elif not self.paused:                               # Currently running, pause
            constants.PAUSE_LOCK.acquire()
            self.flowButton.setText("Unpause")
            self.statusBar.showMessage("Current run paused.")
            self.paused = True
            
        else:                                               # Currently paused, unpause  
            constants.PAUSE_LOCK.release()
            self.flowButton.setText("Pause")
            self.statusBar.showMessage("HandleIt running...")
            self.paused = False

    def stop(self):
        """Kill the currently running handler thread
        
        Uses the "accepted" solution to kill a thread short of finding its PID and killing it."""
        
        constants.DIE = True
        if self.paused:         # Allows us to stop while paused
            constants.PAUSE_LOCK.release()
            self.paused = False
        self.statusBar.showMessage("Stopping...")
        self.stopButton.setEnabled(False)

    def runEnded(self, status="complete"):
        """Called when the handler thread ends, either from completion, error or being stopped"""
        
        self.running = False
        self.flowButton.setText("Start New Run")
        self.stopButton.setEnabled(False)
        self.statusBar.showMessage("Run " + status + ".")
        
    def showConfDialog(self):
        self.confDialog.show()
        

class LogFrame(QFrame):
    
    def __init__(self, parent=None):
        super(LogFrame, self).__init__(parent)
        self.textLog = QTextEdit()
        self.textLog.setReadOnly(True)
        self.textLog.setMinimumHeight(200)
        self.connect(constants.emitter, SIGNAL("AppendToLog"), self.textLog.append)
        self.connect(constants.emitter, SIGNAL("ClearLog"), self.textLog.clear)
        layout = QVBoxLayout(self)
        layout.addWidget(self.textLog)

#-------------------------------------------
# Dialogs
#-------------------------------------------

class ConfigurationDialog(QDialog):
    
    def __init__(self, parent):
        super(ConfigurationDialog, self).__init__(parent)
        self.setWindowTitle("Configure HandleIt")
        
        self.configurationFileName = ".handleit"
        
        # Actions Checkboxes
        self.actionsGroup = QGroupBox("Actions")
        self.extractCheck = QCheckBox("Extract Archives")
        self.imageCheck = QCheckBox("Handle Images")
        self.cleanCheck = QCheckBox("Delete Miscellaneous Files")
        self.convertCheck = QCheckBox("Convert Unwanted Audio Formats")
        self.splitCheck = QCheckBox("Split One-File Albums")
        self.audioCheck = QCheckBox("Handle Audio")
        
        actionsLayout = QVBoxLayout(self.actionsGroup)
        actionsLayout.addWidget(self.extractCheck)
        actionsLayout.addWidget(self.imageCheck)
        actionsLayout.addWidget(self.cleanCheck)
        actionsLayout.addWidget(self.convertCheck)
        actionsLayout.addWidget(self.splitCheck)
        actionsLayout.addWidget(self.audioCheck)
        
        # Settings Checkboxes
        self.settingsGroup = QGroupBox("Settings")
        self.recurseCheck = QCheckBox("Recursively Handle Folders")
        self.simulateCheck = QCheckBox("Simulate Run (No Modifications)")
        self.promptCheck = QCheckBox("Prompt on Modification")
        self.deleteCheck = QCheckBox("Permanently Delete Unwanted Items")
        self.getPUIDCheck = QCheckBox("Fetch PUIDs")
        
        settingsLayout = QVBoxLayout(self.settingsGroup)
        settingsLayout.addWidget(self.recurseCheck)
        settingsLayout.addWidget(self.simulateCheck)
        settingsLayout.addWidget(self.promptCheck)
        settingsLayout.addWidget(self.deleteCheck)
        settingsLayout.addWidget(self.getPUIDCheck)
        
        # Paths Selection
        folderIcon = QFileIconProvider().icon(QFileIconProvider.Folder)
        self.pathsGroup = QGroupBox("Paths")
        
        self.baseDirLabel = QLabel("&Base Directory")
        self.baseDirPath = QLineEdit()
        self.baseDirButton = QToolButton()
        self.baseDirButton.setIcon(folderIcon)
        
        self.archivesLabel = QLabel("&Archives Path")
        self.archivesPath = QLineEdit()
        self.archivesButton = QToolButton()
        self.archivesButton.setIcon(folderIcon)
        
        self.rejectsLabel = QLabel("&Rejects Path")
        self.rejectsPath = QLineEdit()
        self.rejectsButton = QToolButton()
        self.rejectsButton.setIcon(folderIcon)
        
        self.sortedLabel = QLabel("&Sorted Path")
        self.sortedPath = QLineEdit()
        self.sortedButton = QToolButton()
        self.sortedButton.setIcon(folderIcon)
        
        self.deletesLabel = QLabel("&Deletes Path")
        self.deletesPath = QLineEdit()
        self.deletesButton = QToolButton()
        self.deletesButton.setIcon(folderIcon)
        
        self.baseDirLabel.setBuddy(self.baseDirPath)
        self.archivesLabel.setBuddy(self.archivesPath)
        self.rejectsLabel.setBuddy(self.rejectsPath)
        self.sortedLabel.setBuddy(self.sortedPath)
        self.deletesLabel.setBuddy(self.deletesPath)

        pathsLayout = QGridLayout(self.pathsGroup)
        pathsLayout.addWidget(self.baseDirLabel, 0, 0, 1, 2)
        pathsLayout.addWidget(self.baseDirPath, 1, 0)
        pathsLayout.addWidget(self.baseDirButton, 1, 1)
        pathsLayout.addWidget(self.archivesLabel, 2, 0, 1, 2)
        pathsLayout.addWidget(self.archivesPath, 3, 0)
        pathsLayout.addWidget(self.archivesButton, 3, 1)
        pathsLayout.addWidget(self.rejectsLabel, 4, 0, 1, 2)
        pathsLayout.addWidget(self.rejectsPath, 5, 0)
        pathsLayout.addWidget(self.rejectsButton, 5, 1)
        pathsLayout.addWidget(self.sortedLabel, 6, 0, 1, 2)
        pathsLayout.addWidget(self.sortedPath, 7, 0)
        pathsLayout.addWidget(self.sortedButton, 7, 1)
        pathsLayout.addWidget(self.deletesLabel, 8, 0, 1, 2)
        pathsLayout.addWidget(self.deletesPath, 9, 0)
        pathsLayout.addWidget(self.deletesButton, 9, 1)
        
        self.connect(self.baseDirButton, SIGNAL("clicked()"), partial(self.browse, self.baseDirPath))
        self.connect(self.archivesButton, SIGNAL("clicked()"), partial(self.browse, self.archivesPath))
        self.connect(self.rejectsButton, SIGNAL("clicked()"), partial(self.browse, self.rejectsPath))
        self.connect(self.sortedButton, SIGNAL("clicked()"), partial(self.browse, self.sortedPath))
        self.connect(self.deletesButton, SIGNAL("clicked()"), partial(self.browse, self.deletesPath))
        
        # Button Box
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok|QDialogButtonBox.Cancel)
        self.buttonBox.button(QDialogButtonBox.Ok).setDefault(True)
        
        self.connect(self.buttonBox, SIGNAL("accepted()"), self.applyChanges)
        self.connect(self.buttonBox, SIGNAL("rejected()"), self.cancel)
        
        # Dialog Layout
        layout = QVBoxLayout(self)
        layout.addWidget(self.actionsGroup)
        layout.addWidget(self.settingsGroup)
        layout.addWidget(self.pathsGroup)
        layout.addWidget(self.buttonBox)
        
        self.readCurrent()

    def readCurrent(self):
        """Reads the current values in constants into dialog widgets"""
        
        configuration = self.loadConfigurationFile(self.configurationFileName)
        
        # Actions
        self.extractCheck.setChecked(configuration["ACTIONS"]["EXTRACT"])
        self.imageCheck.setChecked(configuration["ACTIONS"]["IMAGE"])
        self.cleanCheck.setChecked(configuration["ACTIONS"]["CLEAN"])
        self.convertCheck.setChecked(configuration["ACTIONS"]["CONVERT"])
        self.splitCheck.setChecked(configuration["ACTIONS"]["SPLIT"])
        self.audioCheck.setChecked(configuration["ACTIONS"]["AUDIO"])
        
        # Settings
        self.recurseCheck.setChecked(configuration["SETTINGS"]["RECURSE"])
        self.simulateCheck.setChecked(configuration["SETTINGS"]["SIMULATE"])
        self.promptCheck.setChecked(configuration["SETTINGS"]["PROMPT"])
        self.deleteCheck.setChecked(configuration["SETTINGS"]["DELETE"])
        self.getPUIDCheck.setChecked(configuration["SETTINGS"]["GET_PUID"])
        
        # Paths
        self.baseDirPath.setText(configuration["PATHS"]["BASE_DIR"])
        self.archivesPath.setText(configuration["PATHS"]["ARCHIVES"][0])
        self.rejectsPath.setText(configuration["PATHS"]["REJECTS"])
        self.sortedPath.setText(configuration["PATHS"]["SORTED"])
        self.deletesPath.setText(configuration["PATHS"]["DELETES"])

    def browse(self, lineEdit):
        startingDirPath = lineEdit.text()
        if not startingDirPath:
            startingDirPath = self.baseDirPath.text()
        directory = QFileDialog.getExistingDirectory(self, "Select Directory", startingDirPath, QFileDialog.ShowDirsOnly)
        if directory:
            lineEdit.setText(directory)

    def applyChanges(self):
        """Read the content of settings widgets into constants variables then hide"""
        
        # Actions
        constants.ACTIONS["EXTRACT"] = self.extractCheck.isChecked()
        constants.ACTIONS["IMAGE"] = self.imageCheck.isChecked()
        constants.ACTIONS["CLEAN"] = self.cleanCheck.isChecked()
        constants.ACTIONS["CONVERT"] = self.convertCheck.isChecked()
        constants.ACTIONS["SPLIT"] = self.splitCheck.isChecked()
        constants.ACTIONS["AUDIO"] = self.audioCheck.isChecked()        
        
        # Settings
        constants.SETTINGS["RECURSE"] = self.recurseCheck.isChecked()
        constants.SETTINGS["SIMULATE"] = self.simulateCheck.isChecked()
        constants.SETTINGS["PROMPT"] = self.promptCheck.isChecked()
        constants.SETTINGS["DELETE"] = self.deleteCheck.isChecked()
        constants.SETTINGS["GET_PUID"] = self.getPUIDCheck.isChecked()
        
        # Paths
        constants.PATHS["BASE_DIR"] = self.baseDirPath.text()
        constants.PATHS["REJECTS"] = self.rejectsPath.text()
        constants.PATHS["SORTED"] = self.sortedPath.text()
        constants.PATHS["DELETES"] = self.deletesPath.text()
        
        if self.archivesPath.text() and self.archivesPath.text() not in self.parent().directoryPathsToScan:
            self.parent().directoryPathsToScan.append(self.archivesPath.text())
            constants.PATHS["ARCHIVES"][0] = self.archivesPath.text()
        
        self.saveConfigurationFile(self.configurationFileName, {"ACTIONS": constants.ACTIONS, "SETTINGS": constants.SETTINGS, "PATHS": constants.PATHS})
        
        self.hide()
    
    def loadConfigurationFile(self, fileName):
        """Unserializes the configuration at fileName and returns it."""
        
        try:
            f = open(fileName, "r")
        except: # File probably doesn't exist yet.
            return {"ACTIONS": constants.ACTIONS, "SETTINGS": constants.SETTINGS, "PATHS": constants.PATHS} # Use the default values.
        
        configuration = pickle.load(f)
        f.close()
        
        return configuration
   
    def saveConfigurationFile(self, fileName, configuration):
        """Serializes configuration and saves it to fileName."""
        
        f = open(fileName, "w")
        pickle.dump(configuration, f)
        f.close()

    def cancel(self):
        """Hide dialog then roll back any changes in widgets by reading from constants"""
        
        self.hide()
        self.readCurrent()
        
        