######################## IMPORTS ########################
import json
import os
import dataclasses
from ecom.database import Unit
from ecom.datatypes import TypeInfo, DefaultValueInfo

# ------------------- PyQt Modules -------------------- #
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

# --------------------- Sources ----------------------- #
from sources.common.balloondata import BalloonPackageDatabase


######################## CLASSES ########################
class ConfigurationsWidget(QMainWindow):
    def __init__(self, database: BalloonPackageDatabase):
        super(QMainWindow, self).__init__()
        self.headerWidget = None
        self.configTypeSelector = None
        self.database = database
        self.basicTypes = ['int8_t', 'uint8_t', 'bool', 'int16_t', 'uint16_t',
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
        self.buttonAddConfig = QPushButton('+ ADD CONFIG', self.buttonWidget)
        self.buttonDeleteConfig = QPushButton('', self.buttonWidget)
        self.buttonDeleteConfig.setIcon(QIcon(QPixmap('sources/icons/delete-icon.svg')))
        self.buttonLayout = QHBoxLayout(self.buttonWidget)
        self.buttonLayout.addWidget(self.buttonAddConfig)
        self.buttonLayout.addWidget(self.buttonDeleteConfig)

        self.centralLayout.addWidget(self.buttonWidget)
        self.centralLayout.addWidget(self.scrollArea)
        self.setCentralWidget(self.centralWidget)

        self.buttonAddConfig.clicked.connect(self.addNewConfig)
        self.buttonDeleteConfig.clicked.connect(self.removeSelected)

        self.rowWidgets = {'SELECTION': [], 'CONFIG NAME': [], 'CONFIG TYPE': [],
                           'DEFAULT VALUE': [],  'DESCRIPTION': []}

        self.fillConfigurationsTable()
        self.show()

    def addConfigurationRow(self, name='', configType='int8_t', defaultValue='', description=''):
        newRowCount = len(self.rowWidgets['SELECTION']) + 1
        self.rowWidgets['SELECTION'].append(self.generateCheckBox())
        self.rowWidgets['CONFIG NAME'].append(self.generateLabel(name))
        self.rowWidgets['CONFIG TYPE'].append(self.generateTypePushButton(configType, newRowCount))
        self.rowWidgets['DEFAULT VALUE'].append(self.generateDefaultEdit(configType, defaultValue))
        self.rowWidgets['DESCRIPTION'].append(self.generateLineEdit(description))
        self.tableWidgetLayout.addWidget(self.rowWidgets['SELECTION'][-1], newRowCount, 0, 1, 1)
        self.tableWidgetLayout.addWidget(self.rowWidgets['CONFIG NAME'][-1], newRowCount, 1, 1, 1)
        self.tableWidgetLayout.addWidget(self.rowWidgets['CONFIG TYPE'][-1], newRowCount, 2, 1, 1)
        self.tableWidgetLayout.addWidget(self.rowWidgets['DEFAULT VALUE'][-1], newRowCount, 3, 1, 1)
        self.tableWidgetLayout.addWidget(self.rowWidgets['DESCRIPTION'][-1], newRowCount, 4, 1, 1)

    @staticmethod
    def generateCheckBox():
        checkbox = QCheckBox()
        return checkbox

    @staticmethod
    def generateLabel(textContent):
        label = QLabel()
        label.setText(textContent)
        return label

    def cleanTable(self):
        self.rowWidgets = {'SELECTION': [], 'CONFIG NAME': [], 'CONFIG TYPE': [],
                           'DEFAULT VALUE': [], 'DESCRIPTION': []}

    def removeSelected(self):
        pass

    def generateTypePushButton(self, textContent, i):
        typeButton = QPushButton()
        unitList = [unitName for unitName, unitVariants in self.database.units.items()]
        if textContent not in self.basicTypes and textContent not in unitList:  # Degenerate Type
            typeButton.setStyleSheet('QPushButton {color: red;}')
        typeButton.setText(textContent)
        typeButton.clicked.connect(lambda: self.openAvailableTypes(i))
        return typeButton

    def generateDefaultEdit(self, configType, defaultValue):
        if configType not in self.basicTypes:  # Must be in Units... Hopefully...
            unitList = [unitName for unitName, unitVariants in self.database.units.items()]
            if configType not in unitList:  # Unknown Unit
                return QWidget()
            else:
                configType = self.database.units[configType][0].baseTypeName
        if configType == 'bool':
            comboBox = QComboBox()
            comboBox.addItems(['true', 'false'])
            comboBox.setCurrentIndex(['true', 'false'].index(defaultValue))
            return comboBox
        else:
            lineEdit = QLineEdit()
            lineEdit.setText(str(defaultValue))
            return lineEdit

    @staticmethod
    def generateLineEdit(textContent):
        lineEdit = QLineEdit()
        lineEdit.setText(textContent)
        # lineEdit.textChanged.connect(self.descriptionChanged)
        return lineEdit

    def openAvailableTypes(self, i):
        self.configTypeSelector = ConfigTypeSelector(database=self.database)
        self.configTypeSelector.buttons.accepted.connect(lambda: self.acceptTypeChange(i))
        self.configTypeSelector.buttons.rejected.connect(self.configTypeSelector.close)
        self.configTypeSelector.show()

    def acceptTypeChange(self, i):
        basicSelection = self.configTypeSelector.basicTypesList.selectedItems()
        unitsSelection = self.configTypeSelector.basicTypesList.selectedItems()
        selection = basicSelection + unitsSelection
        print(selection)
        if len(selection) == 0:  # No Selection
            return
        typeName = selection[0]
        self.rowWidgets['CONFIG TYPE'][i].setStyleSheet('')
        self.rowWidgets['CONFIG TYPE'][i].setText(typeName)
        # TODO CHANGE CONFIGURATION IN NATIVE DATABASE
        # TODO CHANGE DEFAULT VALUE WIDGET TYPE BASED ON PYTHON TYPE (BOOL, STRING, FLOAT, INTEGER)
        self.configTypeSelector.close()

    def addNewConfig(self):
        pass

    def fillConfigurationsTable(self):
        ### ADD HEADER ###
        self.headerWidget = QWidget(self.tableWidget)
        self.tableWidgetLayout.addWidget(QWidget(), 0, 0, 1, 1)
        self.tableWidgetLayout.addWidget(self.generateLabel('NAME'), 0, 1, 1, 1)
        self.tableWidgetLayout.addWidget(self.generateLabel('TYPE'), 0, 2, 1, 1)
        self.tableWidgetLayout.addWidget(self.generateLabel('DEFAULT'), 0, 3, 1, 1)
        self.tableWidgetLayout.addWidget(self.generateLabel('DESCRIPTION'), 0, 4, 1, 1)
        ### ADD ROWS ###
        for configuration in self.database.configurations:
            typeName = self.database.getTypeName(configuration.type)
            defaultValue = json.dumps(configuration.defaultValue)
            self.addConfigurationRow(name=configuration.name, configType=typeName,
                                     defaultValue=defaultValue, description=configuration.description)


class ConfigTypeSelector(QWidget):
    def __init__(self, database: BalloonPackageDatabase):
        super(QWidget, self).__init__()
        self.database = database
        self.setWindowTitle('Selecting Type or Unit')
        self.basicTypes = ['int8_t', 'uint8_t', 'bool', 'int16_t', 'uint16_t',
                           'int32_t', 'uint32_t', 'int64_t', 'uint64_t', 'float',
                           'double', 'char', 'bytes']
        self.basicTypesList = QListWidget()
        self.basicTypesLabel = QLabel('Basic Types')
        self.unitsList = QListWidget()
        self.unitsLabel = QLabel('Database Units')

        # General Layout
        layout = QVBoxLayout()
        self.centralWidget = QWidget()
        editorLayout = QGridLayout()
        editorLayout.addWidget(self.basicTypesLabel, 0, 0)
        editorLayout.addWidget(self.basicTypesList, 1, 0)
        editorLayout.addWidget(self.unitsLabel, 0, 1)
        editorLayout.addWidget(self.unitsList, 1, 1)
        self.centralWidget.setLayout(editorLayout)
        layout.addWidget(self.centralWidget)

        # Adding Buttons
        self.buttons = QDialogButtonBox()
        self.buttons.setStandardButtons(QDialogButtonBox.Cancel | QDialogButtonBox.Ok)
        self.buttons.button(QDialogButtonBox.Ok).setText("Apply")
        layout.addWidget(self.buttons)
        self.setLayout(layout)

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
