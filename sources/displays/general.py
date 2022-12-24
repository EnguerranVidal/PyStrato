######################## IMPORTS ########################
from dataclasses import dataclass
import os
import shutil
import sys
import time as t
import subprocess
from functools import partial
import numpy as np

# ------------------- PyQt Modules -------------------- #
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import pyqtgraph as pg
from ecom.database import CommunicationDatabase
from pyqtgraph.dockarea import Dock, DockArea
import pyqtgraph.widgets.RemoteGraphicsView

# --------------------- Sources ----------------------- #
from sources.common.FileHandling import load_settings, load_format, retrieveCSVData
from sources.common.Widgets import QCustomTabWidget
from sources.common.balloondata import BalloonPackageDatabase


######################## CLASSES ########################

class DisplayTabWidget(QMainWindow):
    def __init__(self, path):
        super(QMainWindow, self).__init__()
        self.currentDir = path
        self.formatPath = os.path.join(self.currentDir, 'formats')
        self.content = ContentStorage(self.currentDir)
        self.content.fill()
        self.settings = load_settings('settings')
        self.formats = {}

        # Central Widget -----------------------------------------------
        # self.graphCentralWindow = QCustomTabWidget()
        # self.setCentralWidget(self.graphCentralWindow)

        dock_widget_1 = QDockWidget("Dock Widget 1")
        dock_widget_2 = QDockWidget("Dock Widget 2")
        dock_widget_3 = QDockWidget("Dock Widget 3")
        dock_widget_4 = QDockWidget("Dock Widget 4")
        dock_widget_5 = QDockWidget('bruh')

        self.addDockWidget(Qt.TopDockWidgetArea, dock_widget_1)
        self.addDockWidget(Qt.RightDockWidgetArea, dock_widget_2)
        self.addDockWidget(Qt.BottomDockWidgetArea, dock_widget_3)
        self.addDockWidget(Qt.LeftDockWidgetArea, dock_widget_4)
        self.splitDockWidget(dock_widget_3, dock_widget_5, Qt.Horizontal)

        dock_widget_1.setFrameStyle(QFrame.Box | QFrame.Raised)
        dock_widget_2.setFrameStyle(QFrame.Box | QFrame.Raised)
        dock_widget_3.setFrameStyle(QFrame.Box | QFrame.Raised)
        dock_widget_4.setFrameStyle(QFrame.Box | QFrame.Raised)
        dock_widget_5.setFrameStyle(QFrame.Box | QFrame.Raised)

        self.show()


class CustomDockWidget(QDockWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.mainWindow = parent
        self.setStyleSheet("border: 1px solid gray;")

    def closeEvent(self, event):
        super().closeEvent(event)
        del self


class ContentStorage:
    def __init__(self, path):
        self.settings = load_settings('settings')
        self.currentDir = path
        self.storage = {}

    def fill(self):
        self.settings = load_settings('settings')
        paths = self.settings['FORMAT_FILES']
        for path in paths:
            path = os.path.join(self.currentDir, 'formats', path)
            if os.path.isdir(path):
                name, database = os.path.basename(path), BalloonPackageDatabase(path)
                self.storage[name] = {
                    telemetryType.id.name: {
                        dataPoint.name: []
                        for dataPoint in telemetryType.data
                    }
                    for telemetryType in database.telemetryTypes
                }

    def append(self, content):
        packageStorage = self.storage[content['parser']][content['type']]
        for key, value in content['data'].items():
            packageStorage[key].append(value)
