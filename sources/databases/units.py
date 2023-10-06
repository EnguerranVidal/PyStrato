######################## IMPORTS ########################
import dataclasses
import os
import csv

from ecom.database import Unit
from ecom.datatypes import TypeInfo

# ------------------- PyQt Modules -------------------- #
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

# --------------------- Sources ----------------------- #
from sources.databases.balloondata import BalloonPackageDatabase


######################## CLASSES ########################
class UnitsWidget(QMainWindow):
    def __init__(self, database: BalloonPackageDatabase):
        super(QMainWindow, self).__init__()
        self.newUnitWindow = None
        self.headerWidget = None
        self.database = database
        self.baseTypesValues = [baseType.value for baseType in TypeInfo.BaseType]
        self.baseTypeNames = [baseType.name for baseType in TypeInfo.BaseType]
        self.centralWidget = QWidget(self)
        self.centralLayout = QVBoxLayout(self.centralWidget)

        self.scrollArea = QScrollArea(self.centralWidget)
        self.scrollArea.setWidgetResizable(True)

        self.tableWidget = QWidget()
        self.tableWidgetLayout = QGridLayout(self.tableWidget)
        self.tableWidgetLayout.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.tableWidgetLayout.setColumnStretch(0, 0)
        self.scrollArea.setWidget(self.tableWidget)

        self.buttonWidget = QWidget()
        self.buttonAddUnit = QPushButton(self.buttonWidget)
        self.buttonAddUnit.setIcon(QIcon('sources/icons/light-theme/icons8-add-96.png'))
        self.buttonAddUnit.setText('ADD UNIT')
        self.buttonDeleteUnit = QPushButton('', self.buttonWidget)
        self.buttonDeleteUnit.setIcon(QIcon(QPixmap('sources/icons/light-theme/icons8-remove-96.png')))
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

    def addUnitRow(self, name='', unitType=TypeInfo.BaseType.INT8.value, description=''):
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
        comboBox = QComboBox(self.tableWidget)
        comboBox.addItems(self.baseTypesValues)
        comboBox.setCurrentIndex(self.baseTypesValues.index(unitType))
        comboBox.currentIndexChanged.connect(self.unitTypeChanged)
        return comboBox

    def generateLabel(self, textContent):
        label = QLabel(self.tableWidget)
        label.setText(textContent)
        label.setFixedHeight(30)
        return label

    def generateLineEdit(self, textContent):
        lineEdit = QLineEdit(self.tableWidget)
        lineEdit.setText(textContent)
        lineEdit.textChanged.connect(self.descriptionChanged)
        return lineEdit

    def generateCheckBox(self):
        checkbox = QCheckBox(self.tableWidget)
        return checkbox

    def fillTable(self):
        ### ADD HEADER ###
        self.tableWidgetLayout.addWidget(self.generateLabel(''), 0, 0, 1, 1)
        self.tableWidgetLayout.addWidget(self.generateLabel('NAME'), 0, 1, 1, 1)
        self.tableWidgetLayout.addWidget(self.generateLabel('TYPE'), 0, 2, 1, 1)
        self.tableWidgetLayout.addWidget(self.generateLabel('DESCRIPTION'), 0, 3, 1, 1)
        ### ADD ROWS ###
        for unitName, unitVariants in self.database.units.items():
            unit = unitVariants[0]
            self.addUnitRow(name=unit.name, unitType=unit.baseTypeName, description=unit.description)

    def cleanTable(self):
        for i in reversed(range(1, self.tableWidgetLayout.count())):
            self.tableWidgetLayout.itemAt(i).widget().setParent(None)
        self.rowWidgets = {'SELECTION': [], 'UNIT NAME': [], 'UNIT TYPE': [], 'DESCRIPTION': []}

    def removeSelected(self):
        # Retrieving selected units for removal
        states = [checkbox.isChecked() for checkbox in self.rowWidgets['SELECTION']]
        unitNames = list(self.database.units.keys())
        removedUnits = [unitNames[i] for i in range(len(unitNames)) if states[i]]
        if len(removedUnits) != 0:
            # Removing selected units
            for unit in removedUnits:
                self.database.units.pop(unit)
            # Refreshing Table
            self.cleanTable()
            self.fillTable()

    def addNewUnit(self):
        self.newUnitWindow = NewUnitWindow(self)
        self.newUnitWindow.buttons.accepted.connect(self.acceptNewUnit)
        self.newUnitWindow.buttons.rejected.connect(self.newUnitWindow.close)
        self.newUnitWindow.show()

    def acceptNewUnit(self):
        name = self.newUnitWindow.nameEdit.text()
        typeName = self.newUnitWindow.comboBox.currentText()
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
            unitType = TypeInfo(TypeInfo.lookupBaseType(typeName).type, typeName, typeName)
            self.database.units[name] = [Unit.fromTypeInfo(name, unitType, '')]
            self.addUnitRow(name=name, unitType=typeName, description='')
            self.newUnitWindow.close()

    def descriptionChanged(self):
        for i in range(len(self.rowWidgets['DESCRIPTION'])):
            name = self.rowWidgets['UNIT NAME'][i].text()
            description = self.rowWidgets['DESCRIPTION'][i].text()
            for j in range(len(self.database.units[name])):
                self.database.units[name][j] = dataclasses.replace(self.database.units[name][j],
                                                                   description=description)
            self.database.replaceType(self.database.units[name][0].type, name)

    def unitTypeChanged(self):
        for i in range(len(self.rowWidgets['DESCRIPTION'])):
            name = self.rowWidgets['UNIT NAME'][i].text()
            unitType = self.rowWidgets['UNIT TYPE'][i].currentText()
            pythonType = TypeInfo.lookupBaseType(unitType).type
            self.database.units[name][0] = dataclasses.replace(self.database.units[name][0],
                                                               type=pythonType, baseTypeName=unitType)
            self.database.replaceType(self.database.units[name][0].type, name)


class NewUnitWindow(QDialog):
    def __init__(self, parent: UnitsWidget):
        super().__init__(parent)
        self.setWindowTitle('Add New Unit')
        # self.setWindowIcon(QIcon('sources/icons/PyStratoGui.jpg'))
        unitTypes = [baseType.value for baseType in TypeInfo.BaseType]
        self.resize(400, 100)
        self.dlgLayout = QVBoxLayout()
        self.formLayout = QFormLayout()
        self.nameEdit = QLineEdit()
        self.comboBox = QComboBox()
        self.comboBox.addItems(unitTypes)
        self.comboBox.setCurrentIndex(0)
        self.formLayout.addRow('Name:', self.nameEdit)
        self.formLayout.addRow('Type:', self.comboBox)
        self.dlgLayout.addLayout(self.formLayout)
        self.buttons = QDialogButtonBox()
        self.buttons.setStandardButtons(QDialogButtonBox.Cancel | QDialogButtonBox.Ok)
        self.dlgLayout.addWidget(self.buttons)
        self.setLayout(self.dlgLayout)


class DefaultUnitsCatalogue:
    def __init__(self, path='sources//common//defaultUnits.csv'):
        self.csvPath = path
        if not os.path.exists(path):
            with open(path, 'w', encoding='utf-8', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(['Unit Name', 'Symbol', 'Description', 'Physical Value', 'Other Names'])
            self.feedDefaultValues()
        self.units = self.load()

    def load(self, csvPath=None):
        if csvPath is None:
            csvPath = self.csvPath
        units = {}
        with open(csvPath, encoding='utf-8', newline='') as file:
            reader = csv.reader(file)
            next(reader)  # Header Row
            for row in reader:
                unit_name = row[0]
                symbol = row[1]
                description = row[2]
                physical_value = row[3]
                other_names = row[4].split(',') if row[4] else []
                units[unit_name] = (symbol, description, physical_value, other_names)
        return units

    def save(self, units=None, csvPath=None):
        if units is None:
            units = self.units
        if csvPath is None:
            csvPath = self.csvPath
        with open(csvPath, 'w', encoding='utf-8', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['Unit Name', 'Symbol', 'Description', 'Physical Value', 'Other Names'])
            for unit_name, values in units.items():
                symbol, description, physical_value, other_names = values
                other_names_str = ','.join(other_names) if other_names else ''
                writer.writerow([unit_name, symbol, description, physical_value, other_names_str])

    def find(self, unitName):
        # Check in the keys
        if unitName in self.units:
            return self.units[unitName]
        # Search in the other names column
        for unit in self.units.values():
            if unitName in unit[3]:
                return unit
            if unitName == unit[0]:
                return unit
        return None

    def getSymbol(self, unitName):
        unit = self.find(unitName)
        if unit is not None:
            return unit[0]
        else:
            return None

    def feedDefaultValues(self):
        with open(self.csvPath, 'a', encoding='utf-8', newline='') as file:
            writer = csv.writer(file)
            ######## TIME UNITS ########
            writer.writerow(['Second', 's', 'Time', 'Time', 'second, sec, seconds'])
            writer.writerow(['Millisecond', 'ms', 'Time', 'Time', 'millisecond, msec'])
            writer.writerow(['Microsecond', 'us', 'Time', 'Time', 'microsecond, use, us'])
            writer.writerow(['Nanosecond', 'ns', 'Time', 'Time', 'nanosecond, nsec'])
            writer.writerow(['Minute', 'min', 'Time', 'Time', 'minute, Min, minutes'])
            writer.writerow(['Hour', 'h', 'Time', 'Time', 'hour, hours'])
            writer.writerow(['Day', 'd', 'Time', 'Time', 'day, days'])
            writer.writerow(['Week', 'wk', 'Time', 'Time', 'week, weeks'])
            writer.writerow(['Month', 'mo', 'Time', 'Time', 'month, months'])
            writer.writerow(['Year', 'yr', 'Time', 'Time', 'year, years'])
            ######## DISTANCE UNITS ########
            writer.writerow(['Meter', 'm', 'Length', 'Distance', 'meter, meters'])
            writer.writerow(['Kilometer', 'km', 'Length', 'Distance', 'kilometer, kilometers, kmeters'])
            ######## SPEED UNITS ########
            writer.writerow(['Meter per second', 'm/s', 'Speed', 'Speed', 'meter per second, mps'])
            writer.writerow(['Kilometer per hour', 'km/h', 'Speed', 'Speed', 'kilometer per hour, kph'])
            ######## ACCELERATION UNITS ########
            writer.writerow(['Meter per second squared', 'm/s²', 'Acceleration', 'Acceleration', 'meter per second squared, mps2, m/s^2'])
            writer.writerow(['Gravity', 'g', 'Acceleration', 'Acceleration', 'gravity'])
            ######## FORCE UNITS ########
            writer.writerow(['Newton', 'N', 'Force', 'Force', 'newton, newtons'])
            ######## QUANTITY UNITS ########
            writer.writerow(['Mole', 'mol', 'Amount of substance', 'Quantity', 'moles, mole'])
            ######## CONCENTRATION UNITS ########
            writer.writerow(['Parts per million', 'ppm', 'Concentration', 'Concentration', 'parts per million'])
            writer.writerow(['Parts per billion', 'ppb', 'Concentration', 'Concentration', 'parts per billion'])
            writer.writerow(['Percent', '%', 'Concentration', 'Concentration', 'percent'])
            ######## TEMPERATURE UNITS ########
            writer.writerow(['Celsius', '°C', 'Temperature', 'Temperature', 'celsius, C'])
            writer.writerow(['Fahrenheit', '°F', 'Temperature', 'Temperature', 'fahrenheit, F'])
            writer.writerow(['Kelvin', '°K', 'Temperature', 'Temperature', 'kelvin, K'])
            writer.writerow(['Rankine', '°R', 'Temperature', 'Temperature', 'rankine, R'])
            ######## PRESSURE UNITS ########
            writer.writerow(['Pascal', 'Pa', 'Pressure', 'Pressure', 'pascal, pa'])
            writer.writerow(['Bar', 'bar', 'Pressure', 'Pressure', None])
            writer.writerow(['Millibar', 'mbar', 'Pressure', 'Pressure', 'millibar, hectopascal, Hectopascal'])
            writer.writerow(['Pound per square inch', 'psi', 'Pressure', 'Pressure', 'pound per square inch'])
            ######## ANGLE UNITS ########
            writer.writerow(['Degree', 'deg', 'Angle', 'Angle', 'degree, degrees'])
            writer.writerow(['Radian', 'rad', 'Angle', 'Angle', 'radian, radians'])
            ######## ANGULAR SPEED UNITS ########
            writer.writerow(['Degree per second', 'deg/s', 'Angular Speed', 'Angular Speed', 'dps, degree per second'])
            writer.writerow(['Radian per second', 'rad/s', 'Angular Speed', 'Angular Speed', 'rps, radian per second'])
            writer.writerow(['Revolution per minute', 'rpm', 'Angular Speed', 'Angular Speed', 'revolution per minute'])
            ######## LIGHT UNITS ########
            writer.writerow(['Lux', 'lx', 'Illuminance', 'Illuminance', 'lux'])
            writer.writerow(['Foot-candle', 'fc', 'Illuminance', 'Illuminance', 'foot candle, foot-candle'])
            ######## VOLTAGE UNITS ########
            writer.writerow(['Volt', 'V', 'Voltage', 'Voltage', 'volt'])
            writer.writerow(['Millivolt', 'mV', 'Voltage', 'Voltage', 'millivolt'])
            writer.writerow(['Microvolt', 'uV', 'Voltage', 'Voltage', 'microvolt'])
            ######## CURRENT UNITS ########
            writer.writerow(['Ampere', 'A', 'Electric Current', 'Electric Current', 'ampere'])
            writer.writerow(['Milliampere', 'mA', 'Electric Current', 'Electric Current', 'milliampere'])
            writer.writerow(['Microampere', 'uA', 'Electric Current', 'Electric Current', 'microampere'])
            ######## RESISTANCE UNITS ########
            writer.writerow(['Ohm', 'Ω', 'Electric Resistance', 'Electric Resistance', 'ohm'])
            ######## FREQUENCY UNITS ########
            writer.writerow(['Hertz', 'Hz', 'Frequency', 'Frequency', 'hertz'])
            writer.writerow(['Kilohertz', 'kHz', 'Frequency', 'Frequency', 'kilohertz'])
            writer.writerow(['Megahertz', 'MHz', 'Frequency', 'Frequency', 'megahertz'])
            ######## MAGNETIC STRENGTH UNITS ########
            writer.writerow(['Tesla', 'T', 'Magnetic Field Strength', 'Magnetic Field Strength', 'tesla'])
            writer.writerow(['Millitesla', 'mT', 'Magnetic Field Strength', 'Magnetic Field Strength', 'millitesla, milliTesla, mTesla'])
            writer.writerow(['Microtesla', 'uT', 'Magnetic Field Strength', 'Magnetic Field Strength', 'microtesla, microTesla, uTesla'])

