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
        self.newConfigWindow = None
        self.configTypeSelector = None
        self.database = database
        self.basicTypes = ['int8_t', 'uint8_t', 'bool', 'int16_t', 'uint16_t',
                           'int32_t', 'uint32_t', 'int64_t', 'uint64_t', 'float',
                           'double', 'char', 'bytes']
        self.rowWidgets = {'SELECTION': [], 'CONFIG NAME': [], 'CONFIG TYPE': [],
                           'DEFAULT VALUE': [], 'DESCRIPTION': []}
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
        self.buttonAddConfig.clicked.connect(self.addNewConfig)
        self.buttonDeleteConfig.clicked.connect(self.removeSelected)

        self.centralLayout.addWidget(self.buttonWidget)
        self.centralLayout.addWidget(self.scrollArea)
        self.setCentralWidget(self.centralWidget)
        self.fillTable()
        self.show()

    def addConfigurationRow(self, name='', configType='int8_t', defaultValue='', description=''):
        newRowCount = len(self.rowWidgets['SELECTION']) + 1
        self.rowWidgets['SELECTION'].append(self.generateCheckBox())
        self.rowWidgets['CONFIG NAME'].append(self.generateLabel(name))
        self.rowWidgets['CONFIG TYPE'].append(self.generateTypePushButton(configType, newRowCount - 1))
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
        for i in reversed(range(1, self.tableWidgetLayout.count())):
            self.tableWidgetLayout.itemAt(i).widget().setParent(None)
        self.rowWidgets = {'SELECTION': [], 'CONFIG NAME': [], 'CONFIG TYPE': [],
                           'DEFAULT VALUE': [], 'DESCRIPTION': []}

    def removeSelected(self):
        # Retrieving selected units for removal
        states = [checkbox.isChecked() for checkbox in self.rowWidgets['SELECTION']]
        configIndices = [i for i in range(len(states)) if states[i]]
        if len(configIndices) != 0:
            # Removing selected units
            configIndices.reverse()
            for i in configIndices:
                self.database.configurations.pop(i)
            # Refreshing Table
            self.cleanTable()
            self.fillTable()

    def generateTypePushButton(self, textContent, i):
        typeButton = QPushButton(self.tableWidget)
        unitList = [unitName for unitName, unitVariants in self.database.units.items()]
        if textContent not in self.basicTypes and textContent not in unitList:  # Degenerate Type
            typeButton.setStyleSheet('QPushButton {color: red;}')
        typeButton.setText(textContent)
        typeButton.clicked.connect(lambda: self.openAvailableTypes(i))
        return typeButton

    def generateDefaultEdit(self, configType='int8_t', defaultValue=''):
        intTypes = ['int8_t', 'uint8_t', 'int16_t', 'uint16_t', 'int32_t', 'uint32_t', 'int64_t', 'uint64_t']
        floatTypes = ['float', 'double']
        if configType not in self.basicTypes:  # Must be in Units... Hopefully...
            unitList = [unitName for unitName, unitVariants in self.database.units.items()]
            if configType not in unitList:  # Unknown Unit
                return QWidget(self.tableWidget)
            else:
                configType = self.database.units[configType][0].baseTypeName
        if configType == 'bool':
            comboBox = QComboBox(self.tableWidget)
            comboBox.addItems(['true', 'false'])
            if defaultValue in ['true', 'false']:
                comboBox.setCurrentIndex(['true', 'false'].index(defaultValue))
            else:
                comboBox.setCurrentIndex(0)
            return comboBox
        else:
            lineEdit = QLineEdit(self.tableWidget)
            lineEdit.setText(str(defaultValue))
            if configType in intTypes:
                onlyInt = QIntValidator()
                lineEdit.setValidator(onlyInt)
            elif configType in floatTypes:
                onlyFloat = QDoubleValidator()
                locale = QLocale(QLocale.English, QLocale.UnitedStates)
                onlyFloat.setLocale(locale)
                onlyFloat.setNotation(QDoubleValidator.StandardNotation)
                lineEdit.setValidator(onlyFloat)
            return lineEdit

    def generateLineEdit(self, textContent):
        lineEdit = QLineEdit(self.tableWidget)
        lineEdit.setText(textContent)
        lineEdit.textChanged.connect(self.descriptionChanged)
        return lineEdit

    def openAvailableTypes(self, i):
        configType = self.rowWidgets['CONFIG TYPE'][i].text()
        self.configTypeSelector = ConfigTypeSelector(configType, database=self.database)
        self.configTypeSelector.buttons.accepted.connect(lambda: self.acceptTypeChange(i))
        self.configTypeSelector.buttons.rejected.connect(self.configTypeSelector.close)
        self.configTypeSelector.show()

    def acceptTypeChange(self, i):
        typeName = self.configTypeSelector.selectedLabel.text()
        self.rowWidgets['CONFIG TYPE'][i].setStyleSheet('')
        self.rowWidgets['CONFIG TYPE'][i].setText(typeName)
        # TODO CHANGE CONFIGURATION IN NATIVE DATABASE

        self.tableWidgetLayout.removeWidget(self.rowWidgets['DEFAULT VALUE'][i])
        self.rowWidgets['DEFAULT VALUE'][i] = self.generateDefaultEdit(typeName, '')
        self.tableWidgetLayout.addWidget(self.rowWidgets['DEFAULT VALUE'][i], i + 1, 3, 1, 1)
        self.configTypeSelector.close()

    def addNewConfig(self):
        self.newConfigWindow = NewConfigWindow(self)
        self.newConfigWindow.buttons.accepted.connect(self.acceptNewConfig)
        self.newConfigWindow.buttons.rejected.connect(self.newConfigWindow.close)
        self.newConfigWindow.show()

    def acceptNewConfig(self):
        name = self.newConfigWindow.nameEdit.text()
        # TODO Add new config in configurations with given name and set parameters
        pass

    def descriptionChanged(self):
        # TODO Change config description by retrieving it from lineedit
        pass

    def fillTable(self):
        ### ADD HEADER ###
        self.tableWidgetLayout.addWidget(self.generateLabel(''), 0, 0, 1, 1)
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
    def __init__(self, configType, database: BalloonPackageDatabase):
        super(QWidget, self).__init__()
        self.database = database
        self.setWindowTitle('Selecting Configuration Type or Unit')
        self.basicTypes = ['int8_t', 'uint8_t', 'bool', 'int16_t', 'uint16_t',
                           'int32_t', 'uint32_t', 'int64_t', 'uint64_t', 'float',
                           'double', 'char', 'bytes']
        self.basicTypesList = QListWidget()
        self.basicTypesLabel = QLabel('Basic Types')
        self.unitsList = QListWidget()
        self.unitsLabel = QLabel('Database Units')
        self.basicTypesList.itemClicked.connect(self.itemClickedBasic)
        self.unitsList.itemClicked.connect(self.itemClickedUnit)

        # General Layout
        centralLayout = QGridLayout()
        centralLayout.addWidget(self.basicTypesLabel, 0, 0)
        centralLayout.addWidget(self.basicTypesList, 1, 0)
        centralLayout.addWidget(self.unitsLabel, 0, 1)
        centralLayout.addWidget(self.unitsList, 1, 1)

        # Selected Type
        self.selectedLabel = QLabel()
        self.selectedLabel.setText(configType)
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

    def itemClickedBasic(self):
        selection = self.basicTypesList.selectedItems()
        self.selectedLabel.setText(selection[0].text())

    def itemClickedUnit(self):
        selection = self.unitsList.selectedItems()
        self.selectedLabel.setText(selection[0].text())


class NewConfigWindow(QDialog):
    def __init__(self, parent: ConfigurationsWidget):
        super().__init__(parent)
        self.setWindowTitle('Add New Configuration')
        # self.setWindowIcon(QIcon('sources/icons/PyGS.jpg'))
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
