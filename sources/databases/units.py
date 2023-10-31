######################## IMPORTS ########################
import dataclasses
import os
import csv

from PyQt5.QtGui import QIcon
from ecom.database import Unit
from ecom.datatypes import TypeInfo

# ------------------- PyQt Modules -------------------- #
from PyQt5.QtWidgets import *

from sources.common.widgets.Widgets import SquareIconButton
# --------------------- Sources ----------------------- #


######################## CLASSES ########################
class UnitsEditorWidget(QWidget):
    def __init__(self, database):
        super().__init__()
        self.database = database
        self.baseTypesValues = [baseType.value for baseType in TypeInfo.BaseType]
        self.baseTypeNames = [baseType.name for baseType in TypeInfo.BaseType]

        # BUTTONS
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.addButton = SquareIconButton('sources/icons/light-theme/icons8-add-96.png', self)
        self.deleteButton = SquareIconButton('sources/icons/light-theme/icons8-remove-96.png', self)
        self.addButton.setStatusTip('Create a new unit')
        self.deleteButton.setStatusTip('Delete selected unit(s)')
        self.addButton.clicked.connect(self.addUnit)
        self.deleteButton.clicked.connect(self.deleteUnit)

        # UNIT TABLE
        self.unitsTable = QTableWidget(self)
        self.unitsTable.setColumnCount(3)
        self.unitsTable.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.unitsTable.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.unitsTable.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.unitsTable.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.unitsTable.setHorizontalHeaderLabels(['Name', 'Type', 'Description'])
        self.populateUnitsTable()

        # LAYOUT
        topLayout = QHBoxLayout()
        topLayout.addWidget(self.addButton)
        topLayout.addWidget(self.deleteButton)
        topLayout.addWidget(spacer)
        self.layout = QVBoxLayout(self)
        self.layout.addLayout(topLayout)
        self.layout.addWidget(self.unitsTable)

    def populateUnitsTable(self):
        self.unitsTable.setRowCount(0)
        units = self.database.units.values()
        for unit in units:
            self.addRow(name=unit[0].name, baseType=unit[0].baseTypeName, description=unit[0].description)
        self.unitsTable.itemChanged.connect(lambda item: self.changingNameOrDescription(item.row(), item.column(), item.text()))
        self.unitsTable.itemSelectionChanged.connect(self.handleSelectionChange)
        self.handleSelectionChange()

    def addRow(self, name, baseType, description=''):
        rowPosition = self.unitsTable.rowCount()
        self.unitsTable.insertRow(rowPosition)
        nameItem = QTableWidgetItem(name)
        self.unitsTable.setItem(rowPosition, 0, nameItem)
        baseTypeComboBox = QComboBox()
        baseTypeComboBox.addItems(self.baseTypeNames)
        baseTypeComboBox.setCurrentIndex(self.baseTypesValues.index(baseType))
        baseTypeComboBox.currentTextChanged.connect(lambda text, row=rowPosition: self.changingType(row, text))
        self.unitsTable.setCellWidget(rowPosition, 1, baseTypeComboBox)
        descriptionItem = QTableWidgetItem(description)
        self.unitsTable.setItem(rowPosition, 2, descriptionItem)

    def changingType(self, row, newType):
        unitName = self.unitsTable.item(row, 0).text()
        baseType = self.baseTypesValues[self.baseTypeNames.index(newType)]
        pythonType = TypeInfo.lookupBaseType(baseType).type
        # TODO : Check for unit usage in configs and telecommands
        self.database.units[unitName][0] = dataclasses.replace(self.database.units[unitName][0], type=pythonType, baseTypeName=baseType)

    def changingNameOrDescription(self, row, col, text):
        if col == 0:
            oldUnitName = list(self.database.units.keys())[row]
            self.database.units[text] = self.database.units.pop(oldUnitName)
            # TODO : Check for Unit Name usage
            for j in range(len(self.database.units[text])):
                self.database.units[text][j] = dataclasses.replace(self.database.units[text][j], name=text)
        elif col == 2:
            unitName = list(self.database.units.keys())[row]
            for j in range(len(self.database.units[unitName])):
                self.database.units[unitName][j] = dataclasses.replace(self.database.units[unitName][j], description=text)

    def handleSelectionChange(self):
        selectedItems = self.unitsTable.selectedItems()
        self.deleteButton.setEnabled(bool(selectedItems))

    def addUnit(self):
        dialog = UnitAdditionDialog(self.database)
        result = dialog.exec_()
        if result == QDialog.Accepted:
            unitName, unitType = dialog.nameLineEdit.text(), dialog.unitTypeComboBox.currentText()
            baseType = self.baseTypesValues[self.baseTypeNames.index(unitType)]
            unitTypeInfo = TypeInfo(TypeInfo.lookupBaseType(baseType).type, baseType, baseType)
            self.database.units[unitName] = [Unit.fromTypeInfo(unitName, unitTypeInfo, '')]
            self.addRow(unitName, baseType, description='')

    def deleteUnit(self):
        selectedRows = [item.row() for item in self.unitsTable.selectedItems()]
        if len(selectedRows):
            selectedRows = sorted(list(set(selectedRows)))
            dialog = UnitDeletionDialog(selectedRows)
            result = dialog.exec_()
            if result == QMessageBox.Yes:
                for row in reversed(selectedRows):
                    unitName = list(self.database.units.keys())[row]
                    self.database.units.pop(unitName)
                    self.unitsTable.removeRow(row)


class UnitAdditionDialog(QDialog):
    def __init__(self, database):
        super().__init__()
        self.setWindowTitle('Add Unit')
        self.setWindowIcon(QIcon('sources/icons/PyStrato.png'))
        self.setModal(True)
        self.database = database
        self.unitList = list(self.database.units.keys())
        self.baseTypesValues = [baseType.value for baseType in TypeInfo.BaseType]
        self.baseTypeNames = [baseType.name for baseType in TypeInfo.BaseType]
        self.unusableNames = self.baseTypesValues + self.baseTypeNames + self.unitList
        # ENTRIES & BUTTONS
        self.nameLabel = QLabel('Name:')
        self.nameLineEdit = QLineEdit()
        self.nameLineEdit.textChanged.connect(self.updateOkButtonState)
        self.unitTypeLabel = QLabel('Type:')
        self.unitTypeComboBox = QComboBox()
        self.unitTypeComboBox.addItems([baseType.name for baseType in TypeInfo.BaseType])
        self.okButton = QPushButton('OK')
        self.okButton.setEnabled(False)
        self.cancelButton = QPushButton('Cancel')
        self.okButton.clicked.connect(self.accept)
        self.cancelButton.clicked.connect(self.reject)
        # LAYOUT
        gridLayout = QGridLayout()
        gridLayout.addWidget(self.nameLabel, 0, 0)
        gridLayout.addWidget(self.nameLineEdit, 0, 1)
        gridLayout.addWidget(self.unitTypeLabel, 1, 0)
        gridLayout.addWidget(self.unitTypeComboBox, 1, 1)
        buttonLayout = QHBoxLayout()
        buttonLayout.addWidget(self.okButton)
        buttonLayout.addWidget(self.cancelButton)
        layout = QVBoxLayout(self)
        layout.addLayout(gridLayout)
        layout.addLayout(buttonLayout)
        self.setLayout(layout)

    def updateOkButtonState(self):
        unitName = self.nameLineEdit.text()
        validNewUnitName = bool(unitName) and unitName not in self.unusableNames
        self.okButton.setEnabled(validNewUnitName)


class UnitDeletionDialog(QMessageBox):
    def __init__(self, selectedRows):
        super().__init__()
        self.setModal(True)
        self.setWindowIcon(QIcon('sources/icons/PyStrato.png'))
        self.setIcon(QMessageBox.Question)
        self.setWindowTitle('Confirmation')
        self.setText(f'You are going to delete {len(selectedRows)} unit(s).\n Do you want to proceed?')
        self.addButton(QMessageBox.Yes)
        self.addButton(QMessageBox.No)
        self.setDefaultButton(QMessageBox.No)


class DefaultUnitsCatalogue:
    def __init__(self, path='sources/common/defaultUnits.csv'):
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

