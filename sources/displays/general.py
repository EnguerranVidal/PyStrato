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

        dock_widget_1 = HoverWidget("Dock Widget 1")
        dock_widget_2 = HoverWidget("Dock Widget 2")
        dock_widget_3 = HoverWidget('Dock Widget 3')
        dock_widget_4 = HoverWidget("Dock Widget 4")
        dock_widget_5 = HoverWidget('bruh')

        self.addDockWidget(Qt.TopDockWidgetArea, dock_widget_1)
        self.addDockWidget(Qt.RightDockWidgetArea, dock_widget_2)
        self.addDockWidget(Qt.BottomDockWidgetArea, dock_widget_3)
        self.addDockWidget(Qt.LeftDockWidgetArea, dock_widget_4)
        self.splitDockWidget(dock_widget_3, dock_widget_5, Qt.Horizontal)

        self.show()


class HoverWidget(QDockWidget):
    def __init__(self, name: str):
        super().__init__()
        self.setWindowTitle(name)
        self.setStyleSheet('border: 2px solid grey;')
        self.button = HoverButton(self)
        self.button.setVisible(False)

        # Create the central widget and add the button to it
        centralWidget = QWidget()
        layout = QVBoxLayout(centralWidget)
        layout.addWidget(self.button)

        # Set the central widget of the dock widget
        self.setWidget(centralWidget)

        # Set the size of the widget to be 500x500 pixels
        self.resize(500, 500)

    def enterEvent(self, event):
        # Animate the button from the top of the widget to the top right corner
        self.button.animation.setStartValue(self.button.pos())
        self.button.animation.setEndValue(QPoint(self.width() - self.button.width(), 0))
        self.button.animation.start()
        self.button.setVisible(True)

    def leaveEvent(self, event):
        # Animate the button back to the top of the widget
        self.button.animation.setStartValue(self.button.pos())
        self.button.animation.setEndValue(QPoint(self.width() - self.button.width(), -self.button.height()))
        self.button.animation.start()
        self.button.setVisible(False)

    def closeEvent(self, event):
        super().closeEvent(event)
        del self


class HoverButton(QPushButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Set the icon and icon size
        self.setIcon(QIcon('sources/icons/stack-icon.svg'))
        self.setIconSize(QSize(25, 25))

        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setStyleSheet('border: none;')
        self.setAutoFillBackground(False)
        self.setFlat(True)

        # Create an animation to move the button
        self.animation = QPropertyAnimation(self, b'pos')
        self.animation.setDuration(250)
        self.animation.setEasingCurve(QEasingCurve.OutQuad)

        # Set the initial position of the button to be off the screen
        self.move(self.parent().width() - self.width(), -self.height())

    def setIconSize(self, size):
        super().setIconSize(size)
        self.setFixedSize(size)

    def sizeHint(self):
        return self.iconSize()


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
