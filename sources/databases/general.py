######################## IMPORTS ########################
import os
import subprocess
from collections import OrderedDict

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
        self.formatPath = os.path.join(self.currentDirectory, "formats")
        self.databases = OrderedDict()

    def newParser(self, name):
        newDatabasePath = os.path.join(self.formatPath, name)
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

    def saveParser(self, path=None):
        pass

    def saveAllParsers(self):
        pass

    def closeParser(self):
        pass

    def closeAllParser(self):
        pass

    def generateParserCode(self):
        if self.count() >= 1:
            currentParser = self.currentWidget().databaseName
            dialog = CodeGenerationDialog(self.currentDirectory, currentParser)
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

    def __init__(self, path, currentParser=None, openedParsers=None):
        super().__init__()
        self.setModal(True)
        self.setWindowTitle('Code Generation')
        self.setWindowIcon(QIcon('sources/icons/PyStrato.png'))
        self.currentDir = path
        self.parserPath = os.path.join(self.currentDir, "parsers")

        # WIDGETS & BUTTONS
        self.parsersComboBox = QComboBox(self)
        path = self.parserPath
        availableFormats = [directory for directory in os.listdir(path) if os.path.isdir(os.path.join(path, directory))]
        self.parsersComboBox.addItems(availableFormats)
        if currentParser is not None:
            self.parsersComboBox.setCurrentText(currentParser[0])
        self.includeEdit = QLineEdit(self)
        self.includeBrowseButton = QPushButton('', self)
        self.includeBrowseButton.clicked.connect(lambda _: self.browseDirectory(0))
        self.sourceEdit = QLineEdit(self)
        self.sourceBrowseButton = QPushButton('', self)
        self.sourceBrowseButton.clicked.connect(lambda _: self.browseDirectory(1))
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
        mainLayout.addWidget(QLabel('Include'), 1, 0, 1, 1)
        mainLayout.addWidget(QLabel('Source'), 2, 0, 1, 1)
        mainLayout.addWidget(self.parsersComboBox, 0, 1, 1, 1)
        mainLayout.addWidget(self.includeEdit, 1, 1, 1, 1)
        mainLayout.addWidget(self.includeBrowseButton, 1, 2, 1, 1)
        mainLayout.addWidget(self.sourceEdit, 2, 1, 1, 1)
        mainLayout.addWidget(self.sourceBrowseButton, 2, 2, 1, 1)
        mainLayout.addLayout(buttonLayout, 3, 0, 1, 3)
        self.setLayout(mainLayout)

    def browseDirectory(self, index):
        options = QFileDialog.Options()
        options |= QFileDialog.ShowDirsOnly
        directory = QFileDialog.getExistingDirectory(self, "Select Directory", options=options)
        if directory and index == 0:
            self.includeEdit.setText(directory)
        if directory and index == 1:
            self.sourceEdit.setText(directory)

    def generateCode(self):
        databasePath = os.path.join(self.parserPath, self.parsersComboBox.currentText())
        if not os.path.exists(databasePath):
            pass
        sourceDirectory = self.sourceEdit.text()
        includeDirectory = self.includeEdit.text()
        ecomUpdateCommand = f'ecomUpdate --dataDir {databasePath} {sourceDirectory} {includeDirectory}'

        try:
            subprocess.run(ecomUpdateCommand, shell=True, check=True)
            QMessageBox.information(self, 'Success', 'Code generation successful!')
            self.accept()
        except subprocess.CalledProcessError as e:
            QMessageBox.critical(self, 'Error', f'Error during code generation: {e}')
