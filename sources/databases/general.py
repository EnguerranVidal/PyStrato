######################## IMPORTS ########################
import json
import os
import csv
from typing import Optional

# ------------------- PyQt Modules -------------------- #
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

# --------------------- Sources ----------------------- #
from sources.databases.balloondata import BalloonPackageDatabase, createNewDatabase
from sources.databases.units import UnitsEditorWidget
from sources.databases.constants import ConstantsWidget
from sources.databases.configurations import ConfigsEditorWidget
from sources.databases.telemetries import TelemetryEditorWidget
from sources.databases.telecommands import TelecommandsWidget


######################## CLASSES ########################
class DatabaseEditor(QTabWidget):
    tabChanged = pyqtSignal()
    editorChanged = pyqtSignal()

    def __init__(self, database: BalloonPackageDatabase):
        super(QTabWidget, self).__init__()
        self.database = database

        self.unitsTab = UnitsEditorWidget(database=self.database)
        self.constantsTab = ConstantsWidget(database=self.database)
        self.configsTab = ConfigsEditorWidget(database=self.database)
        self.dataTypesTab = QWidget()
        self.telemetriesTab = TelemetryEditorWidget(database=self.database)
        self.telecommandsTab = TelecommandsWidget(database=self.database)

        self.unitsTab.change.connect(self.editorChanged.emit())
        self.configsTab.change.connect(self.editorChanged.emit())
        self.telemetriesTab.change.connect(self.editorChanged.emit())

        self.addTab(self.unitsTab, 'UNITS')
        self.addTab(self.constantsTab, 'CONSTANTS')
        self.addTab(self.configsTab, 'CONFIG')
        self.addTab(self.dataTypesTab, 'DATATYPES')
        self.addTab(self.telemetriesTab, 'TELEMETRIES')
        self.addTab(self.telecommandsTab, 'TELECOMMANDS')

        self.currentChanged.connect(self.editorChanged)
        self.setTabPosition(QTabWidget.East)
        # self.setTabShape(QTabWidget.Triangular)

    def editorTabChanged(self, index):
        self.tabChanged.emit()
        if index == 2:
            self.configsTab.validateConfigurations()


class DatabaseTabWidget(QTabWidget):
    tabChanged = pyqtSignal()
    databaseChanged = pyqtSignal()

    def __init__(self, path):
        super(QWidget, self).__init__()
        self.hide()
        self.currentDirectory = path
        self.formatPath = os.path.join(self.currentDirectory, "formats")
        self.databases = {}

    def newFormat(self, name):
        newDatabasePath = os.path.join(self.formatPath, name)
        os.makedirs(newDatabasePath)
        createNewDatabase(newDatabasePath)
        database = BalloonPackageDatabase(newDatabasePath)
        self.databases[name] = database
        editor = DatabaseEditor(self.databases[name])
        editor.tabChanged.connect(self.tabChanged.emit)
        editor.editorChanged.connect(self.databaseChanged.emit)
        self.addTab(editor, name)
        self.tabChanged.emit()

    def openFormat(self, path):
        database = BalloonPackageDatabase(path)
        name = os.path.basename(path)
        # Creating Tab in Editing Tabs
        self.databases[name] = database
        editor = DatabaseEditor(self.databases[name])
        editor.tabChanged.connect(self.tabChanged.emit)
        editor.editorChanged.connect(self.databaseChanged.emit)
        self.addTab(editor, name)
        self.tabChanged.emit()

    def saveFormat(self, path=None):
        pass

    def saveAllFormats(self):
        pass

    @staticmethod
    def _saveDatabase(database: BalloonPackageDatabase, path: Optional[str] = None):
        pass

    def _closeDatabase(self, index: int):
        pass

    def closeFormat(self):
        pass

    def closeAllFormat(self):
        pass



