######################## IMPORTS ########################
import dataclasses
import re

from ecom.datatypes import TypeInfo

# ------------------- PyQt Modules -------------------- #
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from sources.common.widgets.Widgets import ValueWidget, TypeSelector
# --------------------- Sources ----------------------- #
from sources.databases.balloondata import BalloonPackageDatabase


######################## CLASSES ########################
class ConstantEditorWidget(QWidget):
    change = pyqtSignal()

    def __init__(self, database):
        super().__init__()
        self.database = database
        self.baseTypesValues = [baseType.value for baseType in TypeInfo.BaseType]
        self.baseTypeNames = [baseType.name for baseType in TypeInfo.BaseType]

        # Constants Table
        self.constantsTable = QTableWidget(self)
        self.constantsTable.setColumnCount(4)
        self.constantsTable.setHorizontalHeaderLabels(['Name', 'Value', 'Type', 'Description'])
        self.constantsTable.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.constantsTable.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.constantsTable.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.constantsTable.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.constantsTable.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.populateConstantsTable()

        # Layout
        layout = QVBoxLayout(self)
        layout.addWidget(self.constantsTable)
        self.setLayout(layout)

    def populateConstantsTable(self):
        autogeneratedConstantNames = ['NUM_CONFIGURATIONS', 'DEFAULT_CONFIGURATION', 'MAX_TELECOMMAND_DATA_SIZE',
                                      'MAX_TELECOMMAND_RESPONSE_SIZE', 'MAX_CONFIG_VALUE_SIZE']
        defaultConstantNames = ['SYNC_BYTE_1', 'SYNC_BYTE_2']
        self.constantsTable.setRowCount(0)
        for constantName, constant in self.database.constants.items():
            if constantName not in autogeneratedConstantNames:
                disableEdit = constantName in defaultConstantNames
                baseTypeName = constant.type.baseTypeName
                if baseTypeName in self.baseTypesValues:
                    baseTypeName = self.baseTypeNames[self.baseTypesValues.index(baseTypeName)]
                self.addConstantRow(constant.name, str(constant.value), baseTypeName, constant.description, disableEdit)
        self.constantsTable.itemChanged.connect(lambda item: self.changingConstant(item.row(), item.column(), item.text()))
        self.constantsTable.itemSelectionChanged.connect(self.change.emit)

    def addConstantRow(self, name, defaultValue, baseTypeName, description, disableEdit=False):
        unitNames = [unitName for unitName, unitVariants in self.database.units.items()]
        rowPosition = self.constantsTable.rowCount()
        self.constantsTable.insertRow(rowPosition)
        # CONSTANT NAME
        if disableEdit:
            nameWidget = QLabel(name)
            self.constantsTable.setCellWidget(rowPosition, 0, nameWidget)
        else:
            nameItem = QTableWidgetItem(name)
            self.constantsTable.setItem(rowPosition, 0, nameItem)
        # VALUE ENTRY
        matchingArrayFormat = re.search(r'(.*?)\[(.*?)\]', baseTypeName)
        if matchingArrayFormat:
            baseTypeName, arraySize = matchingArrayFormat.group(1), int(matchingArrayFormat.group(2))
        else:
            arraySize = 1
        if baseTypeName not in self.baseTypeNames:
            if baseTypeName in unitNames:
                baseTypeUnitValue = self.database.units[baseTypeName][0].baseTypeName
                valueWidget = ValueWidget(cType=baseTypeUnitValue, value=defaultValue, arraySize=arraySize)
                valueWidget.valueChanged.connect(self.changingValue)
            else:
                valueWidget = ValueWidget(cType=baseTypeName, value=defaultValue, arraySize=arraySize)
                valueWidget.valueChanged.connect(self.changingValue)
        else:
            baseTypeValue = self.baseTypesValues[self.baseTypeNames.index(baseTypeName)]
            valueWidget = ValueWidget(cType=baseTypeValue, value=defaultValue, arraySize=arraySize)
            valueWidget.valueChanged.connect(self.changingValue)
        self.constantsTable.setCellWidget(rowPosition, 1, valueWidget)
        # BASE TYPE BUTTON
        baseTypeButton = QPushButton(baseTypeName)
        if not self.isTypeValid(baseTypeName):
            baseTypeButton.setStyleSheet('QPushButton {color: red;}')
        baseTypeButton.clicked.connect(self.changingConstantType)
        self.constantsTable.setCellWidget(rowPosition, 2, baseTypeButton)
        # CONSTANT DESCRIPTION
        descriptionItem = QTableWidgetItem(description)
        self.constantsTable.setItem(rowPosition, 3, descriptionItem)

    def changingConstantType(self):
        senderWidget: QPushButton = self.sender()
        baseType = senderWidget.text()
        row = self.constantsTable.indexAt(senderWidget.pos()).row()
        dialog = TypeSelector(self.database, baseType)
        result = dialog.exec_()
        if result == QDialog.Accepted:
            selectedType = dialog.selectedType
            constantType = f'{selectedType[0]}[{selectedType[2]}]' if selectedType[1] else f'{selectedType[0]}'
            # TODO : Add constant type changing

    def changingValue(self, valueData):
        senderWidget: ValueWidget = self.sender()
        cType, value = valueData
        row = self.constantsTable.indexAt(senderWidget.pos()).row()
        constantKey = list(self.database.constants.keys())[row]
        constant = self.database.constants[constantKey]
        if cType == 'bool':
            value = senderWidget.valueWidget.currentText() == 'true'
        elif cType in self.baseTypesValues:
            value = constant.type.type(senderWidget.valueWidget.text())
            # TODO : ADD ARRAY VALUE CHANGE HANDLING
        else:
            value = None
            raise ValueError("Value not in regular C-Types")
        print(value)
        # TODO : Add code for constant value change
        self.change.emit()

    def isTypeValid(self, baseTypeName):
        unitNames = [unitName for unitName, unitVariants in self.database.units.items()]
        acceptedTypes = self.baseTypeNames + self.baseTypesValues + unitNames + self.database.getSharedDataTypes()
        matchingArrayFormat = re.search(r'(.*?)\[(.*?)\]', baseTypeName)
        if matchingArrayFormat:
            typeName, arraySize = matchingArrayFormat.group(1), matchingArrayFormat.group(2)
            return typeName in acceptedTypes and arraySize.isdigit()
        else:
            return baseTypeName in acceptedTypes

    def changingConstant(self, row, col, text):
        constantKey = list(self.database.constants.keys())[row]
        if col == 0:
            self.database.constants[constantKey] = dataclasses.replace(self.database.constants[constantKey], name=text)
        elif col == 3:
            self.database.constants[constantKey] = dataclasses.replace(self.database.constants[constantKey], description=text)
        # TODO : Change code for configuration name and description change
        self.change.emit()

    def addConstant(self):
        dialog = ConstantAdditionDialog(self.database)
        result = dialog.exec_()
        if result == QDialog.Accepted:
            configName, configType = dialog.nameLineEdit.text(), dialog.baseTypeButton.text()
            self.addRow(configName, configType, '', '')
            # TODO : Add constant addition
            self.change.emit()

    def deleteConstant(self):
        selectedRows = [item.row() for item in self.constantsTable.selectedItems()]
        if len(selectedRows):
            selectedRows = sorted(list(set(selectedRows)))
            dialog = ConstantDeletionMessageBox(selectedRows)
            result = dialog.exec_()
            if result == QMessageBox.Yes:
                for row in reversed(selectedRows):
                    self.constantsTable.removeRow(row)
                    # TODO : Add constants deletion
                self.change.emit()


class ConstantAdditionDialog(QDialog):
    def __init__(self, database):
        super().__init__()
        self.setWindowTitle('Add Constant')
        self.setModal(True)
        self.setWindowIcon(QIcon('sources/icons/PyStrato.png'))
        self.baseTypesValues = [baseType.value for baseType in TypeInfo.BaseType]
        self.baseTypeNames = [baseType.name for baseType in TypeInfo.BaseType]
        self.database = database
        self.constantNames = list(self.database.constants.keys())
        # ENTRIES & BUTTONS
        self.nameLabel = QLabel('Name:')
        self.nameLineEdit = QLineEdit()
        self.baseTypeLabel = QLabel('Constant:')
        self.baseTypeButton = QPushButton(self.baseTypeNames[0])
        self.baseTypeButton.clicked.connect(self.changingType)
        self.okButton = QPushButton('OK')
        self.okButton.setEnabled(False)
        self.cancelButton = QPushButton('Cancel')
        self.okButton.clicked.connect(self.accept)
        self.cancelButton.clicked.connect(self.reject)

        # LAYOUT
        gridLayout = QGridLayout()
        gridLayout.addWidget(self.nameLabel, 0, 0)
        gridLayout.addWidget(self.nameLineEdit, 0, 1)
        gridLayout.addWidget(self.baseTypeLabel, 1, 0)
        gridLayout.addWidget(self.baseTypeButton, 1, 1)
        buttonLayout = QHBoxLayout()
        buttonLayout.addWidget(self.okButton)
        buttonLayout.addWidget(self.cancelButton)
        layout = QVBoxLayout(self)
        layout.addLayout(gridLayout)
        layout.addLayout(buttonLayout)

    def changingType(self):
        baseType = self.baseTypeButton.text()
        dialog = TypeSelector(self.database, baseType)
        result = dialog.exec_()
        if result == QDialog.Accepted:
            if dialog.selectionSwitch.currentIndex() == 0:
                newType = dialog.baseTypesWidget.currentText()
            else:
                newType = dialog.unitsList.currentItem().text()
            self.baseTypeButton.setText(newType)

    def verifyConstantName(self):
        name = self.nameLineEdit.text()
        if name in self.constantNames:
            QMessageBox.warning(self, 'Invalid Name', 'This constant name \n is already in use.')
        elif len(name) == 0:
            QMessageBox.warning(self, 'No Name Entered', 'No name was entered.')
        else:
            self.accept()


class ConstantDeletionMessageBox(QMessageBox):
    def __init__(self, selectedRows):
        super().__init__()
        self.setModal(True)
        self.setWindowIcon(QIcon('sources/icons/PyStrato.png'))
        self.setIcon(QMessageBox.Question)
        self.setWindowTitle('Confirmation')
        self.setText(f'You are going to delete {len(selectedRows)} constant(s).\n Do you want to proceed?')
        self.addButton(QMessageBox.Yes)
        self.addButton(QMessageBox.No)
        self.setDefaultButton(QMessageBox.No)
