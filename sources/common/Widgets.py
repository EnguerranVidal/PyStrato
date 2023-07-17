######################## IMPORTS ########################
import os
import time

import numpy as np
from ecom.datatypes import TypeInfo

# ------------------- PyQt Modules -------------------- #
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtCore import Qt
from PyQt5.QtGui import *

# --------------------- Sources ----------------------- #
from sources.common.FileHandling import load_settings, save_settings
from sources.databases.balloondata import BalloonPackageDatabase
from sources.databases.units import DefaultUnitsCatalogue


######################## CLASSES ########################
class BasicDisplay(QWidget):
    def __init__(self, path, parent=None):
        super().__init__(parent)
        self.generalSettings = load_settings('settings')
        self.catalogue = DefaultUnitsCatalogue()
        self.settingsWidget = QWidget()
        self.currentDir = path
        self.display = None

    def applyChanges(self, editWidget):
        pass

    def updateContent(self, content):
        pass

    @staticmethod
    def getDescription():
        return {'TYPE': 'BASIC_DISPLAY'}


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


class TypeSelector(QWidget):
    def __init__(self, name, database: BalloonPackageDatabase, sharedDataTypes: bool = False):
        super(QWidget, self).__init__()
        self.sharedDataTypes = sharedDataTypes
        self.database = database
        self.setWindowTitle('Selecting Configuration Type or Unit')
        self.basicTypes = [baseType.value for baseType in TypeInfo.BaseType]
        # Lists
        self.basicTypesList = QListWidget()
        self.basicTypesLabel = QLabel('Basic Types')
        self.unitsList = QListWidget()
        self.unitsLabel = QLabel('Database Units')
        self.dataTypesList = QListWidget()
        self.dataTypesLabel = QLabel('Data Types')
        self.basicTypesList.itemClicked.connect(self.itemClickedBasic)
        self.unitsList.itemClicked.connect(self.itemClickedUnit)
        self.dataTypesList.itemClicked.connect(self.itemClickedData)

        # General Layout
        centralLayout = QGridLayout()
        centralLayout.addWidget(self.basicTypesLabel, 0, 0)
        centralLayout.addWidget(self.basicTypesList, 1, 0)
        centralLayout.addWidget(self.unitsLabel, 0, 1)
        centralLayout.addWidget(self.unitsList, 1, 1)
        if self.sharedDataTypes:
            centralLayout.addWidget(self.dataTypesLabel, 0, 2)
            centralLayout.addWidget(self.dataTypesList, 1, 2)

        # Selected Type
        self.selectedLabel = QLabel()
        self.selectedLabel.setText(name)
        centralLayout.addWidget(self.selectedLabel, 2, 0)

        # Adding Buttons
        self.buttons = QDialogButtonBox()
        self.buttons.setStandardButtons(QDialogButtonBox.Cancel | QDialogButtonBox.Ok)
        self.buttons.button(QDialogButtonBox.Ok).setText("Apply")
        centralLayout.addWidget(self.buttons, 2, 1)

        self.setLayout(centralLayout)
        self.populateLists()

    def populateLists(self, database: BalloonPackageDatabase = None):
        # Clearing Past Items
        if database is not None:
            self.database = database
            self.unitsList.clear()
            self.basicTypesList.clear()
        # Filling Lists
        for basicType in self.basicTypes:
            self.basicTypesList.addItem(basicType)
        for unitName, unitVariants in self.database.units.items():
            self.unitsList.addItem(unitName)
        if self.sharedDataTypes:
            autogeneratedTypes = [
                'ConfigurationId',
                'Configuration',
                'Telecommand',
                'TelemetryType',
            ]
            for name, typeInfo in self.database.dataTypes.items():
                if name not in autogeneratedTypes:
                    self.dataTypesList.addItem(name)

    def itemClickedBasic(self):
        selection = self.basicTypesList.selectedItems()
        self.selectedLabel.setText(selection[0].text())

    def itemClickedUnit(self):
        selection = self.unitsList.selectedItems()
        self.selectedLabel.setText(selection[0].text())

    def itemClickedData(self):
        selection = self.dataTypesList.selectedItems()
        self.selectedLabel.setText(selection[0].text())


class ArgumentSelectorWidget(QWidget):
    def __init__(self, path, parent=None, typeFilter=(int, float)):
        super().__init__(parent)
        self.selectedUnits = {}
        self.selectedTypes = {}
        self.currentDir = path
        self.typeFilter = typeFilter
        self.formatPath = os.path.join(self.currentDir, "formats")
        self.databases = None
        self.settings = load_settings('settings')
        # Set up combo box
        self.comboBox = QComboBox()
        self.fillComboBox()
        self.comboBox.currentIndexChanged.connect(self.changeComboBox)

        # Set up buttons and label
        self.previousButton = QPushButton()
        self.previousButton.setStyleSheet("border: none;")
        self.previousButton.setFlat(True)
        self.previousButton.setIcon(QIcon('sources/icons/light-theme/icons8-previous-96.png'))
        self.previousButton.setIconSize(QSize(20, 20))
        self.previousButton.clicked.connect(self.previousTelemetry)

        self.nextButton = QPushButton()
        self.nextButton.setStyleSheet("border: none;")
        self.nextButton.setFlat(True)
        self.nextButton.setIcon(QIcon('sources/icons/light-theme/icons8-next-96.png'))
        self.nextButton.setIconSize(QSize(20, 20))
        self.nextButton.clicked.connect(self.nextTelemetry)
        self.label = QLabel("Label")
        self.label.setAlignment(Qt.AlignCenter)

        # Set up tree widget
        self.treeWidget = QTreeWidget()
        self.treeWidget.setHeaderLabels([])
        self.treeWidget.setHeaderHidden(True)
        self.treeWidget.setColumnCount(1)
        self.treeItems = {}

        # Set up Main Layout
        mainLayout = QVBoxLayout()
        topRowLayout = QHBoxLayout()
        topRowLayout.addWidget(self.comboBox)
        mainLayout.addLayout(topRowLayout)
        secondRowLayout = QHBoxLayout()
        secondRowLayout.addWidget(self.previousButton)
        secondRowLayout.addWidget(self.label)
        secondRowLayout.addWidget(self.nextButton)
        mainLayout.addLayout(secondRowLayout)
        mainLayout.addWidget(self.treeWidget)
        self.setLayout(mainLayout)

        self.changeComboBox()

    def fillComboBox(self):
        self.settings = load_settings('settings')
        files = self.settings['FORMAT_FILES']
        if len(files) == 1 and len(files[0]) == 0:
            files = []
        self.databases = {}
        for file in files:
            path = os.path.join(self.formatPath, file)
            name, database = os.path.basename(path), BalloonPackageDatabase(path)
            self.databases[name] = (database, 0)
        self.comboBox.clear()
        names = list(self.databases.keys())
        if len(names) != 0:
            for name in names:
                self.comboBox.addItem(name)

    def changeComboBox(self):
        databaseName = self.comboBox.currentText()
        if len(databaseName) != 0:
            database, selectedIndex = self.databases[databaseName]
            telemetries = {telemetry.id.name: telemetry.data for telemetry in database.telemetryTypes}
            selectedTelemetry = list(telemetries.keys())[selectedIndex]
            self.label.setText(selectedTelemetry)
            self.fillTreeWidget(databaseName)

    def previousTelemetry(self):
        databaseName = self.comboBox.currentText()
        if len(databaseName) != 0:
            database, selectedIndex = self.databases[databaseName]
            selectedIndex -= 1
            if selectedIndex < 0:
                selectedIndex = len(database.telemetryTypes) - 1
            self.databases[databaseName] = (database, selectedIndex)
            telemetries = {telemetry.id.name: telemetry.data for telemetry in database.telemetryTypes}
            selectedTelemetry = list(telemetries.keys())[selectedIndex]
            self.label.setText(selectedTelemetry)
            self.fillTreeWidget(databaseName)

    def nextTelemetry(self):
        databaseName = self.comboBox.currentText()
        if len(databaseName) != 0:
            database, selectedIndex = self.databases[databaseName]
            selectedIndex += 1
            if selectedIndex == len(database.telemetryTypes):
                selectedIndex = 0
            self.databases[databaseName] = (database, selectedIndex)
            telemetries = {telemetry.id.name: telemetry.data for telemetry in database.telemetryTypes}
            selectedTelemetry = list(telemetries.keys())[selectedIndex]
            self.label.setText(selectedTelemetry)
            self.fillTreeWidget(databaseName)

    def fillTreeWidget(self, databaseName: str):
        self.treeWidget.clear()
        database, selectedIndex = self.databases[databaseName]
        telemetryName = database.telemetryTypes[selectedIndex].id.name
        self.selectedTypes, self.selectedUnits = database.nestedPythonTypes(telemetryName, searchedType=self.typeFilter)

        def addGrandChildren(treeItem, selectedDict):
            for childName, childValue in selectedDict.items():
                if isinstance(childValue, dict):
                    child = QTreeWidgetItem(treeItem, [childName])
                    treeItem.addChild(child)
                    child.setFlags(child.flags() & ~Qt.ItemIsEnabled)
                    addGrandChildren(child, childValue)
                elif isinstance(childValue, bool):
                    child = QTreeWidgetItem(treeItem, [childName])
                    treeItem.addChild(child)
                    if value:
                        child.setFlags(child.flags() & Qt.ItemIsEnabled)
                    else:
                        child.setFlags(child.flags() & ~Qt.ItemIsEnabled)
            return treeItem

        for name, value in self.selectedTypes.items():
            if isinstance(value, dict):
                item = QTreeWidgetItem(self.treeWidget, [name])
                self.treeWidget.addTopLevelItem(item)
                item.setFlags(item.flags() & ~Qt.ItemIsEnabled)
                addGrandChildren(item, value)
            elif isinstance(value, bool):
                item = QTreeWidgetItem(self.treeWidget, [name])
                self.treeWidget.addTopLevelItem(item)
                if value:
                    item.setFlags(item.flags() & Qt.ItemIsEnabled)
                else:
                    item.setFlags(item.flags() & ~Qt.ItemIsEnabled)


class ArgumentSelector(QDialog):
    selected = pyqtSignal()

    def __init__(self, path, parent=None):
        super().__init__(parent)
        self.selectedArgument = None
        self.argumentUnit = None
        self.currentDir = path
        self.formatPath = os.path.join(self.currentDir, 'formats')
        # Set up label
        self.label = QLabel("Select an argument")

        # Set up item selection widget
        self.itemSelectionWidget = ArgumentSelectorWidget(self.currentDir)
        self.itemSelectionWidget.treeWidget.itemSelectionChanged.connect(self.selectionMade)

        # Set buttons for bottom row
        bottomRowLayout = QHBoxLayout()
        self.selectButton = QPushButton("Select")
        self.cancelButton = QPushButton("Cancel")
        self.selectButton.clicked.connect(self.selectedPushed)
        self.cancelButton.clicked.connect(self.cancelPushed)
        bottomRowLayout.addWidget(self.selectButton)
        bottomRowLayout.addWidget(self.cancelButton)

        # Setting Up Selected Name
        self.selectionNameLabel = QLabel()

        mainLayout = QVBoxLayout()
        mainLayout.addWidget(self.label)
        mainLayout.addWidget(self.itemSelectionWidget)
        mainLayout.addLayout(bottomRowLayout)
        self.setLayout(mainLayout)

    def selectedPushed(self):
        if self.selectedArgument is not None:
            self.selected.emit()
            self.close()

    def cancelPushed(self):
        self.close()

    def selectionMade(self):
        currentItem = self.itemSelectionWidget.treeWidget.currentItem()

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
            return level

        if not currentItem.isDisabled():
            # Retrieving Data
            database = self.itemSelectionWidget.comboBox.currentText()
            telemetry = self.itemSelectionWidget.label.text()
            itemAncestors = getAncestors(currentItem)
            unitName = getUnit(self.itemSelectionWidget.selectedUnits, itemAncestors)
            itemName = currentItem.text(0)
            # Updating Value
            self.selectionNameLabel.setText(itemName)
            self.selectedArgument = '{}${}${}'.format(database, telemetry, '$'.join(itemAncestors))
            if unitName is not None:
                self.argumentUnit = self.itemSelectionWidget.databases[database][0].units[unitName][0]
            else:
                self.argumentUnit = None


class SerialWindow(QWidget):
    sendCommand = pyqtSignal(str)

    def __init__(self):
        super(SerialWindow, self).__init__()
        self.resize(450, 350)
        self.setWindowTitle('Serial Monitor')
        self.setWindowIcon(QIcon('sources/icons/PyGS.jpg'))
        # General Layout
        self.layout = QGridLayout(self)
        self.setLayout(self.layout)
        # Loading settings
        self.settings = {}
        self.settings = load_settings("settings")
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
        save_settings(self.settings, "settings")
        self.autoscroll_box.setChecked(bool(self.settings["AUTOSCROLL"]))

    def clearOutput(self):
        open("output", "w").close()
        self.textedit.setText("")


class MessageBox(QMessageBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        grid_layout = self.layout()
        qt_msgboxex_icon_label = self.findChild(QLabel, "qt_msgboxex_icon_label")
        qt_msgboxex_icon_label.deleteLater()
        qt_msgbox_label = self.findChild(QLabel, "qt_msgbox_label")
        qt_msgbox_label.setAlignment(Qt.AlignCenter)
        grid_layout.removeWidget(qt_msgbox_label)
        qt_msgbox_buttonbox = self.findChild(QDialogButtonBox, "qt_msgbox_buttonbox")
        grid_layout.removeWidget(qt_msgbox_buttonbox)
        grid_layout.addWidget(qt_msgbox_label, 0, 0)
        grid_layout.addWidget(qt_msgbox_buttonbox, 1, 0, alignment=Qt.AlignCenter)


class NewPackageWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Create New Package')
        self.setWindowIcon(QIcon('sources/icons/PyGS.jpg'))
        self.dataChanged = False
        self.saveChanged = False
        self.resize(400, 100)
        self.dlgLayout = QVBoxLayout()
        self.formLayout = QFormLayout()
        self.nameEdit = QLineEdit()
        self.dataEdit = QLineEdit()
        self.formatEdit = QLineEdit()
        self.formLayout.addRow('Name:', self.nameEdit)
        self.dlgLayout.addLayout(self.formLayout)
        self.buttons = QDialogButtonBox()
        self.buttons.setStandardButtons(QDialogButtonBox.Cancel | QDialogButtonBox.Ok)
        self.dlgLayout.addWidget(self.buttons)
        self.setLayout(self.dlgLayout)


class TrackedBalloonsWindow(QWidget):
    def __init__(self, path):
        super().__init__()
        self.current_dir = path
        self.format_path = os.path.join(self.current_dir, "formats")
        self.setWindowTitle('Tracked Balloons')
        self.setWindowIcon(QIcon('sources/icons/PyGS.jpg'))
        self.settings = load_settings("settings")
        # Selected Balloon List
        self.selectedList = BalloonsListWidget()
        self.selectedLabel = QLabel('Tracked Formats')
        # Trackable Balloons List
        self.availableList = BalloonsListWidget()
        self.availableLabel = QLabel('Available Formats')
        # General Layout
        layout = QVBoxLayout()
        self.editorWidget = QWidget()
        editorLayout = QGridLayout()
        editorLayout.addWidget(self.selectedLabel, 0, 0)
        editorLayout.addWidget(self.selectedList, 1, 0)
        editorLayout.addWidget(self.availableLabel, 0, 1)
        editorLayout.addWidget(self.availableList, 1, 1)
        self.editorWidget.setLayout(editorLayout)
        layout.addWidget(self.editorWidget)

        self.buttons = QDialogButtonBox()
        self.buttons.setStandardButtons(QDialogButtonBox.Cancel | QDialogButtonBox.Ok)
        self.buttons.button(QDialogButtonBox.Ok).setText("Accept")
        layout.addWidget(self.buttons)
        self.setLayout(layout)

        # Populating Names and Lists
        self.names = {}
        self.populateFormats()

    def populateFormats(self):
        path = self.format_path
        trackedFormats = self.settings['FORMAT_FILES']
        if len(trackedFormats) == 1 and len(trackedFormats[0]) == 0:
            trackedFormats = []
        availableFormats = [directory for directory in os.listdir(path) if os.path.isdir(os.path.join(path, directory))]
        # Get NAMES for later uses
        for directory in availableFormats:
            self.names[os.path.basename(directory)] = directory
        for directory in trackedFormats:
            if directory in availableFormats:
                availableFormats.remove(directory)
        # Fill both lists
        for directory in trackedFormats:
            self.selectedList.addItem(os.path.basename(directory))
        for directory in availableFormats:
            self.availableList.addItem(os.path.basename(directory))

    def getListedValues(self):
        trackedFormats = []
        for i in range(self.selectedList.count()):
            item = self.selectedList.item(i)
            trackedFormats.append(self.names[item.text()])
        return trackedFormats


class BalloonsListWidget(QListWidget):
    def __init__(self):
        super(QListWidget, self).__init__()
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setDragDropOverwriteMode(False)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setDefaultDropAction(Qt.MoveAction)

    def dropEvent(self, event):
        source = event.source()
        items = source.selectedItems()
        for i in items:
            source.takeItem(source.indexFromItem(i).row())
            self.addItem(i)


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
    def __init__(self, title, label_text, parent=None):
        super(StringInputDialog, self).__init__(parent)
        self.setWindowTitle(title)
        mainLayout = QVBoxLayout()
        textLabel = QLabel(label_text, self)
        mainLayout.addWidget(textLabel)

        self.inputLineEdit = QLineEdit(self)
        mainLayout.addWidget(self.inputLineEdit)

        bottomButtonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        bottomButtonBox.accepted.connect(self.accept)
        bottomButtonBox.rejected.connect(self.reject)
        mainLayout.addWidget(bottomButtonBox)
        self.setLayout(mainLayout)

    def getStringInput(self):
        return self.inputLineEdit.text()


class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About")
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        # Add your content here
        aboutText = """
        <html>
        <body>
        <p align="justify">About the PyGS Software</p>

        <p align="justify">Our Stratospheric Balloon Ground Station software is an open-source solution designed specifically for student projects involving stratospheric balloon missions. Developed by <a href='https://github.com/EnguerranVidal'>KeplerDream</a> for the TSI Master located in Toulouse (France), with ease of use and functionality in mind, our software provides a comprehensive suite of tools and features to support ground station operations.</p>

        <p align="justify">Key Features:</p>
        <ul>
        <li>Real-time telemetry data visualization: Visualize information in real_time through several diagram types and plots.</li>
        <li>Payload Telemetry Data Editing : Set up the telecommunication payload layout.</li>
        </ul>

        <p align="justify">This software is written in Python, utilizing the power and flexibility of the language to provide an intuitive user experience. We recommend using Python 3.9 for optimal performance.</p>

        <p align="justify">Icon Provider: <a href='https://www.icons8.com'>Icons8</a></p>

        <p align="justify">Contributors: 
            <a href='https://github.com/Abestanis'>Abestanis</a>
        </p>

        <p align="justify">To get started with our Stratospheric Balloon Ground Station software, please visit our GitHub repository <a href='https://github.com/EnguerranVidal/PyGS'>PyGS</a> for the latest version, installation instructions, and detailed documentation. We welcome contributions from the community and encourage you to provide feedback and suggestions to help us improve the software.</p>

        <p align="justify">Thank you for choosing our software for your stratospheric balloon project. We hope it facilitates your mission and contributes to the success of your endeavors.</p>
        </body>
        </html>
        """

        text_edit = ExternalLinkTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setTextInteractionFlags(Qt.TextBrowserInteraction)
        text_edit.setHtml(aboutText)
        self.layout.addWidget(text_edit)

        done_button = QPushButton("Done")
        done_button.clicked.connect(self.accept)
        self.layout.addWidget(done_button)

        # Set fixed width and height
        text_edit.setFixedWidth(400)
        text_edit.setFixedHeight(500)


class ExternalLinkTextEdit(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)

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
    accepted = pyqtSignal()
    applied = pyqtSignal()
    canceled = pyqtSignal()

    def __init__(self, currentDir, currentLayout=None):
        super().__init__()
        self.setModal(True)
        self.setFixedSize(400, 600)
        self.setWindowTitle('Layout Preset Selection')
        self.setWindowIcon(QIcon('sources/icons/PyGS.jpg'))
        self.currentDir = currentDir
        self.dataPath = os.path.join(self.currentDir, "data")
        self.presetPath = os.path.join(self.dataPath, 'presets')
        self.autosavePath = os.path.join(self.presetPath, 'autosaves')
        self.examplesPath = os.path.join(self.presetPath, 'examples')
        self.currentLayout = currentLayout
        if self.currentLayout is None or self.currentLayout == '':
            self.currentLayout = 'None'
        self.layoutLabel = QLabel("Current Layout : ")
        self.selectedLabel = QLabel("Selected Layout : ")
        self.currentLayoutLabel = QLabel(self.currentLayout)
        self.selectedLayoutLabel = QLabel(self.currentLayout)
        self.topLayout = QGridLayout()
        self.topLayout.addWidget(self.layoutLabel, 0, 0, 1, 1)
        self.topLayout.addWidget(self.selectedLabel, 0, 1, 1, 1)
        self.topLayout.addWidget(self.currentLayoutLabel, 1, 0, 1, 1)
        self.topLayout.addWidget(self.selectedLayoutLabel, 1, 1, 1, 1)

        # Tab Widget
        self.tabWidget = QTabWidget()

        # AUTOSAVES
        self.autosaveScrollArea = QScrollArea()
        self.autosaveScrollArea.setWidgetResizable(True)
        # AutoSaves Buttons
        self.autosaveWidget = QWidget()
        self.autosaveLayout = QVBoxLayout()
        self.autosaveWidget.setLayout(self.autosaveLayout)
        self.autosaveScrollArea.setWidget(self.autosaveWidget)
        self.tabWidget.addTab(self.autosaveScrollArea, "Autosaves")

        # USER SAVES
        self.userSavesWidget = QWidget()
        self.userSavesWidgetLayout = QVBoxLayout()
        # Top Buttons --------------------
        self.userButtonsWidget = QWidget()
        self.userButtonsLayout = QHBoxLayout()
        self.renameButton = FlatButton('sources/icons/light-theme/icons8-rename-96.png', self.userButtonsWidget)
        self.loadButton = FlatButton('sources/icons/light-theme/icons8-up-square-96.png', self.userButtonsWidget)
        self.deleteButton = FlatButton('sources/icons/light-theme/icons8-remove-96.png', self.userButtonsWidget)
        self.newButton = FlatButton('sources/icons/light-theme/icons8-add-new-96.png', self.userButtonsWidget)

        self.userButtonsLayout.addWidget(self.newButton)
        self.userButtonsLayout.addWidget(self.renameButton)
        self.userButtonsLayout.addWidget(self.loadButton)
        self.userButtonsLayout.addWidget(self.deleteButton)
        self.userButtonsWidget.setLayout(self.userButtonsLayout)

        # User Saves ---------------------
        self.savesWidget = QWidget()
        self.savesLayout = QVBoxLayout()
        self.savesScrollArea = QScrollArea()
        self.savesScrollArea.setWidgetResizable(True)
        self.savesWidget.setLayout(self.savesLayout)
        self.savesScrollArea.setWidget(self.savesWidget)

        self.userSavesWidgetLayout.addWidget(self.userButtonsWidget)
        self.userSavesWidgetLayout.addWidget(self.savesScrollArea)
        self.userSavesWidget.setLayout(self.userSavesWidgetLayout)
        self.tabWidget.addTab(self.userSavesWidget, "User Saves")

        # BUTTON GROUP
        self.buttonGroup = QButtonGroup()
        self.buttonGroup.buttonClicked.connect(self.onSaveButtonClicked)
        self.userButtons, self.autoButtons = None, None

        # ACCEPT BUTTONS
        buttonLayout = QHBoxLayout()
        # Add three buttons to the button layout
        self.acceptButton = QPushButton("Accept")
        self.applyButton = QPushButton("Apply")
        self.cancelButton = QPushButton("Cancel")
        self.acceptButton.clicked.connect(self.acceptedButtonClicked)
        self.applyButton.clicked.connect(self.appliedButtonClicked)
        self.cancelButton.clicked.connect(self.canceledButtonClicked)
        buttonLayout.addWidget(self.acceptButton)
        buttonLayout.addWidget(self.applyButton)
        buttonLayout.addWidget(self.cancelButton)

        # Main Layout
        mainLayout = QVBoxLayout()
        mainLayout.addLayout(self.topLayout)
        mainLayout.addWidget(self.tabWidget)
        mainLayout.addLayout(buttonLayout)
        self.setLayout(mainLayout)

        self.fillTabs()

    def fillTabs(self):
        # SAVES RECON -----------------------------------------------------
        userItems = os.listdir(self.presetPath)
        userSaves = [item for item in userItems if os.path.isfile(os.path.join(self.presetPath, item))]
        autoItems = os.listdir(self.autosavePath)
        autoSaves = [item for item in autoItems if os.path.isfile(os.path.join(self.autosavePath, item))]
        autoSaves.reverse()
        self.userButtons, self.autoButtons = [], []

        for save in userSaves:
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
            if save == self.currentLayout:
                button.setChecked(True)

        for autoSave in autoSaves:
            modificationTime = os.path.getmtime(os.path.join(self.autosavePath, autoSave))
            modificationTimeFormatted = time.ctime(modificationTime)
            button = TwoLineButton(autoSave, f"Creation Date : {modificationTimeFormatted}")
            button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            self.buttonGroup.addButton(button)
            self.autosaveLayout.addWidget(button)
            button.setCheckable(True)
            if autoSave == self.currentLayout:
                button.setChecked(True)

    def emptyTabs(self):
        pass

    def onSaveButtonClicked(self, button: TwoLineButton):
        # Deselect all buttons except the clicked one
        for otherButton in self.buttonGroup.buttons():
            if otherButton is not button:
                otherButton.setChecked(False)
        self.selectedLayoutLabel.setText(button.topTextLabel.text())
        isUserSave = self.userSavesWidget.isAncestorOf(button)
        if isUserSave:
            print('UserSave')
        else:
            print('not UserSave')

    def acceptedButtonClicked(self):
        self.accepted.emit()
        self.close()

    def appliedButtonClicked(self):
        self.applied.emit()

    def canceledButtonClicked(self):
        self.canceled.emit()
        self.close()


class FlatButton(QPushButton):
    def __init__(self, icon: str, parent=None):
        super().__init__(parent)
        # Set the icon and icon size
        self.setIcon(QIcon(icon))
        self.setIconSize(QSize(25, 25))

        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setStyleSheet('border: none;')
        self.setAutoFillBackground(False)
        self.setFlat(True)

    def setIconSize(self, size):
        super().setIconSize(size)
        self.setFixedSize(size)

    def sizeHint(self):
        return self.iconSize()


class ValueWidget(QWidget):
    def __init__(self, cType, value=''):
        super().__init__()
        self.cType = cType
        self.value = value
        self.valueWidget = None
        self.setLayout(QVBoxLayout())
        self.createValueWidget()

    def createValueWidget(self):
        if self.cType == 'bool':
            self.valueWidget = QComboBox()
            self.valueWidget.addItems(['false', 'true'])
            if self.value not in ['true', 'false']:
                self.value = 'false'
            self.valueWidget.setCurrentIndex(['true', 'false'].index(self.value))

        elif self.cType.startswith('int') or self.cType.startswith('uint'):
            minValue, maxValue = self.getIntRange(self.cType)
            self.valueWidget = QLineEdit()
            if np.iinfo(np.int64).min <= minValue <= np.iinfo(np.int64).max and np.iinfo(
                    np.int64).min <= maxValue <= np.iinfo(np.int64).max:
                if not self.value.isdigit() or not minValue <= int(self.value) <= maxValue:
                    self.value = '0'
                self.valueWidget.setValidator(QIntValidator(minValue, maxValue))
            self.valueWidget.setText(self.value)

        elif self.cType == 'double':
            self.valueWidget = QLineEdit()
            self.valueWidget.setValidator(QDoubleValidator())
            if not self.value or not self.value.replace('.', '').isdigit():
                self.value = '0.0'
            self.valueWidget.setText(self.value)

        elif self.cType == 'float':
            self.valueWidget = QLineEdit()
            self.valueWidget.setValidator(
                QDoubleValidator(-3.4e+38, 3.4e+38, 4, notation=QDoubleValidator.StandardNotation))
            if not self.value or not self.value.replace('.', '').isdigit():
                self.value = '0.0'
            self.valueWidget.setText(self.value)

        elif self.cType == 'char':
            self.valueWidget = QLineEdit()
            self.valueWidget.setMaxLength(1)
            if not self.value or not len(self.value) == 1:
                self.value = ''
            self.valueWidget.setText(self.value)

        elif self.cType == 'bytes':
            self.valueWidget = QLineEdit()
            self.valueWidget.setInputMask('HHHHHHHH')
            if not self.value or not len(self.value) == 8:
                self.value = ''
            self.valueWidget.setText(self.value)

        elif '[' in self.cType:
            self.valueWidget = QPushButton('Add Value')
            self.valueWidget.clicked.connect(self.addValue)
            self.layout().addWidget(self.valueWidget)
        self.layout().addWidget(self.valueWidget)

    def addValue(self):
        # create a new ValueWidget for array elements
        elementType = self.cType[:-2]
        elementWidget = ValueWidget(elementType)
        self.layout().insertWidget(self.layout().count() - 1, elementWidget)

    def changeCType(self, newCType):
        if newCType == self.cType:
            return
        if self.valueWidget:
            self.valueWidget.setParent(None)
            self.valueWidget = None
        self.cType = newCType
        self.createValueWidget()

    def destroy_value(self):
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
