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
from sources.common.FileHandling import load_settings, save_settings, load_format, save_format, loadDatabase
from sources.common.balloondata import BalloonPackageDatabase


######################## CLASSES ########################


############################################################################################
class UnitsWidget(QMainWindow):
    def __init__(self, database: BalloonPackageDatabase):
        super(QMainWindow, self).__init__()
        self.newUnitWindow = None
        self.headerWidget = None
        self.database = database
        self.unitTypes = ['int8_t', 'uint8_t', 'bool', 'int16_t', 'uint16_t',
                          'int32_t', 'uint32_t', 'int64_t', 'uint64_t', 'float',
                          'double', 'char', 'bytes']
        self.centralWidget = QWidget(self)
        self.centralLayout = QVBoxLayout(self.centralWidget)

        self.scrollArea = QScrollArea(self.centralWidget)
        self.scrollArea.setWidgetResizable(True)
        self.tableWidget = QWidget()
        self.tableWidget.setGeometry(QRect(0, 0, 780, 539))
        self.tableWidgetLayout = QGridLayout(self.tableWidget)
        self.tableWidgetLayout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
        self.scrollArea.setWidget(self.tableWidget)

        self.buttonWidget = QWidget()
        self.buttonAddUnit = QPushButton('+ ADD UNIT', self.buttonWidget)
        self.buttonDeleteUnit = QPushButton('', self.buttonWidget)
        self.buttonDeleteUnit.setIcon(QIcon(QPixmap('sources/icons/delete-icon.svg')))
        self.buttonLayout = QHBoxLayout(self.buttonWidget)
        self.buttonLayout.addWidget(self.buttonAddUnit)
        self.buttonLayout.addWidget(self.buttonDeleteUnit)

        self.centralLayout.addWidget(self.buttonWidget)
        self.centralLayout.addWidget(self.scrollArea)
        self.setCentralWidget(self.centralWidget)

        self.buttonAddUnit.clicked.connect(self.addNewUnit)
        self.buttonDeleteUnit.clicked.connect(self.removeSelected)

        self.rowWidgets = {'SELECTION': [], 'UNIT NAME': [], 'UNIT TYPE': [], 'DESCRIPTION': []}

        self.fillTable()
        self.show()

    def addUnitRow(self, name='', unitType='int8_t', description=''):
        self.rowWidgets['SELECTION'].append(self.generateCheckBox())
        self.rowWidgets['UNIT NAME'].append(self.generateLabel(name))
        self.rowWidgets['UNIT TYPE'].append(self.generateComboBox(unitType))
        self.rowWidgets['DESCRIPTION'].append(self.generateLineEdit(description))
        rowCount = len(self.rowWidgets['SELECTION'])
        self.tableWidgetLayout.addWidget(self.rowWidgets['SELECTION'][-1], rowCount, 0, 1, 1)
        self.tableWidgetLayout.addWidget(self.rowWidgets['UNIT NAME'][-1], rowCount, 1, 1, 1)
        self.tableWidgetLayout.addWidget(self.rowWidgets['UNIT TYPE'][-1], rowCount, 2, 1, 1)
        self.tableWidgetLayout.addWidget(self.rowWidgets['DESCRIPTION'][-1], rowCount, 3, 1, 1)

    def generateComboBox(self, unitType):
        comboBox = QComboBox()
        comboBox.addItems(self.unitTypes)
        comboBox.setCurrentIndex(self.unitTypes.index(unitType))
        comboBox.currentIndexChanged.connect(self.unitTypeChanged)
        return comboBox

    @staticmethod
    def generateLabel(textContent):
        label = QLabel()
        label.setText(textContent)
        return label

    def generateLineEdit(self, textContent):
        lineEdit = QLineEdit()
        lineEdit.setText(textContent)
        lineEdit.textChanged.connect(self.descriptionChanged)
        return lineEdit

    @staticmethod
    def generateCheckBox():
        checkbox = QCheckBox()
        return checkbox

    def fillTable(self):
        ### ADD HEADER ###
        self.headerWidget = QWidget(self.tableWidget)
        self.tableWidgetLayout.addWidget(QWidget(), 0, 0, 1, 1)
        self.tableWidgetLayout.addWidget(self.generateLabel('NAME'), 0, 1, 1, 1)
        self.tableWidgetLayout.addWidget(self.generateLabel('TYPE'), 0, 2, 1, 1)
        self.tableWidgetLayout.addWidget(self.generateLabel('DESCRIPTION'), 0, 3, 1, 1)
        ### ADD ROWS ###
        for unitName, unitVariants in self.database.units.items():
            unit = unitVariants[0]
            self.addUnitRow(name=unit.name, unitType=unit.baseTypeName, description=unit.description)

    def cleanTable(self):
        self.rowWidgets = {'SELECTION': [], 'UNIT NAME': [], 'UNIT TYPE': [], 'DESCRIPTION': []}

    def removeSelected(self):

        pass

    def addNewUnit(self):
        self.newUnitWindow = NewUnitWindow(self)
        self.newUnitWindow.buttons.accepted.connect(self.acceptNewUnit)
        self.newUnitWindow.buttons.rejected.connect(self.newUnitWindow.close)
        self.newUnitWindow.show()

    def acceptNewUnit(self):
        name = self.newUnitWindow.nameEdit.text()
        if name in list(self.database.units.keys()):
            messageBox = QMessageBox()
            title = "Unit Error"
            message = "This unit name is already used.\n\nCreate a Variant?"
            reply = messageBox.question(self, title, message, messageBox.Yes | messageBox.Cancel, messageBox.Cancel)
            if reply == messageBox.Yes:
                # self.database.units[name].append()
                self.newUnitWindow.close()
                # TODO : Add Variant creation
        else:
            typeName = 'int8_t'
            unitType = TypeInfo(TypeInfo.lookupBaseType(typeName), typeName, typeName)
            self.database.units[name] = [Unit.fromTypeInfo(name, unitType, '')]
            self.addUnitRow(name=name, unitType=typeName, description='')
            self.newUnitWindow.close()

    def descriptionChanged(self):
        for i in range(len(self.rowWidgets['DESCRIPTION'])):
            name = self.rowWidgets['UNIT NAME'][i].text()
            description = self.rowWidgets['DESCRIPTION'][i].text()
            self.database.units[name][0] = dataclasses.replace(self.database.units[name][0], description=description)

    def unitTypeChanged(self):
        intTypes = ['int8_t', 'uint8_t', 'int16_t', 'uint16_t', 'int32_t', 'uint32_t', 'int64_t', 'uint64_t']
        floatTypes = ['float', 'double']
        stringTypes = ['char', 'bytes']
        for i in range(len(self.rowWidgets['DESCRIPTION'])):
            name = self.rowWidgets['UNIT NAME'][i].text()
            unitType = self.rowWidgets['UNIT TYPE'][i].currentText()
            if unitType in intTypes:
                pythonType = int
            elif unitType in floatTypes:
                pythonType = float
            elif unitType in stringTypes:
                pythonType = str
            else:
                pythonType = bool
            self.database.units[name][0] = dataclasses.replace(self.database.units[name][0],
                                                               type=pythonType, baseTypeName=unitType)


class NewUnitWindow(QDialog):
    def __init__(self, parent: UnitsWidget):
        super().__init__(parent)
        self.setWindowTitle('Add New Unit')
        # self.setWindowIcon(QIcon('sources/icons/PyGS.jpg'))
        self.resize(400, 100)
        self.dlgLayout = QVBoxLayout()
        self.formLayout = QFormLayout()
        self.nameEdit = QLineEdit()
        self.formLayout.addRow('Name:', self.nameEdit)
        self.formLayout.addRow('Name:', parent.generateComboBox())
        self.dlgLayout.addLayout(self.formLayout)
        self.buttons = QDialogButtonBox()
        self.buttons.setStandardButtons(QDialogButtonBox.Cancel | QDialogButtonBox.Ok)
        self.dlgLayout.addWidget(self.buttons)
        self.setLayout(self.dlgLayout)


####################################################################################
class PacketTabWidget(QMainWindow):
    def __init__(self, path):
        super(QMainWindow, self).__init__()
        self.currentDirectory = path
        self.formatPath = os.path.join(self.currentDirectory, "databases")
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
                self.setCentralWidget(QWidget(self))
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


class PacketCentralWidget(QWidget):
    def __init__(self):
        super(QWidget, self).__init__()
        self.topWidget = TopCentralPacketWidget()
        self.bottomWidget = ValuePacketWidget()
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.topWidget)
        self.layout.addWidget(self.bottomWidget)
        self.setLayout(self.layout)


class TopCentralPacketWidget(QWidget):
    def __init__(self):
        super(QWidget, self).__init__()
        # Balloon Identifier ---------------------------------------------
        self.balloonIdToggle = Toggle()
        self.balloonIdEdit = QLineEdit()
        self.balloonIdLabel = QLabel()
        # Balloon Internal Clock -----------------------------------------

        # Balloon Packet Identifier --------------------------------------
        self.packetIdToggle = Toggle()
        self.packetIdSlider = QSlider()
        self.packetIdLabel = QLabel()


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
