# -*- coding: utf-8 -*-

"""HandleIt program launcher.

This file has only one function: to start the GUI."""

import sys

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from MainWindow import MainWindow

app = QApplication(sys.argv)
mainWindow = MainWindow()
mainWindow.show()
app.exec_()
