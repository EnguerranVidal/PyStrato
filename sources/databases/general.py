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
from sources.databases.constants import ConstantEditorWidget
from sources.databases.configurations import ConfigsEditorWidget
from sources.databases.sharedtypes import SharedTypesEditorWidget
from sources.databases.telemetries import TelemetryEditorWidget
from sources.databases.telecommands import TelecommandEditorWidget


######################## CLASSES ########################
class DatabaseEditor(QTabWidget):
    def __init__(self, database: BalloonPackageDatabase):
        super(QTabWidget, self).__init__()
        self.database = database

        self.unitsTab = UnitsEditorWidget(database=self.database)
        self.constantsTab = ConstantEditorWidget(database=self.database)
        self.configsTab = ConfigsEditorWidget(database=self.database)
        self.dataTypesTab = SharedTypesEditorWidget(database=self.database)
        self.telemetriesTab = TelemetryEditorWidget(database=self.database)
        self.telecommandsTab = TelecommandEditorWidget(database=self.database)

        self.addTab(self.unitsTab, 'UNITS')
        self.addTab(self.constantsTab, 'CONSTANTS')
        self.addTab(self.configsTab, 'CONFIG')
        self.addTab(self.dataTypesTab, 'DATATYPES')
        self.addTab(self.telemetriesTab, 'TELEMETRIES')
        self.addTab(self.telecommandsTab, 'TELECOMMANDS')

        self.currentChanged.connect(self.editorTabChanged)
        self.setTabPosition(QTabWidget.East)

    def editorTabChanged(self, index):
        if index == 2:
            self.configsTab.validateConfigurations()


class DatabaseTabWidget(QTabWidget):
    tabChanged = pyqtSignal()
    databaseChanged = pyqtSignal()

    def __init__(self, path):
        super(QWidget, self).__init__()
        self.hide()
        self.unsavedChanges = True
        self.currentDirectory = path
        self.formatPath = os.path.join(self.currentDirectory, "formats")
        self.databases = {}

    def newParser(self, name):
        newDatabasePath = os.path.join(self.formatPath, name)
        os.makedirs(newDatabasePath)
        createNewDatabase(newDatabasePath)
        database = BalloonPackageDatabase(newDatabasePath)
        self.databases[name] = database
        # EDITOR CREATION AND SIGNALS' CONNECTIONS
        editor = DatabaseEditor(self.databases[name])
        editor.unitsTab.change.connect(self.databaseChanged.emit)
        editor.constantsTab.change.connect(self.databaseChanged.emit)
        editor.configsTab.change.connect(self.databaseChanged.emit)
        editor.dataTypesTab.change.connect(self.databaseChanged.emit)
        editor.telemetriesTab.change.connect(self.databaseChanged.emit)
        editor.telecommandsTab.change.connect(self.databaseChanged.emit)
        editor.currentChanged.connect(self.tabChanged.emit)
        self.addTab(editor, name)
        self.tabChanged.emit()

    def openParser(self, path):
        database = BalloonPackageDatabase(path)
        name = os.path.basename(path)
        self.databases[name] = database
        # EDITOR CREATION AND SIGNALS' CONNECTIONS
        editor = DatabaseEditor(self.databases[name])
        editor.unitsTab.change.connect(self.databaseChanged.emit)
        editor.constantsTab.change.connect(self.databaseChanged.emit)
        editor.configsTab.change.connect(self.databaseChanged.emit)
        editor.dataTypesTab.change.connect(self.databaseChanged.emit)
        editor.telemetriesTab.change.connect(self.databaseChanged.emit)
        editor.telecommandsTab.change.connect(self.databaseChanged.emit)
        editor.currentChanged.connect(self.tabChanged.emit)
        self.addTab(editor, name)
        self.tabChanged.emit()

    def saveParser(self, path=None):
        pass

    def saveAllParsers(self):
        pass

    @staticmethod
    def _saveDatabase(database: BalloonPackageDatabase, path: Optional[str] = None):
        pass

    def _closeDatabase(self, index: int):
        pass

    def closeParser(self):
        pass

    def closeAllParser(self):
        pass


class NewDatabaseWindow(QDialog):
    def __init__(self, parent=None, databases=[]):
        super().__init__(parent)
        self.databases = databases
        self.setWindowTitle('Create New Package')
        self.setWindowIcon(QIcon('sources/icons/PyStrato.png'))
        self.setModal(True)
        self.dataChanged = False
        self.saveChanged = False
        self.resize(400, 100)
        # NAME ENTRY & BUTTONS
        self.nameLabel = QLabel('Database Name :')
        self.nameLineEdit = QLineEdit()
        self.nameLineEdit.textChanged.connect(self.updateOkButtonState)
        self.okButton = QPushButton('OK')
        self.okButton.setEnabled(False)
        self.cancelButton = QPushButton('Cancel')
        self.okButton.clicked.connect(self.accept)
        self.cancelButton.clicked.connect(self.reject)
        # LAYOUT
        buttonLayout = QHBoxLayout()
        buttonLayout.addWidget(self.okButton)
        buttonLayout.addWidget(self.cancelButton)
        layout = QVBoxLayout(self)
        layout.addWidget(self.nameLabel)
        layout.addWidget(self.nameLineEdit)
        layout.addLayout(buttonLayout)

    def updateOkButtonState(self):
        name = self.nameLineEdit.text()
        validNewDatabaseName = bool(name) and name not in self.databases
        self.okButton.setEnabled(validNewDatabaseName)

