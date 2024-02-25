######################## IMPORTS ########################
import json
import os
import re
import time

import numpy as np
from ecom.datatypes import TypeInfo

# ------------------- PyQt Modules -------------------- #
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtCore import Qt
from PyQt5.QtGui import *

# --------------------- Sources ----------------------- #
from sources.common.utilities.fileSystem import loadSettings, saveSettings, nameGiving, getModificationDate
from sources.databases.balloondata import BalloonPackageDatabase


######################## CLASSES ########################
class ContentStorage:
    def __init__(self, path):
        self.settings = loadSettings('settings')
        self.currentDir = path
        self.storage = {}

    def fill(self):
        self.settings = loadSettings('settings')
        formatFiles = self.settings['FORMAT_FILES']
        for formatFile in formatFiles:
            path = os.path.join(self.currentDir, 'parsers')
            if os.path.isdir(path):
                formatPath = os.path.join(path, formatFile)
                name, database = os.path.basename(formatPath), BalloonPackageDatabase(formatPath)
                self.storage[name] = {
                    telemetryType.id.name: {
                        dataPoint.name: []
                        for dataPoint in telemetryType.data
                    }
                    for telemetryType in database.telemetryTypes
                }

    def __len__(self):
        return len(list(self.storage.keys()))

    def append(self, content):
        packageStorage = self.storage[content['parser']][content['type']]
        for key, value in content['data'].items():
            packageStorage[key].append(value)

    def retrieveStoredContent(self, keys):
        currentLevel = self.storage
        try:
            for key in keys:
                currentLevel = currentLevel[key]
            return currentLevel
        except (KeyError, TypeError):
            return None


class TypeSelector(QDialog):
    def __init__(self, database, typeName, haveDataTypes=False, telemetryType=None, dataType=None):
        super().__init__()
        self.selectedType = None
        self.setWindowTitle('Select a Type')
        self.setModal(True)
        self.typeName, self.database = typeName, database
        self.haveDataTypes, self.telemetryType, self.arraySize = haveDataTypes, telemetryType, None
        self.baseTypesValues = [baseType.value for baseType in TypeInfo.BaseType]
        self.baseTypeNames = [baseType.name for baseType in TypeInfo.BaseType]
        self.specialTypes = ['TelecommandMessageHeader', 'TelemetryMessageHeader']

        # ARRAY SIZE ---------------------------------------------------
        self.arraySizeWidget = QWidget()
        self.arraySizeLabel = QLabel('ARRAY SIZE')
        # Array Verification
        matchingArrayFormat = re.search(r'(.*?)\[(.*?)\]', self.typeName)
        if matchingArrayFormat:
            newTypeName, self.arraySize = matchingArrayFormat.group(1), matchingArrayFormat.group(2)
            self.typeName = newTypeName.upper() if newTypeName in self.baseTypesValues else newTypeName

        # Array Widget & Switch
        self.arrayCheckBox = QCheckBox("Array Type", self)
        self.arraySizeFrame = QFrame()
        self.arraySizeFrame.setFrameShape(QFrame.Box)
        self.arraySizeFrame.setLineWidth(2)
        self.arraySizeSwitch = QComboBox(self)
        self.arraySizeSwitch.addItem("Integer")
        self.arraySizeSwitch.addItem("Constant")
        if self.telemetryType is not None:
            self.arraySizeSwitch.addItem("Telemetry Argument")
        self.arraySizeSwitch.currentIndexChanged.connect(self.switchArraySizeSelection)
        # Integer & Constants
        self.arrayIntegerLineEdit = QLineEdit(self)
        self.arrayIntegerLineEdit.setValidator(QIntValidator())
        self.arrayConstantListWidget = QListWidget(self)
        self.arrayArgumentsListWidget = QListWidget(self)
        for constant in list(self.database.constants.keys()):
            self.arrayConstantListWidget.addItem(constant)
        self.telemetryArguments = []
        if self.telemetryType is not None:
            for dataPoint in self.telemetryType.data:
                argumentTypeName = self.database.getTypeName(dataPoint.type)
                integer = argumentTypeName.startswith('int') or argumentTypeName.startswith('uint')
                if integer and not self.isAnArray(argumentTypeName):
                    self.telemetryArguments.append(dataPoint.name)
                    self.arrayArgumentsListWidget.addItem(dataPoint.name)
            if self.arrayArgumentsListWidget.count() == 0:
                self.arraySizeSwitch.removeItem(2)
        self.initializeArraySizeType()
        self.arrayCheckBox.stateChanged.connect(self.toggleArraySizeWidget)
        self.arrayIntegerLineEdit.textChanged.connect(self.arraySizeIntegerChanged)
        self.arrayConstantListWidget.itemSelectionChanged.connect(self.arraySizeSelectionChanged)
        self.arrayArgumentsListWidget.itemSelectionChanged.connect(self.arraySizeSelectionChanged)

        # BASE-TYPES/UNITS SELECTION
        self.selectionSwitch = QComboBox(self)
        self.selectionSwitch.addItem("Base Types")
        self.selectionSwitch.addItem("Units")
        if self.haveDataTypes:
            self.sharedDataTypes = self.database.dataTypes
            self.selectionSwitch.addItem("Shared Types")
        self.selectionSwitch.currentIndexChanged.connect(self.switchTypeSelection)

        # BASE-TYPES
        self.baseTypesWidget = QComboBox(self)
        self.baseTypesWidget.addItems(self.baseTypeNames)
        self.baseTypesWidget.currentIndexChanged.connect(self.baseTypeChanged)

        # UNITS LIST
        self.unitsList = QListWidget(self)
        self.unitInfoLabel = QLabel(self)
        for unitName in self.database.units.keys():
            self.unitsList.addItem(unitName)
        self.unitsList.setSelectionMode(QListWidget.SingleSelection)
        self.unitsList.currentItemChanged.connect(self.displayUnitInfo)

        # SHARED TYPES
        self.sharedTypesList = QListWidget(self)
        self.sharedTypesInfoLabel = QLabel(self)
        if self.haveDataTypes:
            for sharedType in self.database.getSharedDataTypes():
                if sharedType not in self.specialTypes and sharedType != dataType:
                    self.sharedTypesList.addItem(sharedType)
        self.sharedTypesList.setSelectionMode(QListWidget.SingleSelection)
        self.sharedTypesList.currentItemChanged.connect(self.displaySharedDataTypeInfo)

        # BUTTONS
        self.okButton = QPushButton('OK')
        self.cancelButton = QPushButton('Cancel')
        self.okButton.clicked.connect(self.accept)
        self.cancelButton.clicked.connect(self.reject)

        # TYPE LABELS
        self.previousTypeLabel = QLabel(f'Previous Type : {typeName}')
        self.selectedTypeLabel = QLabel(f'Selected Type : {typeName}')

        # MAIN LAYOUT
        layout = QVBoxLayout()
        layout.addWidget(self.previousTypeLabel)
        layout.addWidget(self.selectedTypeLabel)
        layout.addWidget(self.selectionSwitch)
        layout.addWidget(self.baseTypesWidget)
        layout.addWidget(self.unitsList)
        layout.addWidget(self.unitInfoLabel)
        layout.addWidget(self.sharedTypesList)
        layout.addWidget(self.sharedTypesInfoLabel)
        layout.addWidget(self.arrayCheckBox)
        layout.setAlignment(Qt.AlignTop)
        buttonLayout = QHBoxLayout()
        buttonLayout.addWidget(self.okButton)
        buttonLayout.addWidget(self.cancelButton)
        layout.addLayout(buttonLayout)

        self.arraySizeFrame.setLayout(QVBoxLayout())
        self.arraySizeFrame.layout().addWidget(self.arraySizeSwitch)
        self.arraySizeFrame.layout().addWidget(self.arrayIntegerLineEdit)
        self.arraySizeFrame.layout().addWidget(self.arrayConstantListWidget)
        self.arraySizeFrame.layout().addWidget(self.arrayArgumentsListWidget)
        arraySizeLayout = QVBoxLayout()
        arraySizeLayout.addWidget(self.arraySizeLabel)
        arraySizeLayout.addWidget(self.arraySizeFrame)
        self.arraySizeWidget.setLayout(arraySizeLayout)

        mainLayout = QHBoxLayout()
        mainLayout.addLayout(layout)
        mainLayout.addWidget(self.arraySizeWidget)
        self.setLayout(mainLayout)

        if self.typeName in self.baseTypeNames:
            self.switchTypeSelection(0)
            baseTypeIndex = self.baseTypeNames.index(self.typeName)
            self.baseTypesWidget.setCurrentIndex(baseTypeIndex)
        elif self.typeName in self.database.units:
            self.switchTypeSelection(1)
            unitIndex = list(self.database.units.keys()).index(self.typeName)
            unitItem = self.unitsList.item(unitIndex)
            self.unitsList.setCurrentItem(unitItem)
        elif self.haveDataTypes and self.typeName in self.database.getSharedDataTypes():
            self.switchTypeSelection(2)
            typeIndex = self.database.getSharedDataTypes().index(self.typeName)
            typeItem = self.sharedTypesList.item(typeIndex)
            self.sharedTypesList.setCurrentItem(typeItem)

    def initializeArraySizeType(self, typeName=None):
        typeName = typeName if typeName is not None else self.typeName
        if self.arraySize is not None:
            self.arrayCheckBox.setChecked(True)
            self.arraySizeWidget.setVisible(True)
            if self.arraySize.isdigit():  # INTEGER SIZE
                self.arrayIntegerLineEdit.setText(self.arraySize)
                self.switchArraySizeSelection(0)
                self.selectedType = (typeName, True, self.arraySize, False)
            elif self.telemetryType is not None and self.arraySize.startswith('.'):
                argumentIndex = self.telemetryArguments.index(self.arraySize[1:])
                argumentItem = self.arrayArgumentsListWidget.item(argumentIndex)
                self.arrayArgumentsListWidget.setCurrentItem(argumentItem)
                self.switchArraySizeSelection(2)
                self.selectedType = (typeName, True, self.arraySize[1:], True)
            else:
                constantIndex = list(self.database.constants.keys()).index(self.arraySize)
                constantItem = self.arrayConstantListWidget.item(constantIndex)
                self.arrayConstantListWidget.setCurrentItem(constantItem)
                self.switchArraySizeSelection(1)
                self.selectedType = (typeName, True, self.arraySize, False)
        else:
            self.arraySizeWidget.setVisible(False)
            self.arrayCheckBox.setChecked(False)
            self.switchArraySizeSelection(0)
            self.selectedType = (typeName, False, None, False)

    def toggleArraySizeWidget(self, state):
        isArray = state == Qt.Checked
        if self.arraySize is None:
            self.arraySize = '1'
            self.arrayIntegerLineEdit.setText(self.arraySize)
            self.changeSelectedTypeLabel(self.selectedType[0], isArray, self.arraySize, self.selectedType[3])
        else:
            self.changeSelectedTypeLabel(self.selectedType[0], isArray, self.selectedType[2], self.selectedType[3])
        self.arraySizeWidget.setVisible(isArray)
        self.adjustSize()

    def switchArraySizeSelection(self, index):
        self.arraySizeSwitch.setCurrentIndex(index)
        self.arrayIntegerLineEdit.setVisible(index == 0)
        self.arrayConstantListWidget.setVisible(index == 1)
        self.arrayArgumentsListWidget.setVisible(index == 2)
        self.arrayConstantListWidget.clearSelection()
        self.arrayArgumentsListWidget.clearSelection()
        self.adjustSize()
        self.arraySizeFrame.adjustSize()

    def switchTypeSelection(self, index):
        self.selectionSwitch.setCurrentIndex(index)
        self.baseTypesWidget.setVisible(index == 0)
        self.unitsList.setVisible(index == 1)
        self.unitInfoLabel.setVisible(index == 1)
        self.sharedTypesList.setVisible(index == 2)
        self.sharedTypesInfoLabel.setVisible(index == 2)
        self.adjustSize()

    def displayUnitInfo(self, current, previous):
        if current:
            unitName = current.text()
            unitInfo = self.database.units[unitName][0]
            unitType = unitInfo.baseTypeName
            description = unitInfo.description
            self.unitInfoLabel.setText(f"Unit Type: {unitType}\nDescription: {description}")
            self.changeSelectedTypeLabel(unitName, self.selectedType[1], self.selectedType[2], self.selectedType[3])
        else:
            self.unitInfoLabel.clear()

    def displaySharedDataTypeInfo(self, current, previous):
        if current:
            sharedTypeName = current.text()
            description = ''
            if self.sharedDataTypes[sharedTypeName].description:
                description = self.sharedDataTypes[sharedTypeName].description
            self.sharedTypesInfoLabel.setText(f"{sharedTypeName}\nDescription: {description}")
            self.changeSelectedTypeLabel(sharedTypeName, self.selectedType[1], self.selectedType[2], self.selectedType[3])
        else:
            self.sharedTypesInfoLabel.clear()

    def arraySizeSelectionChanged(self):
        senderWidget: QListWidget = self.sender()
        currentItem = senderWidget.currentItem()
        if currentItem:
            arraySize = currentItem.text()
            isTelemetry = arraySize in self.telemetryArguments
            self.changeSelectedTypeLabel(self.selectedType[0], self.selectedType[1], arraySize, isTelemetry)

    def arraySizeIntegerChanged(self):
        senderWidget: QLineEdit = self.sender()
        self.changeSelectedTypeLabel(self.selectedType[0], self.selectedType[1], senderWidget.text(), False)

    def baseTypeChanged(self, index):
        self.changeSelectedTypeLabel(self.baseTypeNames[index], self.selectedType[1], self.selectedType[2],
                                     self.selectedType[3])

    def changeSelectedTypeLabel(self, typeName, isArray, arraySize, isTelemetry):
        typeName = typeName.upper() if typeName in self.baseTypesValues else typeName
        typeValue = typeName.lower() if typeName in self.baseTypeNames else typeName
        self.selectedType = (typeValue, isArray, arraySize, isTelemetry)
        if not isArray:
            self.selectedTypeLabel.setText(f'Selected Type : {typeName}')
        elif isTelemetry:
            self.selectedTypeLabel.setText(f'Selected Type : {typeName}[.{arraySize}]')
        else:
            self.selectedTypeLabel.setText(f'Selected Type : {typeName}[{arraySize}]')

    @staticmethod
    def isAnArray(typeName):
        return re.search(r'(.*?)\[(.*?)\]', typeName)


class ArgumentSelector(QDialog):
    def __init__(self, path, parent=None, typeFilter=(int, float), argument=None):
        super().__init__(parent)
        self.currentDir = path
        self.setModal(True)
        self.settings = loadSettings('settings')
        self.selectedArgument, self.argumentUnit, self.databases, self.typeFilter = argument, None, None, typeFilter
        self.setWindowTitle('Argument Selection')
        self.formatPath = os.path.join(self.currentDir, 'parsers')

        # DISPLAY & PARSER SELECTION
        self.selectionNameLabel = QLabel()
        self.parserComboBox = QComboBox()
        self.fillComboBox()
        self.parserComboBox.currentIndexChanged.connect(self.changeComboBox)
        # TELEMETRY TYPE SELECTION
        themeFolder = 'dark-theme' if self.settings['DARK_THEME'] else 'light-theme'
        self.telemetryTypeLabel = QLabel("Label")
        self.telemetryTypeLabel.setAlignment(Qt.AlignCenter)
        self.previousButton = SquareIconButton(f'sources/icons/{themeFolder}/icons8-back-96.png', flat=True)
        self.previousButton.clicked.connect(self.previousTelemetry)
        self.nextButton = SquareIconButton(f'sources/icons/{themeFolder}/icons8-forward-96.png', flat=True)
        self.nextButton.clicked.connect(self.nextTelemetry)
        secondRowLayout = QHBoxLayout()
        secondRowLayout.addWidget(self.previousButton)
        secondRowLayout.addWidget(self.telemetryTypeLabel)
        secondRowLayout.addWidget(self.nextButton)
        # TELEMETRY ARGUMENTS SELECTION
        self.selectionWidget = QStackedWidget()
        self.createTreeStructures()
        self.setArgument()

        # BOTTOM BUTTONS
        bottomRowLayout = QHBoxLayout()
        self.selectButton = QPushButton("Select")
        self.cancelButton = QPushButton("Cancel")
        self.selectButton.clicked.connect(self.accept)
        self.cancelButton.clicked.connect(self.reject)
        bottomRowLayout.addWidget(self.selectButton)
        bottomRowLayout.addWidget(self.cancelButton)

        # MAIN LAYOUT
        mainLayout = QVBoxLayout()
        mainLayout.addWidget(self.selectionNameLabel)
        mainLayout.addWidget(self.parserComboBox)
        mainLayout.addLayout(secondRowLayout)
        mainLayout.addWidget(self.selectionWidget)
        mainLayout.addLayout(bottomRowLayout)
        self.setLayout(mainLayout)

    def setArgument(self):
        if self.selectedArgument is not None:
            argument = self.selectedArgument.split('/')
            database, telemetry, argument = argument[0], argument[1], argument[2:]
            if database in list(self.databases.keys()):
                telemetries = {telemetry.id.name: telemetry.data for telemetry in database.telemetryTypes}
                self.selectionWidget.setCurrentIndex(list(self.databases.keys()).index(database))
                self.selectionWidget.currentWidget().setCurrentIndex(list(telemetries.keys()).index(telemetry))
            self.selectionNameLabel.setText(self.selectedArgument)
        else:
            database = self.databases[list(self.databases.keys())[0]]
            self.selectionWidget.setCurrentIndex(0)
            self.selectionWidget.currentWidget().setCurrentIndex(0)
            telemetryNames = [telemetry.id.name for telemetry in database.telemetryTypes]
            self.telemetryTypeLabel.setText(telemetryNames[0])
            self.selectionNameLabel.setText('None')

    def createTreeStructures(self):

        def addGrandChildren(treeItem, selectedDict):
            for childName, childValue in selectedDict.items():
                if isinstance(childValue, dict):
                    child = QTreeWidgetItem(treeItem, [childName])
                    treeItem.addChild(child)
                    child.setFlags(child.flags() & Qt.ItemIsEnabled)
                    addGrandChildren(child, childValue)
                elif isinstance(childValue, bool):
                    child = QTreeWidgetItem(treeItem, [childName])
                    treeItem.addChild(child)
                    if childValue:
                        child.setFlags(child.flags() & Qt.ItemIsEnabled)
                    else:
                        child.setFlags(child.flags() & ~Qt.ItemIsEnabled)
            return treeItem

        for databaseName, database in self.databases.items():
            databaseStackedWidget = QStackedWidget()
            for telemetry in database.telemetryTypes:
                treeWidget = QTreeWidget()
                treeWidget.setHeaderLabels([])
                treeWidget.setHeaderHidden(True)
                treeWidget.setColumnCount(1)
                treeWidget.itemSelectionChanged.connect(self.selectionMade)
                telemetryName = telemetry.id.name
                selectedTypes, _ = database.nestedPythonTypes(telemetryName, searchedType=self.typeFilter)
                for name, value in selectedTypes.items():
                    if isinstance(value, dict):
                        item = QTreeWidgetItem(treeWidget, [name])
                        treeWidget.addTopLevelItem(item)
                        item.setFlags(item.flags() & Qt.ItemIsEnabled)
                        addGrandChildren(item, value)
                    elif isinstance(value, bool):
                        item = QTreeWidgetItem(treeWidget, [name])
                        treeWidget.addTopLevelItem(item)
                        if value:
                            item.setFlags(item.flags() & Qt.ItemIsEnabled)
                        else:
                            item.setFlags(item.flags() & ~Qt.ItemIsEnabled)
                databaseStackedWidget.addWidget(treeWidget)
            databaseStackedWidget.setCurrentIndex(0)
            self.selectionWidget.addWidget(databaseStackedWidget)

    def fillComboBox(self):
        files = self.settings['FORMAT_FILES']
        if len(files) == 1 and len(files[0]) == 0:
            files = []
        self.databases = {}
        for file in files:
            path = os.path.join(self.formatPath, file)
            name, database = os.path.basename(path), BalloonPackageDatabase(path)
            self.databases[name] = database
        self.parserComboBox.clear()
        names = list(self.databases.keys())
        if len(names) != 0:
            for name in names:
                self.parserComboBox.addItem(name)

    def changeComboBox(self):
        databaseName = self.parserComboBox.currentText()
        currentIndex = self.parserComboBox.currentIndex()
        if len(databaseName) != 0:
            database = self.databases[databaseName]
            telemetries = [telemetry.id.name for telemetry in database.telemetryTypes]
            self.selectionWidget.setCurrentIndex(currentIndex)
            self.telemetryTypeLabel.setText(telemetries[self.selectionWidget.currentWidget().currentIndex()])

    def previousTelemetry(self):
        databaseName = self.parserComboBox.currentText()
        if len(databaseName) != 0:
            database = self.databases[databaseName]
            selectedIndex = self.selectionWidget.currentWidget().currentIndex() - 1
            if selectedIndex < 0:
                selectedIndex = len(database.telemetryTypes) - 1
            telemetries = {telemetry.id.name: telemetry.data for telemetry in database.telemetryTypes}
            selectedTelemetry = list(telemetries.keys())[selectedIndex]
            self.telemetryTypeLabel.setText(selectedTelemetry)
            self.selectionWidget.currentWidget().setCurrentIndex(selectedIndex)

    def nextTelemetry(self):
        databaseName = self.parserComboBox.currentText()
        if len(databaseName) != 0:
            database = self.databases[databaseName]
            selectedIndex = self.selectionWidget.currentWidget().currentIndex() + 1
            if selectedIndex == len(database.telemetryTypes):
                selectedIndex = 0
            telemetries = [telemetry.id.name for telemetry in database.telemetryTypes]
            selectedTelemetry = telemetries[selectedIndex]
            self.telemetryTypeLabel.setText(selectedTelemetry)
            self.selectionWidget.currentWidget().setCurrentIndex(selectedIndex)

    def selectionMade(self):
        currentItem = self.selectionWidget.currentWidget().currentWidget().currentItem()

        def getAncestors(item):
            ancestors = [item.text(0)]
            while item.parent():
                ancestors.append(item.parent().text(0))
                item = item.parent()
            return ancestors

        def getUnit(level, keys):
            for key in keys:
                if key in level:
                    level = level[key]
                else:
                    return None
            if isinstance(level, dict):
                return None
            return level

        if not currentItem.isDisabled() and currentItem.childCount() == 0:
            # RETRIEVING DATA
            database = self.parserComboBox.currentText()
            telemetry = self.telemetryTypeLabel.text()
            itemAncestors = getAncestors(currentItem)
            selectedTypes, selectedUnits = self.databases[database].nestedPythonTypes(telemetry, self.typeFilter)
            unitName = getUnit(selectedUnits, itemAncestors)
            # UPDATING VALUE
            self.selectedArgument = f"{database}/{telemetry}/{'/'.join(itemAncestors[::-1])}"
            self.selectionNameLabel.setText(self.selectedArgument)
            self.argumentUnit = self.databases[database].units[unitName][0] if unitName is not None else None


class SerialWindow(QWidget):
    sendCommand = pyqtSignal(str)

    def __init__(self):
        super(SerialWindow, self).__init__()
        self.resize(450, 350)
        self.setWindowTitle('Serial Monitor')
        self.setWindowIcon(QIcon('sources/icons/PyStrato.png'))
        # General Layout
        self.layout = QGridLayout(self)
        self.setLayout(self.layout)
        # Loading settings
        self.settings = {}
        self.settings = loadSettings("settings")
        # Text edit box
        self.textedit = QTextEdit(self)
        self.textedit.setText('Run Serial listening to display incoming info ...')
        self.textedit.setStyleSheet('font-size:15px')
        self.textedit.setLineWrapMode(QTextEdit.FixedPixelWidth)
        self.textedit.setLineWrapColumnOrWidth(1000)
        self.layout.addWidget(self.textedit, 1, 1, 1, 2)
        # Autoscroll Che-box
        self.autoscroll_box = QCheckBox("Autoscroll")
        self.autoscroll_box.setChecked(bool(self.settings["AUTOSCROLL"]))
        self.autoscroll_box.stateChanged.connect(self.changeAutoscroll)
        self.layout.addWidget(self.autoscroll_box, 2, 1)
        # Clearing Output Button
        self.clearButton = QPushButton("Clear Output")
        self.clearButton.clicked.connect(self.clearOutput)
        self.layout.addWidget(self.clearButton, 2, 2)

    def changeAutoscroll(self):
        self.settings["AUTOSCROLL"] = int(not bool(self.settings["AUTOSCROLL"]))
        saveSettings(self.settings, "settings")
        self.autoscroll_box.setChecked(bool(self.settings["AUTOSCROLL"]))

    def clearOutput(self):
        open("output", "w").close()
        self.textedit.setText("")


class MessageBox(QMessageBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        gridLayout = self.layout()
        iconLabel = self.findChild(QLabel, "qt_msgboxex_icon_label")
        iconLabel.deleteLater()
        label = self.findChild(QLabel, "qt_msgbox_label")
        label.setAlignment(Qt.AlignCenter)
        gridLayout.removeWidget(label)
        buttonBox = self.findChild(QDialogButtonBox, "qt_msgbox_buttonbox")
        gridLayout.removeWidget(buttonBox)
        gridLayout.addWidget(label, 0, 0)
        gridLayout.addWidget(buttonBox, 1, 0, alignment=Qt.AlignCenter)


class TrackedParsersDialog(QDialog):
    def __init__(self, path):
        super().__init__()
        self.setModal(True)
        self.setFixedSize(300, 600)
        self.setWindowTitle('Tracked Parsers')
        self.setWindowIcon(QIcon('sources/icons/PyStrato.png'))
        self.currentDir = path
        self.names = {}
        self.settings = loadSettings("settings")
        self.parserPath = os.path.join(self.currentDir, "parsers")

        # WIDGETS & DONE BUTTON
        self.parserScrollArea = QScrollArea()
        self.parserScrollArea.setWidgetResizable(True)
        self.parserWidget = QWidget()
        self.parserLayout = QVBoxLayout()
        self.parserWidget.setLayout(self.parserLayout)
        self.parserScrollArea.setWidget(self.parserWidget)
        self.doneButton = QPushButton("Done")
        self.doneButton.clicked.connect(self.accept)
        self.doneButton.setDefault(True)

        # CREATE PARSER BUTTONS
        self.parserButtons = []
        path = self.parserPath
        trackedFormats = self.settings['FORMAT_FILES']
        if len(trackedFormats) == 1 and len(trackedFormats[0]) == 0:
            trackedFormats = []
        availableFormats = [os.path.join(path, directory) for directory in os.listdir(path) if os.path.isdir(os.path.join(path, directory))]
        for directory in availableFormats:
            parserName = os.path.basename(directory)
            self.names[parserName] = directory
            database = BalloonPackageDatabase(directory)
            nbTelemetry, nbTelecommand = len(database.telemetryTypes), len(database.telecommandTypes)
            modificationTime = os.path.getmtime(os.path.join(directory, 'telemetry.csv'))
            modificationTimeFormatted = time.ctime(modificationTime)
            button = ThreeLineButton(parserName, f"Last Modified : {modificationTimeFormatted}",
                                     f"Telemetries : {nbTelemetry}, Telecommands : {nbTelecommand}")
            button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            self.parserLayout.addWidget(button)
            button.setCheckable(True)
            if directory in trackedFormats:
                button.setChecked(True)
            self.parserButtons.append(button)

        # MAIN LAYOUT
        mainLayout = QVBoxLayout()
        mainLayout.addWidget(self.parserScrollArea)
        mainLayout.addWidget(self.doneButton)
        self.setLayout(mainLayout)

    def returnTrackedParsers(self):
        trackedParsers = []
        for button, path in zip(self.parserButtons, list(self.names.values())):
            if button.isChecked():
                trackedParsers.append(path)
        return trackedParsers


class TwoLineButton(QPushButton):
    def __init__(self, topText, bottomText, parent=None):
        super().__init__(parent)

        # Create the labels
        self.topTextLabel = QLabel(topText)
        self.bottomTextLabel = QLabel(bottomText)

        # Set up the layout
        layout = QVBoxLayout()
        layout.addWidget(self.topTextLabel)
        layout.addWidget(self.bottomTextLabel)
        self.setLayout(layout)
        self.setMinimumSize(150, 60)


class ThreeLineButton(QPushButton):
    def __init__(self, topText, middleText, bottomText, parent=None):
        super().__init__(parent)

        # Create the labels
        self.topTextLabel = QLabel(topText)
        self.middleTextLabel = QLabel(middleText)
        self.bottomTextLabel = QLabel(bottomText)

        # Set up the layout
        layout = QVBoxLayout()
        layout.addWidget(self.topTextLabel)
        layout.addWidget(self.middleTextLabel)
        layout.addWidget(self.bottomTextLabel)
        self.setLayout(layout)
        self.setMinimumSize(150, 90)


class StringInputDialog(QDialog):
    def __init__(self, title, label_text, defaultText='', placeholder=False, exclusives=None, parent=None):
        super(StringInputDialog, self).__init__(parent)
        self.setWindowTitle(title)
        mainLayout = QVBoxLayout()
        self.placeholder = placeholder
        self.defaultText = defaultText
        self.exclusives = exclusives

        textLabel = QLabel(label_text, self)
        mainLayout.addWidget(textLabel)

        self.inputLineEdit = QLineEdit(self)
        if not self.placeholder:
            self.inputLineEdit.setText(defaultText)
        else:
            self.inputLineEdit.setPlaceholderText(defaultText)
        mainLayout.addWidget(self.inputLineEdit)

        bottomButtonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        bottomButtonBox.accepted.connect(self.validateInput)
        bottomButtonBox.rejected.connect(self.reject)
        mainLayout.addWidget(bottomButtonBox)
        self.setLayout(mainLayout)

    def validateInput(self):
        text = self.inputLineEdit.text()
        if self.exclusives and text in self.exclusives:
            QMessageBox.critical(self, "Error", "This name already exists")
            return

        self.accept()

    def getStringInput(self):
        text = self.inputLineEdit.text()
        if self.placeholder and text == '':
            return self.defaultText
        else:
            return text


class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About")
        # ABOUT TEXT EDIT
        aboutText = """
        <html>
        <body>
        <p align="justify"><strong>About the PyStrato Software</strong></p>

        <p align="justify">Our Stratospheric Balloon Ground Station software is an open-source solution designed specifically for student projects involving stratospheric balloon missions. Developed by <a href='https://github.com/EnguerranVidal'>KeplerDream</a> for the TSI Master located in Toulouse (France), with ease of use and functionality in mind, our software provides a comprehensive suite of tools and features to support ground station operations.</p>

        <p align="justify">Key Features:</p>
        <ul>
        <li><strong>Real-time telemetry data visualization :</strong>
        Visualize information in real_time through several graphical display types and plots.</li>
        <li><strong>Telemetry Parser Editing :</strong> 
        Set up the <a href='https://ecom.readthedocs.io/en/latest/index.html'>Ecom</a> database parser as you wish.</li>
        <li><strong>Weather Forecast :</strong> 
        Be able to get weather forecasts and air pollution levels from <a href='https://openweathermap.org'>OpenWeatherMap</a>.</li>
        </ul>

        <p align="justify">This software is written in Python, utilizing the power and flexibility of the language to provide an intuitive user experience. We recommend using Python 3.9 for optimal performance.</p>

        <p align="justify">Icon Provider: <a href='https://www.icons8.com'>Icons8</a></p>

        <p align="justify">Contributors: 
            <a href='https://github.com/Abestanis'>Abestanis</a>
        </p>

        <p align="justify">To get started with our Stratospheric Balloon Ground Station software, please visit our GitHub repository <a href='https://github.com/EnguerranVidal/PyStrato'>PyStrato</a> for the latest version, installation instructions, and detailed documentation. We welcome contributions from the community and encourage you to provide feedback and suggestions to help us improve the software.</p>

        <p align="justify">Thank you for choosing our software for your stratospheric balloon project. We hope it facilitates your mission and contributes to the success of your endeavors.</p>
        </body>
        </html>
        """
        testEdit = ExternalLinkTextEdit()
        testEdit.setReadOnly(True)
        testEdit.setTextInteractionFlags(Qt.TextBrowserInteraction)
        testEdit.setHtml(aboutText)
        testEdit.setFixedWidth(400)
        testEdit.setFixedHeight(500)
        doneButt = QPushButton("Done")
        doneButt.clicked.connect(self.accept)
        # MAIN LAYOUT
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.layout.addWidget(testEdit)
        self.layout.addWidget(doneButt)


class ExternalLinkTextEdit(QTextEdit):
    def __init__(self, parent=None):
        super(QTextEdit, self).__init__(parent)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            anchor = self.anchorAt(event.pos())
            if anchor:
                QDesktopServices.openUrl(QUrl(anchor))
            else:
                super().mousePressEvent(event)
        else:
            super().mousePressEvent(event)


class LayoutManagerDialog(QDialog):
    loadSignal = pyqtSignal(str)

    def __init__(self, currentDir, layoutDescription, currentLayout=None):
        super(QDialog, self).__init__()
        self.setModal(True)
        self.setFixedSize(600, 600)
        self.setWindowTitle('Layout Preset Selection')
        self.setWindowIcon(QIcon('sources/icons/PyStrato.png'))
        self.settings = loadSettings('settings')
        self.currentDir = currentDir
        self.dataPath = os.path.join(self.currentDir, "data")
        self.presetPath = os.path.join(self.dataPath, '_presets')
        self.autosavePath = os.path.join(self.presetPath, 'autosaves')
        self.examplesPath = os.path.join(self.presetPath, 'examples')
        self.currentLayout = currentLayout
        self.layoutDescription = layoutDescription
        if self.currentLayout is None or self.currentLayout == '':
            self.currentLayout = 'None'
        # LABELS
        self.layoutLabel = QLabel("Current Layout : ")
        self.selectedLabel = QLabel("Selected Layout : ")
        self.currentLayoutLabel = QLabel(self.currentLayout)
        self.selectedLayoutLabel = QLabel(self.currentLayout)
        self.topLayout = QGridLayout()
        self.topLayout.addWidget(self.layoutLabel, 0, 0, 1, 1)
        self.topLayout.addWidget(self.selectedLabel, 0, 1, 1, 1)
        self.topLayout.addWidget(self.currentLayoutLabel, 1, 0, 1, 1)
        self.topLayout.addWidget(self.selectedLayoutLabel, 1, 1, 1, 1)

        # TOP BUTTONS
        self.topButtonsWidget = QWidget()
        self.topButtonsLayout = QHBoxLayout()
        self.renameButton = QPushButton('Rename')
        self.loadButton = QPushButton('Load')
        self.deleteButton = QPushButton('Delete')
        self.newButton = QPushButton('New')
        self.renameButton.setToolTip('Rename Layout')
        self.loadButton.setToolTip('Load Save')
        self.deleteButton.setToolTip('Delete Layout')
        self.newButton.setToolTip('Create Layout')
        self.renameButton.clicked.connect(self.renameSave)
        self.loadButton.clicked.connect(self.loadSave)
        self.deleteButton.clicked.connect(self.deleteSave)
        self.newButton.clicked.connect(self.newSave)
        self.loadButton.setDisabled(True)
        self.renameButton.setDisabled(True)
        self.deleteButton.setDisabled(True)

        # BUTTON GROUP
        self.buttonGroup = QButtonGroup()
        self.buttonGroup.buttonClicked.connect(self.onSaveButtonClicked)
        self.userButtons, self.autoButtons = None, None

        self.topButtonsLayout.addWidget(self.newButton)
        self.topButtonsLayout.addWidget(self.loadButton)
        self.topButtonsLayout.addWidget(self.renameButton)
        self.topButtonsLayout.addWidget(self.deleteButton)
        self.topButtonsWidget.setLayout(self.topButtonsLayout)
        self.topLayout.addWidget(self.topButtonsWidget, 2, 0, 1, 1)

        self.savesScrollArea = QScrollArea()
        self.savesScrollArea.setWidgetResizable(True)
        self.savesWidget = None
        self.savesLayout = None
        self.initializeTab()
        self.fillTabs()

        # DONE BUTTON
        self.doneButton = QPushButton("Done")
        self.doneButton.clicked.connect(self.accept)

        # MAIN LAYOUT
        mainLayout = QVBoxLayout()
        mainLayout.addLayout(self.topLayout)
        mainLayout.addWidget(self.savesScrollArea)
        mainLayout.addWidget(self.doneButton)
        self.setLayout(mainLayout)

    def initializeTab(self):
        # USER SAVES
        self.savesWidget = QWidget()
        self.savesLayout = QVBoxLayout()
        self.savesWidget.setLayout(self.savesLayout)
        self.savesScrollArea.setWidget(self.savesWidget)

        # BUTTON GROUP
        self.buttonGroup = QButtonGroup()
        self.buttonGroup.buttonClicked.connect(self.onSaveButtonClicked)
        self.userButtons, self.autoButtons = None, None

    def fillTabs(self):
        # SAVES RECON -----------------------------------------------------
        userItems = os.listdir(self.presetPath)
        userSaves = [os.path.join(self.presetPath, item) for item in userItems if
                     os.path.isfile(os.path.join(self.presetPath, item))]
        autoItems = os.listdir(self.autosavePath)
        autoSaves = [os.path.join(self.autosavePath, item) for item in autoItems if
                     os.path.isfile(os.path.join(self.autosavePath, item))]
        filePaths = userSaves + autoSaves
        sortedFilePaths = sorted(filePaths, key=getModificationDate)
        sortedFilePaths.reverse()
        self.userButtons, self.autoButtons = [], []
        for save in sortedFilePaths:
            if save in userSaves:
                modificationTime = os.path.getmtime(os.path.join(self.presetPath, save))
                creationTime = os.path.getctime(os.path.join(self.presetPath, save))
                modificationTimeFormatted = time.ctime(modificationTime)
                creationTimeFormatted = time.ctime(creationTime)
                button = ThreeLineButton(os.path.splitext(os.path.basename(save))[0],
                                         f"Creation Date : {creationTimeFormatted}",
                                         f"Last Modified : {modificationTimeFormatted}")
                button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
                self.buttonGroup.addButton(button)
                self.savesLayout.addWidget(button)
                button.setCheckable(True)
                if os.path.splitext(os.path.basename(save))[0] == self.currentLayout:
                    button.setChecked(True)
            if save in autoSaves:
                modificationTime = os.path.getmtime(os.path.join(self.autosavePath, save))
                modificationTimeFormatted = time.ctime(modificationTime)
                button = TwoLineButton(os.path.splitext(os.path.basename(save))[0],
                                       f"Creation Date : {modificationTimeFormatted}")
                button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
                self.buttonGroup.addButton(button)
                self.savesLayout.addWidget(button)
                button.setCheckable(True)
                if os.path.splitext(os.path.basename(save))[0] == self.currentLayout:
                    button.setChecked(True)
        self.buttonGroup.buttonClicked.connect(self.onSaveButtonClicked)

    def emptyTabs(self):
        # Clear the saves Tab
        self.savesLayout.removeWidget(self.savesWidget)
        self.savesWidget.deleteLater()
        self.savesWidget = QWidget()
        self.savesLayout = QVBoxLayout()
        self.savesWidget.setLayout(self.savesLayout)
        self.savesScrollArea.setWidget(self.savesWidget)

        # Clear the button group
        for button in self.buttonGroup.buttons():
            self.buttonGroup.removeButton(button)
            button.setParent(None)

    def refreshSaveTab(self):
        self.emptyTabs()
        self.initializeTab()
        self.fillTabs()

    def generateNewName(self):
        userItems = os.listdir(self.presetPath)
        userSaves = [item for item in userItems if os.path.isfile(os.path.join(self.presetPath, item))]
        name = nameGiving(userSaves, baseName='New_Layout', parentheses=True, startingIndex=1, firstName=True)
        return name

    def onSaveButtonClicked(self, button):
        # Deselect all buttons except the clicked one
        userItems = os.listdir(self.presetPath)
        userSaves = [os.path.splitext(os.path.basename(item))[0] for item in userItems
                     if os.path.isfile(os.path.join(self.presetPath, item))]
        for otherButton in self.buttonGroup.buttons():
            if otherButton is not button:
                otherButton.setChecked(False)
        selectedLayout = button.topTextLabel.text()
        self.selectedLayoutLabel.setText(selectedLayout)
        if selectedLayout in userSaves:
            self.loadButton.setDisabled(False)
            self.renameButton.setDisabled(False)
            self.deleteButton.setDisabled(False)
        else:
            self.loadButton.setDisabled(False)
            self.renameButton.setDisabled(True)
            self.deleteButton.setDisabled(False)

    def loadSave(self):
        userItems = os.listdir(self.presetPath)
        userSaves = [os.path.splitext(os.path.basename(item))[0] for item in userItems if
                     os.path.isfile(os.path.join(self.presetPath, item))]
        selectedLayout = self.selectedLayoutLabel.text()

        if selectedLayout in userSaves:
            path = os.path.join(self.presetPath, f"{selectedLayout}.json")
        else:
            path = os.path.join(self.autosavePath, f"{selectedLayout}.json")
        reply = QMessageBox.question(self, 'Message', "Do you really want to load this layout?\n "
                                                      "Some changes to the current layout may not have been saved.",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.loadSignal.emit(path)
            self.currentLayoutLabel.setText(selectedLayout)

    def newSave(self):
        userItems = os.listdir(self.presetPath)
        userSaves = [os.path.splitext(os.path.basename(item))[0] for item in userItems if
                     os.path.isfile(os.path.join(self.presetPath, item))]
        defaultName = self.generateNewName()
        newNameDialog = StringInputDialog('Creating a New Layout', 'New Layout Name :',
                                          defaultText=defaultName, placeholder=True, exclusives=userSaves)
        result = newNameDialog.exec_()
        if result == QDialog.Accepted:
            givenNewName = newNameDialog.getStringInput()
            newLayoutPath = os.path.join(self.presetPath, f"{givenNewName}.json")
            with open(newLayoutPath, 'w') as file:
                json.dump({}, file)

            messageBox = QMessageBox()
            messageBox.setIcon(QMessageBox.Question)
            messageBox.setWindowTitle("Load Layout")
            messageBox.setText("Do you want to load the newly created layout?")
            messageBox.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            messageBox.setDefaultButton(QMessageBox.No)
            reply = messageBox.exec_()
            if reply == QMessageBox.Yes:
                self.selectedLayoutLabel.setText(givenNewName)
                self.loadSave()
        self.refreshSaveTab()

    def renameSave(self):
        userItems = os.listdir(self.presetPath)
        userSaves = [os.path.splitext(os.path.basename(item))[0] for item in userItems if
                     os.path.isfile(os.path.join(self.presetPath, item))]
        selectedLayout = self.selectedLayoutLabel.text()
        userSaves.remove(selectedLayout)
        newNameDialog = StringInputDialog('Renaming Display Layout', 'New Layout Name :',
                                          defaultText=selectedLayout, placeholder=False, exclusives=userSaves)
        result = newNameDialog.exec_()
        if result == QDialog.Accepted:
            givenNewName = newNameDialog.getStringInput()
            oldPath = os.path.join(self.presetPath, f"{selectedLayout}.json")
            newPath = os.path.join(self.presetPath, f"{givenNewName}.json")
            try:
                os.rename(oldPath, newPath)
            except OSError as e:
                print(f"An error occurred: {e}")
            finally:
                self.refreshSaveTab()

    def deleteSave(self):
        selectedLayout = self.selectedLayoutLabel.text()
        # TODO : MAYBE ADD SPECIFIC MESSAGE IF CURRENT LAYOUT IS ABOUT TO BE DELETED ?
        reply = QMessageBox.question(self, 'Message', "Are you sure to delete this layout?", QMessageBox.Yes |
                                     QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            userItems = os.listdir(self.presetPath)
            userSaves = [os.path.splitext(os.path.basename(item))[0] for item in userItems if
                         os.path.isfile(os.path.join(self.presetPath, item))]
            try:
                if selectedLayout in userSaves:
                    os.remove(os.path.join(self.presetPath, f"{selectedLayout}.json"))
                else:
                    os.remove(os.path.join(self.autosavePath, f"{selectedLayout}.json"))
            except OSError as e:
                print(f"An error occurred: {e}")
            finally:
                self.refreshSaveTab()


class ScrollableContainer(QScrollArea):
    def __init__(self, parent=None):
        super(ScrollableContainer, self).__init__(parent)
        self.setWidgetResizable(True)
        self.containerWidget = QWidget(self)
        self.containerLayout = QHBoxLayout(self.containerWidget)
        self.setWidget(self.containerWidget)
        self.setFrameShape(QFrame.NoFrame)

    def addWidget(self, widget):
        self.containerLayout.addWidget(widget)


class ScrollableWidget(QWidget):
    def __init__(self, path, widgetList, widgetsToScroll=3):
        super(ScrollableWidget, self).__init__()
        self.settings = loadSettings('settings')
        themeFolder = 'dark-theme' if self.settings['DARK_THEME'] else 'light-theme'
        # SCROLLING BUTTONS AND AREA
        # Scroll Left Button
        self.currentDir = path
        self.scrollLeftButton = SquareIconButton(f'sources/icons/{themeFolder}/icons8-back-96.png', self, flat=True)
        self.scrollLeftButton.clicked.connect(self.scrollLeft)
        self.scrollLeftButton.setFixedWidth(30)
        # Scroll Right Button
        self.scrollRightButton = SquareIconButton(f'sources/icons/{themeFolder}/icons8-forward-96.png', self, flat=True)
        self.scrollRightButton.clicked.connect(self.scrollRight)
        self.scrollRightButton.setFixedWidth(30)
        # Scroll Area
        self.scrollArea = ScrollableContainer(self)
        self.currentScrollPosition = 0
        self.widgetsToScroll = widgetsToScroll
        self.widgetWidth = widgetList[0].sizeHint().width() if widgetList else 0
        self.widgetHeight = widgetList[0].sizeHint().height() if widgetList else 0
        self.setFixedHeight(int(self.widgetHeight * 1.5))
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.scrollAnimation = QPropertyAnimation(self.scrollArea.horizontalScrollBar(), b"value")
        self.scrollAnimation.setEasingCurve(QEasingCurve.OutCubic)
        self.scrollAnimation.setDuration(500)

        # CONTAINER & LAYOUT
        for widget in widgetList:
            self.scrollArea.addWidget(widget)
        mainLayout = QVBoxLayout(self)
        buttonLayout = QHBoxLayout()
        buttonLayout.addWidget(self.scrollLeftButton)
        buttonLayout.addWidget(self.scrollArea)
        buttonLayout.addWidget(self.scrollRightButton)
        mainLayout.addLayout(buttonLayout)

    def scrollLeft(self):
        self.currentScrollPosition -= self.widgetsToScroll
        self.scrollAnimation.stop()
        self.scrollAnimation.setStartValue(self.scrollArea.horizontalScrollBar().value())
        self.scrollAnimation.setEndValue(self.currentScrollPosition * self.widgetWidth)
        self.scrollAnimation.start()

    def scrollRight(self):
        self.currentScrollPosition += self.widgetsToScroll
        self.scrollAnimation.stop()
        self.scrollAnimation.setStartValue(self.scrollArea.horizontalScrollBar().value())
        self.scrollAnimation.setEndValue(self.currentScrollPosition * self.widgetWidth)
        self.scrollAnimation.start()

    def changeTheme(self):
        self.settings = loadSettings('settings')
        themeFolder = 'dark-theme' if self.settings['DARK_THEME'] else 'light-theme'
        self.scrollLeftButton.setIcon(QIcon(f'sources/icons/{themeFolder}/icons8-back-96.png'))
        self.scrollRightButton.setIcon(QIcon(f'sources/icons/{themeFolder}/icons8-forward-96.png'))


class SearchBar(QLineEdit):
    searchDone = pyqtSignal()

    def __init__(self, searchOptions, maxSuggestions=5, parent=None):
        super(SearchBar, self).__init__(parent)
        self.selection = ''
        self.searchOptions = searchOptions
        self.maxSuggestions = maxSuggestions

        # LINE EDIT
        self.setPlaceholderText('Search Location ...')
        searchCompleter = QCompleter(self.searchOptions, self)
        searchCompleter.setCaseSensitivity(Qt.CaseInsensitive)
        searchCompleter.setFilterMode(Qt.MatchStartsWith)
        searchCompleter.setCompletionMode(QCompleter.PopupCompletion)
        searchCompleter.setMaxVisibleItems(self.maxSuggestions)
        self.setCompleter(searchCompleter)
        searchCompleter.activated.connect(self.onCompleterActivated)

        # SEARCH ACTION BUTTON
        self.searchButtonAction = QAction(self)
        self.settings = loadSettings('settings')
        themeFolder = 'dark-theme' if self.settings['DARK_THEME'] else 'light-theme'
        self.searchButtonAction.setIcon(QIcon(f'sources/icons/{themeFolder}/icons8-search-96.png'))
        self.searchButtonAction.triggered.connect(self.performSearch)
        self.addAction(self.searchButtonAction, QLineEdit.TrailingPosition)

    def performSearch(self):
        if self.text() != '':
            closestSuggestion = self.completer().currentCompletion()
            self.selection = closestSuggestion
            self.searchDone.emit()
            QTimer.singleShot(0, self.clearLineEdit)

    def changeTheme(self):
        self.settings = loadSettings('settings')
        themeFolder = 'dark-theme' if self.settings['DARK_THEME'] else 'light-theme'
        self.searchButtonAction.setIcon(QIcon(f'sources/icons/{themeFolder}/icons8-search-96.png'))

    def onCompleterActivated(self, text):
        self.selection = text
        self.searchDone.emit()
        QTimer.singleShot(0, self.clearLineEdit)

    def clearLineEdit(self):
        self.clear()
        self.setPlaceholderText('Search Location ...')


class SquareIconButton(QPushButton):
    def __init__(self, icon: str, parent=None, size=25, flat=False):
        super(SquareIconButton, self).__init__(parent)
        self.iconPath = icon
        self.setIcon(QIcon(self.iconPath))
        self.setIconSize(QSize(size, size))
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        if flat:
            styleSheet = 'border: none;text-align: center; margin-left:50%; margin-right:50%;'
            self.setFlat(True)
        else:
            styleSheet = 'text-align: center; margin-left:50%; margin-right:50%;'
        self.setStyleSheet(styleSheet)
        self.setAutoFillBackground(False)

    def setIconSize(self, size):
        super().setIconSize(size)
        self.setFixedSize(size)

    def sizeHint(self):
        return self.iconSize()


class ArrowWidget(QLabel):
    def __init__(self, iconPath: str, angle: int = 0):
        super().__init__()
        self.sizeIntegers = (25, 25)
        self.iconPath = iconPath
        self.angle = angle

        self.setAlignment(Qt.AlignCenter)
        self.setFixedSize(self.sizeIntegers[0], self.sizeIntegers[1])
        self.updateIcon(self.angle)

    def setSize(self, height: int = 25, width: int = 25):
        self.sizeIntegers = (height, width)
        self.setFixedSize(self.sizeIntegers[0], self.sizeIntegers[1])
        self.updateIcon(self.angle)

    def updateIcon(self, angle):
        self.angle = angle
        pixmap = QPixmap(self.iconPath)
        pixmap = pixmap.scaledToWidth(100)
        rotated_pixmap = pixmap.transformed(
            QTransform().rotate(angle), Qt.SmoothTransformation
        ).scaled(self.sizeIntegers[0], self.sizeIntegers[1],
                 Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.setPixmap(rotated_pixmap)

    def setAngle(self, angle):
        self.angle = angle
        self.updateIcon(self.angle)


class ValueWidget(QWidget):
    valueChanged = pyqtSignal(tuple)

    def __init__(self, cType, value='', arraySize=1):
        super(QWidget, self).__init__()
        self.cType, self.arraySize, self.value = cType, arraySize, value
        self.valueWidget = None
        self.setLayout(QVBoxLayout())
        self.createValueWidget()

    def createValueWidget(self):
        if self.arraySize == 1 or self.cType == 'char':
            if self.cType == 'bool':
                self.valueWidget = QComboBox()
                self.valueWidget.addItems(['true', 'false'])
                if self.value not in ['true', 'false']:
                    self.value = 'false'
                self.valueWidget.setCurrentIndex(['true', 'false'].index(self.value))
                self.valueWidget.currentIndexChanged.connect(
                    lambda value=self.valueWidget.currentText(): self.changeValue(value))

            elif self.cType.startswith('int') or self.cType.startswith('uint'):
                minValue, maxValue = self.getIntRange(self.cType)
                self.valueWidget = QLineEdit()
                if np.iinfo(np.int64).min <= minValue <= np.iinfo(np.int64).max and np.iinfo(
                        np.int64).min <= maxValue <= np.iinfo(np.int64).max:
                    if not self.value.isdigit() or not minValue <= int(self.value) <= maxValue:
                        self.value = '0'
                    self.valueWidget.setValidator(QIntValidator(minValue, maxValue))
                self.valueWidget.setText(self.value)
                self.valueWidget.textChanged.connect(lambda value=self.valueWidget.text(): self.changeValue(value))

            elif self.cType == 'double':
                self.valueWidget = QLineEdit()
                self.valueWidget.setValidator(QDoubleValidator())
                if not self.value or not self.value.replace('.', '').isdigit():
                    self.value = '0.0'
                self.valueWidget.setText(self.value)
                self.valueWidget.textChanged.connect(lambda value=self.valueWidget.text(): self.changeValue(value))

            elif self.cType == 'float':
                self.valueWidget = QLineEdit()
                self.valueWidget.setValidator(
                    QDoubleValidator(-3.4e+38, 3.4e+38, 4, notation=QDoubleValidator.StandardNotation))
                if not self.value or not self.value.replace('.', '').isdigit():
                    self.value = '0.0'
                self.valueWidget.setText(self.value)
                self.valueWidget.textChanged.connect(lambda value=self.valueWidget.text(): self.changeValue(value))

            elif self.cType == 'char':
                self.valueWidget = QLineEdit()
                self.valueWidget.setMaxLength(self.arraySize)
                if not self.value:
                    self.value = ''
                if len(self.value) > self.arraySize:
                    self.value = self.value[:self.arraySize]
                self.valueWidget.setText(self.value)
                self.valueWidget.textChanged.connect(lambda value=self.valueWidget.text(): self.changeValue(value))

            elif self.cType == 'bytes':
                minValue, maxValue = self.getIntRange('uint8')
                self.valueWidget = QLineEdit()
                if np.iinfo(np.int64).min <= minValue <= np.iinfo(np.int64).max and np.iinfo(
                        np.int64).min <= maxValue <= np.iinfo(np.int64).max:
                    if not self.value.isdigit() or not minValue <= int(self.value) <= maxValue:
                        self.value = '0'
                    self.valueWidget.setValidator(QIntValidator(minValue, maxValue))
                self.valueWidget.setText(self.value)
                self.valueWidget.textChanged.connect(lambda value=self.valueWidget.text(): self.changeValue(value))
            else:
                self.valueWidget = QWidget()
        else:
            self.valueWidget = QWidget()

        self.layout().addWidget(self.valueWidget)
        self.layout().setContentsMargins(0, 0, 0, 0)

    def addValue(self):
        # TODO : Create a new ValueWidget for array elements
        elementType = self.cType[:-2]
        elementWidget = ValueWidget(elementType)
        self.layout().insertWidget(self.layout().count() - 1, elementWidget)

    def changeCType(self, newCType, arraySize=1):
        if newCType == self.cType and self.arraySize == int(arraySize):
            return
        if self.valueWidget:
            self.valueWidget.setParent(None)
            self.valueWidget = None
        self.cType = newCType
        self.arraySize = int(arraySize)
        self.createValueWidget()

    def changeValue(self, value):
        self.value = value
        self.valueChanged.emit((self.cType, self.value))

    def destroyValue(self):
        if self.valueWidget:
            self.valueWidget.setParent(None)
            self.valueWidget = None

    @staticmethod
    def getIntRange(cType):
        if cType.startswith('int'):
            size = int(cType[3:])
            maxVal = np.iinfo(np.int64).max if size > 64 else np.int64(np.power(2, size - 1) - 1)
            minVal = -maxVal - 1
        elif cType.startswith('uint'):
            size = int(cType[4:])
            maxVal = np.iinfo(np.uint64).max if size > 64 else np.uint64(np.power(2, size) - 1)
            minVal = 0
        return minVal, maxVal
