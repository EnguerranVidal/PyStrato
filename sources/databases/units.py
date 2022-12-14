######################## IMPORTS ########################
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
