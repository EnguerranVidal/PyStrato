######################## IMPORTS ########################
import os
import dataclasses
import shutil
import sys
import time as t
import subprocess
from functools import partial
from typing import Optional

import numpy as np

# ------------------- PyQt Modules -------------------- #
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import pyqtgraph as pg
from pyqtgraph.dockarea import Dock, DockArea
import pyqtgraph.widgets.RemoteGraphicsView

from qtwidgets import Toggle, AnimatedToggle
from ecom.database import Unit
from ecom.datatypes import TypeInfo, DefaultValueInfo

# --------------------- Sources ----------------------- #
from sources.common.FileHandling import load_format, save_format
from sources.common.balloondata import BalloonPackageDatabase
from sources.databases.telecommands import TelecommandsWidget
from sources.databases.telemetries import TelemetriesWidget
from sources.databases.units import UnitsWidget
from sources.databases.configurations import ConfigurationsWidget


######################## CLASSES ########################
class PacketTabWidget(QMainWindow):
    def __init__(self, path):
        super(QMainWindow, self).__init__()
        self.currentDirectory = path
        self.formatPath = os.path.join(self.currentDirectory, "formats")
        self.databases = {}

        self.centralWidget = QWidget(self)
        self.setCentralWidget(self.centralWidget)

        # Left Menu Widget ---------------------------------------------
        self.databaseLeftWidget = QDockWidget('Selection')
        self.databaseMenu = DatabaseMenu()
        self.databaseLeftWidget.setWidget(self.databaseMenu)
        self.databaseLeftWidget.setAllowedAreas(Qt.LeftDockWidgetArea)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.databaseLeftWidget)

        # Setting Connects --------------------------------------------- -
        self.databaseMenu.openComboBox.currentIndexChanged.connect(self.comboBoxChanged)
        self.databaseMenu.valuesListWidget.clicked.connect(self.itemListSelected)

    def comboBoxChanged(self):
        self.databaseMenu.valuesListWidget.clear()
        # Loading New Values
        name = self.databaseMenu.openComboBox.currentText()
        if not name:
            return
        database: BalloonPackageDatabase = self.databases[name]
        if len(database.units) != 0:
            item = QListWidgetItem('Units')
            self.databaseMenu.valuesListWidget.addItem(item)
        if len(database.constants) != 0:
            item = QListWidgetItem('Constants')
            self.databaseMenu.valuesListWidget.addItem(item)
        if len(database.configurations) != 0:
            item = QListWidgetItem('Configurations')
            self.databaseMenu.valuesListWidget.addItem(item)
        if len(database.dataTypes) != 0:
            item = QListWidgetItem('Shared Data Types')
            self.databaseMenu.valuesListWidget.addItem(item)
        if len(database.telemetryTypes) != 0:
            item = QListWidgetItem('Telemetries')
            self.databaseMenu.valuesListWidget.addItem(item)
        if len(database.telecommandTypes) != 0:
            item = QListWidgetItem('Telecommands')
            self.databaseMenu.valuesListWidget.addItem(item)

    def itemListSelected(self):
        item = self.databaseMenu.valuesListWidget.currentItem()
        databaseName = self.databaseMenu.openComboBox.currentText()
        itemName = item.text()
        if item is not None:
            if itemName == 'Units':
                self.centralWidget = UnitsWidget(database=self.databases[databaseName])
                self.setCentralWidget(self.centralWidget)
            if itemName == 'Constants':
                self.setCentralWidget(QWidget(self))
            if itemName == 'Configurations':
                self.centralWidget = ConfigurationsWidget(database=self.databases[databaseName])
                self.setCentralWidget(self.centralWidget)
            if itemName == 'Shared Data Types':
                self.setCentralWidget(QWidget(self))
            if itemName == 'Telemetries':
                self.setCentralWidget(TelemetriesWidget(database=self.databases[databaseName]))
            if itemName == 'Telecommands':
                self.setCentralWidget(TelecommandsWidget(database=self.databases[databaseName]))

    def newFormat(self, name):
        databasePath = os.path.join(self.formatPath, name)
        # self.databaseMenu.openComboBox.addItem(name)
        pass

    def openFormat(self, path):
        # Loading Packet Database Folder
        database = BalloonPackageDatabase(path)
        name = os.path.basename(path)
        # Getting Database into ComboBox
        self.databases[name] = database
        self.databaseMenu.openComboBox.addItem(name)

    def saveFormat(self, path=None):
        name = self.databaseMenu.openComboBox.currentText()
        if name:
            self._saveDatabase(self.databases[name], path=path)

    def saveAllFormats(self):
        n = self.databaseMenu.openComboBox.count()
        for name in [self.databaseMenu.openComboBox.itemText(i) for i in range(n)]:
            self._saveDatabase(self.databases[name])

    @staticmethod
    def _saveDatabase(database: BalloonPackageDatabase, path: Optional[str] = None):
        if path is None:
            path = database.path
        database.save(path)

    def _closeDatabase(self, index: int):
        name = self.databaseMenu.openComboBox.itemText(index)
        if not name:
            return
        database = self.databases[name]
        referenceDatabase = BalloonPackageDatabase(database.path)
        if database != referenceDatabase:  # If changes
            messageBox = QMessageBox()
            title = "Close Format"
            message = f'WARNING !\n\nIf you close without saving, any changes made to {name}' \
                      'will be lost.\n\nSave format before closing?'
            reply = messageBox.question(self, title, message, messageBox.Yes | messageBox.No |
                                        messageBox.Cancel, messageBox.Cancel)
            if reply != messageBox.Yes and reply != messageBox.No:  # Cancel
                return
            if reply == messageBox.Yes:  # Yes Pressed
                self._saveDatabase(database)
        self.databaseMenu.openComboBox.removeItem(index)
        if self.databaseMenu.openComboBox.count() != 0:
            self.databaseMenu.openComboBox.setCurrentIndex(0)
        self.comboBoxChanged()

    def closeFormat(self):
        index = self.databaseMenu.openComboBox.currentIndex()
        if index != -1:
            self._closeDatabase(index)

    def closeAllFormat(self):
        for i in range(self.databaseMenu.openComboBox.count()):
            self._closeDatabase(0)


class DatabaseMenu(QWidget):
    def __init__(self):
        super(QWidget, self).__init__()
        # Open Files ComboBox
        self.openComboBox = QComboBox()
        # Data Values ListBox
        self.valuesListWidget = QListWidget()
        self.listedValues = []
        self.valuesListWidget.setDragDropMode(QAbstractItemView.InternalMove)
        # Number Label
        self.nbLabel = QLabel("Number of Data Values : 0")

        layout = QFormLayout()
        layout.addRow(self.openComboBox)
        layout.addRow(self.valuesListWidget)
        layout.addRow(self.nbLabel)
        layout.setVerticalSpacing(0)
        self.setLayout(layout)


class ValuePacketWidget(QWidget):
    def __init__(self):
        super(QWidget, self).__init__()
        # Sign ---------------------------------------------
        self.signToggle = Toggle()
        # Total Digits -------------------------------------
        self.totalSlider = QSlider(Qt.Vertical)
        self.totalSlider.setSingleStep(1)
        self.totalSlider.setTickInterval(1)
        self.totalSlider.setRange(0, 10)
        self.totalSlider.setTickPosition(QSlider.TicksLeft)
        self.totalLabel = QLabel('Total')
        # Float Digits -------------------------------------
        self.floatSlider = QSlider(Qt.Vertical)
        self.floatSlider.setSingleStep(1)
        self.floatSlider.setTickInterval(1)
        self.floatSlider.setRange(0, 10)
        self.floatSlider.setTickPosition(QSlider.TicksLeft)
        self.floatLabel = QLabel('Float')
        # Value Unit
        self.unitEdit = QLineEdit()
        self.nameEdit = QLineEdit()

        self.formLayout = QFormLayout()
        self.formLayout.addRow('Name:', self.nameEdit)
        self.formLayout.addRow('Unit:', self.unitEdit)
        self.formLayout.addRow('Sign', self.signToggle)
        self.leftContainer = QWidget()
        self.leftContainer.setLayout(self.formLayout)

        self.rightLayout = QGridLayout()
        self.rightLayout.addWidget(self.totalLabel, 0, 0)
        self.rightLayout.addWidget(self.totalSlider, 1, 0)
        self.rightLayout.addWidget(self.floatLabel, 0, 1)
        self.rightLayout.addWidget(self.floatSlider, 1, 1)
        self.rightContainer = QWidget()
        self.rightContainer.setLayout(self.rightLayout)

        self.layout = QHBoxLayout()
        self.layout.addWidget(self.leftContainer)
        self.layout.addWidget(self.rightContainer)

        self.setLayout(self.layout)
