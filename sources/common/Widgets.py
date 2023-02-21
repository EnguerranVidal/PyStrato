######################## IMPORTS ########################
import os

# ------------------- PyQt Modules -------------------- #
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtCore import Qt
from PyQt5.QtGui import *
import pyqtgraph as pg
from pyqtgraph.dockarea import Dock, DockArea
import pyqtgraph.widgets.RemoteGraphicsView

# --------------------- Sources ----------------------- #
from sources.common.FileHandling import load_settings, save_settings
from sources.common.balloondata import BalloonPackageDatabase


######################## CLASSES ########################
class BasicDisplay(QWidget):
    def __init__(self, path, parent=None):
        super().__init__(parent)
        self.generalSettings = load_settings('settings')
        self.settingsWidget = QWidget()
        self.currentDir = path
        self.display = None

    def applyChanges(self, editWidget):
        pass

    def updateContent(self, content):
        pass


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


class QCustomDockWidget(QDockWidget):
    def __init__(self, string, parent=None):
        super(QCustomDockWidget, self).__init__(parent)
        self.setAllowedAreas(Qt.TopDockWidgetArea | Qt.LeftDockWidgetArea |
                             Qt.BottomDockWidgetArea | Qt.RightDockWidgetArea)
        self.setWindowTitle(string)
        # self.setTitleBarWidget(QWidget())


class QCustomTabWidget(QTabWidget):
    def __init__(self):
        super(QCustomTabWidget, self).__init__()
        self.setTabsClosable(True)
        self.setMovable(True)
        self.tabCloseRequested.connect(self.closeTab)

    def closeTab(self, currentIndex):
        currentQWidget = self.widget(currentIndex)
        currentQWidget.deleteLater()
        self.removeTab(currentIndex)


class NewGraphWindow(QWidget):
    def __init__(self, parent=None, *args):
        super().__init__(parent, *args)
        self.setWindowTitle('Open New Plot Window')
        self.setWindowIcon(QIcon('sources/icons/PyGS.jpg'))
        self.resize(400, 100)
        self.dlgLayout = QVBoxLayout()
        self.formLayout = QFormLayout()
        self.nameEdit = QLineEdit()
        self.formLayout.addRow('Name:', self.nameEdit)
        self.dlgLayout.addLayout(self.formLayout)
        self.buttons = QDialogButtonBox()
        self.buttons.setStandardButtons(QDialogButtonBox.Cancel | QDialogButtonBox.Ok)
        self.dlgLayout.addWidget(self.buttons)
        self.setLayout(self.dlgLayout)


class NewPlotWindow(QWidget):
    def __init__(self, parent=None, *args):
        super().__init__(parent, *args)
        self.setWindowTitle('Add New Plot Instance')
        self.setWindowIcon(QIcon('sources/icons/PyGS.jpg'))
        self.resize(400, 100)
        self.dlgLayout = QVBoxLayout()
        self.formLayout = QFormLayout()
        self.nameEdit = QLineEdit()
        self.formLayout.addRow('Name:', self.nameEdit)
        self.dlgLayout.addLayout(self.formLayout)
        self.buttons = QDialogButtonBox()
        self.buttons.setStandardButtons(QDialogButtonBox.Cancel | QDialogButtonBox.Ok)
        self.dlgLayout.addWidget(self.buttons)
        self.setLayout(self.dlgLayout)


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
        self.nameEdit.textChanged.connect(self.editLineEdits)
        self.dataEdit = QLineEdit()
        self.formatEdit = QLineEdit()
        self.formLayout.addRow('Name:', self.nameEdit)
        self.dlgLayout.addLayout(self.formLayout)
        self.buttons = QDialogButtonBox()
        self.buttons.setStandardButtons(QDialogButtonBox.Cancel | QDialogButtonBox.Ok)
        self.dlgLayout.addWidget(self.buttons)
        self.setLayout(self.dlgLayout)


class HeaderChangeWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Change Header')
        self.setWindowIcon(QIcon('sources/icons/PyGS.jpg'))
        self.resize(400, 100)
        self.dlgLayout = QVBoxLayout()
        self.formLayout = QFormLayout()
        self.headerEdit = QLineEdit()
        self.formLayout.addRow('Header:', self.headerEdit)
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
