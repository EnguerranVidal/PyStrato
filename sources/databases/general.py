######################## IMPORTS ########################
import os
import dataclasses
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
from pyqtgraph.dockarea import Dock, DockArea
import pyqtgraph.widgets.RemoteGraphicsView

from qtwidgets import Toggle, AnimatedToggle
from ecom.database import Unit
from ecom.datatypes import TypeInfo, DefaultValueInfo

# --------------------- Sources ----------------------- #
from sources.common.FileHandling import load_format, save_format
from sources.common.balloondata import BalloonPackageDatabase
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
        if len(database.telecommands) != 0:
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
                self.setCentralWidget(QWidget(self))
            if itemName == 'Telecommands':
                self.setCentralWidget(QWidget(self))

    def newFormat(self, name):
        databasePath = os.path.join(self.formatPath, name)
        pass
        # self.databaseMenu.openComboBox.addItem(name)

    def openFormat(self, path):
        # Loading Packet Database Folder
        database = BalloonPackageDatabase(path)
        name = os.path.basename(path)
        # Getting Database into ComboBox
        self.databases[name] = database
        self.databaseMenu.openComboBox.addItem(name)

    def saveFormat(self, path=None):
        name = self.databaseMenu.openComboBox.currentText()
        if len(name) != 0:
            if path is None:
                path = self.databases[name]['PATH']
            else:
                self.databases[name]['PATH'] = path
            formatLine = self.databases[name]
            formatLine['NAME'] = name
            save_format(formatLine, path)

    def saveAllFormats(self):
        n = self.databaseMenu.openComboBox.count()
        for name in [self.databaseMenu.openComboBox.itemText(i) for i in range(n)]:
            save_format(self.databases[name], self.databases[name]['PATH'])

    def closeFormat(self):
        name = self.databaseMenu.openComboBox.currentText()
        print(name)
        if name != '':
            path = self.databases[name]['PATH']
            name, formatLine = load_format(path)
            if formatLine != self.databases[name]:
                messageBox = QMessageBox()
                title = "Close Format"
                message = "WARNING !\n\nIf you close without saving, any changes made to the format" \
                          "will be lost.\n\nSave format before closing?"
                reply = messageBox.question(self, title, message, messageBox.Yes | messageBox.No |
                                            messageBox.Cancel, messageBox.Cancel)
                if reply == messageBox.Yes or reply == messageBox.No:
                    if reply == messageBox.Yes:
                        save_format(self.databases[name], path)
                    index = self.databaseMenu.openComboBox.currentIndex()
                    self.databaseMenu.openComboBox.removeItem(index)
                    self.databaseMenu.openComboBox.setCurrentIndex(0)
                    self.comboBoxChanged()

    def closeAllFormat(self):
        n = self.databaseMenu.openComboBox.count()
        names = [self.databaseMenu.openComboBox.itemText(i) for i in range(n)]
        changes = []
        for i in range(n):
            name, formatLine = load_format(self.databases[names[i]]['PATH'])
            changes.append(formatLine != self.databases[name])
        if True in changes:
            messageBox = QMessageBox()
            title = "Close Format"
            message = "WARNING !\n\nIf you quit without saving, any changes made to the balloonFormats" \
                      "will be lost.\n\nSave format before quitting?"
            reply = messageBox.question(self, title, message, messageBox.Yes | messageBox.No |
                                        messageBox.Cancel, messageBox.Cancel)
            if reply == messageBox.Yes or reply == messageBox.No:
                if reply == messageBox.Yes:
                    for i in range(n):
                        save_format(self.databases[names[i]], self.databases[names[i]]['PATH'])
                self.databaseMenu.openComboBox.clear()


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
