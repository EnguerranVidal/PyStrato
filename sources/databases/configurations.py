######################## IMPORTS ########################
import dataclasses
from ecom.datatypes import TypeInfo

# ------------------- PyQt Modules -------------------- #
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from sources.common.widgets.Widgets import ValueWidget, TypeSelector, SquareIconButton
# --------------------- Sources ----------------------- #
from sources.databases.balloondata import BalloonPackageDatabase, serializeTypedValue


######################## CLASSES ########################
class ConfigsEditorWidget(QWidget):
    def __init__(self, database: BalloonPackageDatabase):
        super().__init__()
        self.database = database
        self.baseTypesValues = [baseType.value for baseType in TypeInfo.BaseType]
        self.baseTypeNames = [baseType.name for baseType in TypeInfo.BaseType]

        # BUTTONS
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.addButton = SquareIconButton('sources/icons/light-theme/icons8-add-96.png', self, flat=True)
        self.deleteButton = SquareIconButton('sources/icons/light-theme/icons8-remove-96.png', self, flat=True)
        self.addButton.setStatusTip('Create a new configuration')
        self.deleteButton.setStatusTip('Delete selected configuration(s)')
        self.addButton.clicked.connect(self.addConfig)
        self.deleteButton.clicked.connect(self.deleteConfig)

        # CONFIG TABLE
        self.configsTable = QTableWidget(self)
        self.configsTable.setColumnCount(4)  # Name, Type, Default Value, Description
        self.configsTable.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.configsTable.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.configsTable.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.configsTable.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.configsTable.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.configsTable.setHorizontalHeaderLabels(['Name', 'Type', 'Default Value', 'Description'])
        self.populateConfigsTable()

        # LAYOUT
        topLayout = QHBoxLayout()
        topLayout.addWidget(self.addButton)
        topLayout.addWidget(self.deleteButton)
        topLayout.addWidget(spacer)
        self.layout = QVBoxLayout(self)
        self.layout.addLayout(topLayout)
        self.layout.addWidget(self.configsTable)

    def populateConfigsTable(self):
        self.configsTable.setRowCount(0)
        for configuration in self.database.configurations:
            baseTypeName = self.database.getTypeName(configuration.type)
            if baseTypeName in self.baseTypesValues:
                baseTypeName = self.baseTypeNames[self.baseTypesValues.index(baseTypeName)]
            self.addRow(name=configuration.name, baseTypeName=baseTypeName,
                        defaultValue=serializeTypedValue(configuration.defaultValue, configuration.type.type),
                        description=configuration.description)
        self.configsTable.itemChanged.connect(lambda item: self.changingConfig(item.row(), item.column(), item.text()))
        self.configsTable.itemSelectionChanged.connect(self.handleSelectionChange)
        self.handleSelectionChange()

    def addRow(self, name, baseTypeName, defaultValue, description=''):
        # CONFIGURATION NAME
        unitNames = [unitName for unitName, unitVariants in self.database.units.items()]
        rowPosition = self.configsTable.rowCount()
        self.configsTable.insertRow(rowPosition)
        nameItem = QTableWidgetItem(name)
        self.configsTable.setItem(rowPosition, 0, nameItem)
        # BASE TYPE BUTTON
        baseTypeButton = QPushButton(baseTypeName)
        if not self.isTypeValid(baseTypeName):
            baseTypeButton.setStyleSheet('QPushButton {color: red;}')
        baseTypeButton.clicked.connect(self.changingType)
        self.configsTable.setCellWidget(rowPosition, 1, baseTypeButton)
        # DEFAULT VALUE ENTRY
        if baseTypeName not in self.baseTypeNames:
            if baseTypeName in unitNames:
                baseTypeUnitValue = self.database.units[baseTypeName][0].baseTypeName
                defaultValueWidget = ValueWidget(cType=baseTypeUnitValue, value=defaultValue)
                defaultValueWidget.valueChanged.connect(self.changingDefaultValue)
            else:
                defaultValueWidget = ValueWidget(cType=baseTypeName, value=defaultValue)
                defaultValueWidget.valueChanged.connect(self.changingDefaultValue)

        else:
            baseTypeValue = self.baseTypesValues[self.baseTypeNames.index(baseTypeName)]
            defaultValueWidget = ValueWidget(cType=baseTypeValue, value=defaultValue)
            defaultValueWidget.valueChanged.connect(self.changingDefaultValue)
        self.configsTable.setCellWidget(rowPosition, 2, defaultValueWidget)
        # CONFIGURATION DESCRIPTION
        descriptionItem = QTableWidgetItem(description)
        self.configsTable.setItem(rowPosition, 3, descriptionItem)

    def changingType(self):
        senderWidget: QPushButton = self.sender()
        baseType = senderWidget.text()
        row = self.configsTable.indexAt(senderWidget.pos()).row()
        dialog = TypeSelector(self.database, baseType)
        result = dialog.exec_()
        if result == QDialog.Accepted:
            if dialog.selectionSwitch.currentIndex() == 0:
                newType = dialog.baseTypesWidget.currentText()
            else:
                newType = dialog.unitsList.currentItem().text()
            # CHANGING TYPE BUTTON SHOWN TEXT
            if not self.isTypeValid(newType):
                senderWidget.setStyleSheet('QPushButton {color: red;}')
            senderWidget.setText(newType)
            # CHANGING TYPE IN DATABASE
            if newType in self.baseTypeNames:
                newType = self.baseTypesValues[self.baseTypeNames.index(newType)]
            typeInfo = self.database.getTypeInfo(newType)
            self.database.configurations[row] = dataclasses.replace(self.database.configurations[row], type=typeInfo)
            # CHANGING DEFAULT VALUE WIDGET
            valueWidget: ValueWidget = self.configsTable.cellWidget(row, 2)
            if newType in [unitName for unitName, unitVariants in self.database.units.items()]:
                newType = self.database.units[newType][0].baseTypeName
            valueWidget.changeCType(newType)
        # TODO : Change code for configuration type change

    def changingConfig(self, row, col, text):
        if col == 0:
            self.database.configurations[row] = dataclasses.replace(self.database.configurations[row], name=text)
        elif col == 3:
            self.database.configurations[row] = dataclasses.replace(self.database.configurations[row], description=text)
        # TODO : Change code for configuration name and description change

    def changingDefaultValue(self, valueData):
        senderWidget: ValueWidget = self.sender()
        row = self.configsTable.indexAt(senderWidget.pos()).row()
        cType, value = valueData
        configuration = self.database.configurations[row]
        if cType == 'bool':
            defaultValue = senderWidget.valueWidget.currentText() == 'true'
        elif cType in self.baseTypesValues:
            defaultValue = configuration.type.type(senderWidget.valueWidget.text())
        else:
            raise ValueError("Value not in regular C-Types")
        self.database.configurations[row] = dataclasses.replace(configuration, defaultValue=defaultValue)
        # TODO : Change code for configuration default value change

    def handleSelectionChange(self):
        selectedItems = self.configsTable.selectedItems()
        self.deleteButton.setEnabled(bool(selectedItems))

    def addConfig(self):
        dialog = ConfigAdditionDialog(self.database)
        result = dialog.exec_()
        if result == QDialog.Accepted:
            configName, configType = dialog.nameLineEdit.text(), dialog.baseTypeButton.text()
            print(configName, configType)
            # TODO : Add configuration addition

    def deleteConfig(self):
        selectedRows = [item.row() for item in self.configsTable.selectedItems()]
        if len(selectedRows):
            selectedRows = sorted(list(set(selectedRows)))
            dialog = ConfigDeletionDialog(selectedRows)
            result = dialog.exec_()
            if result == QMessageBox.Yes:
                for row in reversed(selectedRows):
                    configName = list(self.database.units.keys())[row]
                    print(configName)
                    return
                    # TODO : Add configuration deletion
                    #self.database.configurations.pop(configName)
                    #self.unitsTable.removeRow(row)

    def isTypeValid(self, baseTypeName):
        unitNames = [unitName for unitName, unitVariants in self.database.units.items()]
        acceptedTypes = self.baseTypeNames + self.baseTypesValues + unitNames + self.database.getSharedDataTypes()
        return baseTypeName in acceptedTypes

    def validateConfigurations(self):
        for row, configuration in enumerate(self.database.configurations):
            baseTypeName = self.database.getTypeName(configuration.type)
            if baseTypeName in self.baseTypesValues:
                baseTypeName = self.baseTypeNames[self.baseTypesValues.index(baseTypeName)]
            if not self.isTypeValid(baseTypeName):
                self.configsTable.cellWidget(row, 1).setStyleSheet('QPushButton {color: red;}')
            else:
                self.configsTable.cellWidget(row, 1).setStyleSheet('QPushButton {color: black;}')


class ConfigAdditionDialog(QDialog):
    def __init__(self, database):
        super().__init__()
        self.setWindowTitle('Add Configuration')
        self.baseTypesValues = [baseType.value for baseType in TypeInfo.BaseType]
        self.baseTypeNames = [baseType.name for baseType in TypeInfo.BaseType]
        self.database = database
        self.unusableNames = []
        # ENTRIES & BUTTONS
        self.nameLabel = QLabel('Name:')
        self.nameLineEdit = QLineEdit()
        self.nameLineEdit.textChanged.connect(self.updateOkButtonState)
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
        gridLayout.addWidget(self.unitTypeLabel, 1, 0)
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

    def updateOkButtonState(self):
        configName = self.nameLineEdit.text()
        validNewUnitName = bool(configName) and configName not in self.unusableNames
        self.okButton.setEnabled(validNewUnitName)


class ConfigDeletionDialog(QMessageBox):
    def __init__(self, selectedRows):
        super().__init__()
        self.setIcon(QMessageBox.Question)
        self.setWindowTitle('Confirmation')
        self.setText(f'You are going to delete {len(selectedRows)} configuration(s).\n Do you want to proceed?')
        self.addButton(QMessageBox.Yes)
        self.addButton(QMessageBox.No)
        self.setDefaultButton(QMessageBox.No)
