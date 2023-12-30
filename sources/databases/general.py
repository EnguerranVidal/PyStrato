######################## IMPORTS ########################
import os
import subprocess
from typing import Dict

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
from sources.common.utilities.FileHandling import loadSettings


######################## CLASSES ########################
class DatabaseEditor(QTabWidget):
    def __init__(self, database: BalloonPackageDatabase, databaseName: str):
        super(QTabWidget, self).__init__()
        self.database = database
        self.databaseName = databaseName

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
        self.parserPath = os.path.join(self.currentDirectory, "parsers")
        self.databases = {}  # type: Dict[str, BalloonPackageDatabase]

    def newParser(self, name):
        newDatabasePath = os.path.join(self.parserPath, name)
        os.makedirs(newDatabasePath)
        createNewDatabase(newDatabasePath)
        database = BalloonPackageDatabase(newDatabasePath)
        self.databases[name] = database
        # EDITOR CREATION AND SIGNALS' CONNECTIONS
        editor = DatabaseEditor(self.databases[name], name)
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
        editor = DatabaseEditor(self.databases[name], name)
        editor.unitsTab.change.connect(self.databaseChanged.emit)
        editor.constantsTab.change.connect(self.databaseChanged.emit)
        editor.configsTab.change.connect(self.databaseChanged.emit)
        editor.dataTypesTab.change.connect(self.databaseChanged.emit)
        editor.telemetriesTab.change.connect(self.databaseChanged.emit)
        editor.telecommandsTab.change.connect(self.databaseChanged.emit)
        editor.currentChanged.connect(self.tabChanged.emit)
        self.addTab(editor, name)
        self.tabChanged.emit()

    def saveParser(self, databaseName: str = None, path=None):
        if databaseName is None:
            databaseName = self.tabText(self.currentIndex())
        if path is None:
            path = self.databases[databaseName].path
        self.databases[databaseName].save(path)
        if path != self.databases[databaseName].path:
            self.databases[databaseName].setPath(path)
        self.tabChanged.emit()

    def saveAllParsers(self):
        databaseNames = list(self.databases.keys())
        for databaseName in databaseNames:
            self.saveParser(databaseName)

    def closeParser(self, databaseName: str = None):
        if databaseName is None:
            databaseName = self.tabText(self.currentIndex())
        databasePath = self.databases[databaseName].path
        savedDatabase = BalloonPackageDatabase(databasePath)
        if savedDatabase != self.databases[databaseName]:
            unsavedMessage = f'There are unsaved changes in {databaseName}. What do you want to do?'
            buttons = QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel
            reply = QMessageBox.question(self, 'Unsaved Changes', unsavedMessage, buttons, QMessageBox.Save)
            if reply == QMessageBox.Save:
                self.saveParser(databaseName)
            elif reply == QMessageBox.Cancel:
                return
        tabIndex = list(self.databases.keys()).index(databaseName)
        self.removeTab(tabIndex)
        self.databases.pop(databaseName)
        self.tabChanged.emit()

    def closeAllParser(self):
        if self.unsavedChanges:
            unsavedMessage = "There are unsaved changes in the editor. What do you want to do?"
            buttons = QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel
            reply = QMessageBox.question(self, 'Unsaved Changes', unsavedMessage, buttons, QMessageBox.Save)
            if reply == QMessageBox.Save:
                self.saveAllParserTab()
            elif reply == QMessageBox.Cancel:
                return
        else:
            for i in range(self.count()):
                self.removeTab(i)
            self.databases = {}  # type: Dict[str, BalloonPackageDatabase]

    def generateParserCode(self):
        if self.count() >= 1:
            currentParser = self.currentWidget().databaseName
            dialog = CodeGenerationDialog(self.currentDirectory, currentParser, self.databases)
            dialog.saveParser.connect(self.saveParser)
            dialog.exec_()


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


class CodeGenerationDialog(QDialog):
    saveParser = pyqtSignal(str)

    def __init__(self, path, currentParser, openedParsers):
        super().__init__()
        self.setModal(True)
        self.setWindowTitle('Code Generation')
        self.setWindowIcon(QIcon('sources/icons/PyStrato.png'))
        self.databases = openedParsers
        self.currentDir = path
        self.parserPath = os.path.join(self.currentDir, "parsers")
        self.settings = loadSettings('settings')

        # WIDGETS & BUTTONS
        self.parsersComboBox = QComboBox(self)
        self.parsersComboBox.addItems(list(self.databases.keys()))
        self.parsersComboBox.setCurrentText(currentParser)
        self.sourceEdit = QLineEdit(self)
        self.sourceBrowseButton = QPushButton('', self)
        self.sourceBrowseButton.clicked.connect(lambda _: self.browseDirectory(0))
        self.includeEdit = QLineEdit(self)
        self.includeBrowseButton = QPushButton('', self)
        self.includeBrowseButton.clicked.connect(lambda _: self.browseDirectory(1))

        generateButton = QPushButton('Generate', self)
        generateButton.clicked.connect(self.generateCode)
        cancelButton = QPushButton('Cancel', self)
        cancelButton.clicked.connect(self.reject)

        # MAIN LAYOUT
        mainLayout = QGridLayout()
        buttonLayout = QHBoxLayout()
        buttonLayout.addWidget(generateButton)
        buttonLayout.addWidget(cancelButton)
        mainLayout.addWidget(QLabel('Database'), 0, 0, 1, 1)
        mainLayout.addWidget(QLabel('Source'), 1, 0, 1, 1)
        mainLayout.addWidget(QLabel('Include'), 2, 0, 1, 1)
        mainLayout.addWidget(self.parsersComboBox, 0, 1, 1, 1)
        mainLayout.addWidget(self.sourceEdit, 1, 1, 1, 1)
        mainLayout.addWidget(self.sourceBrowseButton, 1, 2, 1, 1)
        mainLayout.addWidget(self.includeEdit, 2, 1, 1, 1)
        mainLayout.addWidget(self.includeBrowseButton, 2, 2, 1, 1)
        mainLayout.addLayout(buttonLayout, 3, 0, 1, 3)
        self.setLayout(mainLayout)

    def browseDirectory(self, index):
        options = QFileDialog.Options()
        options |= QFileDialog.ShowDirsOnly
        directory = QFileDialog.getExistingDirectory(self, "Select Directory", options=options)
        if directory and index == 0:
            self.sourceEdit.setText(directory)
            if self.includeEdit.text() == '':
                self.includeEdit.setText(directory)
        if directory and index == 1:
            self.includeEdit.setText(directory)
            if self.sourceEdit.text() == '':
                self.sourceEdit.setText(directory)

    def generateCode(self):
        databaseName = self.parsersComboBox.currentText()
        databasePath = self.databases[databaseName].path
        savedDatabase = BalloonPackageDatabase(databasePath)
        if savedDatabase != self.databases[databaseName]:
            replyMessage = 'Save changes before generating?'
            reply = QMessageBox.question(self, 'Save Confirmation', replyMessage, QMessageBox.Yes | QMessageBox.Cancel)
            if reply == QMessageBox.Cancel:
                return
        sourceDirectory = self.sourceEdit.text()
        includeDirectory = self.includeEdit.text()
        ecomUpdateCommand = f'ecomUpdate --dataDir {databasePath} {sourceDirectory} {includeDirectory}'

        try:
            subprocess.run(ecomUpdateCommand, shell=True, check=True)
            QMessageBox.information(self, 'Success', 'Code generation successful!')
            self.accept()
        except subprocess.CalledProcessError as e:
            QMessageBox.critical(self, 'Error', f'Error during code generation: {e}')
