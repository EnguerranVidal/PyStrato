######################## IMPORTS ########################
import dataclasses
import re

from ecom.database import ConfigurationValueResponseType
from ecom.datatypes import TypeInfo

# ------------------- PyQt Modules -------------------- #
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

# --------------------- Sources ----------------------- #
from sources.common.widgets.Widgets import TypeSelector
from sources.databases.balloondata import BalloonPackageDatabase


######################## CLASSES ########################
class TelecommandEditorWidget(QWidget):
    change = pyqtSignal()

    def __init__(self, database):
        super().__init__()
        self.selectedTelecommand = None
        self.database = database
        self.baseTypesValues = [baseType.value for baseType in TypeInfo.BaseType]
        self.baseTypeNames = [baseType.name for baseType in TypeInfo.BaseType]

        # Telemetry Table
        self.telecommandTable = QTableWidget(self)
        self.telecommandTable.setColumnCount(5)
        self.telecommandTable.setHorizontalHeaderLabels(['Name', '', 'Debug', 'Response', 'Description'])
        self.telecommandTable.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.telecommandTable.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.telecommandTable.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.telecommandTable.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.telecommandTable.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self.populateTelecommandTable()

        # Telemetry Arguments Table
        self.telecommandArgumentsTable = QTableWidget(self)
        self.telecommandArgumentsTable.setColumnCount(4)
        self.telecommandArgumentsTable.setHorizontalHeaderLabels(['Name', 'Type', 'Default', 'Description'])
        self.telecommandArgumentsTable.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.telecommandArgumentsTable.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.telecommandArgumentsTable.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.telecommandArgumentsTable.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)

        # Go Back Button
        self.goBackButton = QPushButton('Go Back to Telecommand Types', self)
        self.goBackButton.clicked.connect(self.switchMode)
        self.goBackButton.hide()  # Initially hide the "Go Back" button

        # Stacked Widget
        self.stackedWidget = QStackedWidget(self)
        self.stackedWidget.addWidget(self.telecommandTable)
        self.stackedWidget.addWidget(self.telecommandArgumentsTable)

        # Layout
        layout = QVBoxLayout(self)
        layout.addWidget(self.goBackButton)
        layout.addWidget(self.stackedWidget)

    def populateTelecommandTable(self):
        self.telecommandTable.setRowCount(0)
        for telecommand in self.database.telecommandTypes:
            responseName = telecommand.response.name if telecommand.response else ''
            self.addTelecommandRow(telecommand.id.name, telecommand.isDebug, responseName, telecommand.description)
        self.telecommandTable.resizeColumnsToContents()
        self.telecommandTable.itemSelectionChanged.connect(self.change.emit)

    def populateTelecommandArgumentsTable(self, telecommand):
        self.telecommandArgumentsTable.setRowCount(0)
        for dataPoint in telecommand.data:
            dataPointType = self.database.getTypeName(dataPoint.type)
            if dataPointType in self.baseTypesValues:
                dataPointType = self.baseTypeNames[self.baseTypesValues.index(dataPointType)]
            self.addArgumentRow(dataPoint.name, dataPointType, dataPoint.description)
        self.telecommandArgumentsTable.resizeColumnsToContents()
        self.telecommandArgumentsTable.itemSelectionChanged.connect(self.change.emit)
        self.change.emit()

    def changingArgumentType(self):
        senderWidget: QPushButton = self.sender()
        baseType = senderWidget.text()
        row = self.telecommandArgumentsTable.indexAt(senderWidget.pos()).row()
        dialog = TypeSelector(self.database, baseType, haveDataTypes=True, telemetryType=self.selectedTelecommand)
        result = dialog.exec_()
        if result == QDialog.Accepted:
            # TODO : Add code for telecommand argument type change
            self.change.emit()

    def switchToArguments(self):
        senderWidget: QPushButton = self.sender()
        row = self.telecommandTable.indexAt(senderWidget.pos()).row()
        self.selectedTelecommand = self.database.telecommandTypes[row]
        self.switchMode()

    def changeDebugState(self):
        senderWidget: QPushButton = self.sender()
        row = self.telecommandTable.indexAt(senderWidget.pos()).row()
        telecommand = dataclasses.replace(self.database.telecommandTypes[row], isDebug=senderWidget.isChecked())
        # TODO : Put telecommand back to where it was
        self.change.emit()

    def changeTelecommandResponse(self):
        senderWidget: QPushButton = self.sender()
        row = self.telecommandTable.indexAt(senderWidget.pos()).row()
        dialog = TelecommandResponseDialog(self.database, row)
        result = dialog.exec_()
        if result == QDialog.Accepted:
            responseName = dialog.nameEdit.text()
            senderWidget.setText(responseName)
            # TODO : Add code for telecommand response change
            self.change.emit()

    def addTelecommandType(self):
        dialog = TelecommandAdditionDialog(self.database)
        result = dialog.exec_()
        if result == QDialog.Accepted:
            name = dialog.nameLineEdit.text()
            self.addTelecommandRow(name, debug=False, responseName='', description='')
            # TODO : Add code to add telecommand to database
            self.change.emit()

    def deleteTelecommandType(self):
        selectedRows = [item.row() for item in self.telecommandTable.selectedItems()]
        if len(selectedRows):
            selectedRows = sorted(list(set(selectedRows)))
            dialog = TelecommandDeletionMessageBox(selectedRows)
            result = dialog.exec_()
            if result == QMessageBox.Yes:
                for row in reversed(selectedRows):
                    self.telecommandTable.removeRow(row)
                    # TODO : Add telecommand deletion
                self.change.emit()

    def addArgumentType(self):
        dialog = TelecommandArgumentAdditionDialog(self.database, self.selectedTelecommand)
        result = dialog.exec_()
        if result == QDialog.Accepted:
            name = dialog.nameLineEdit.text()
            baseTypeName = dialog.baseTypeButton.text()
            self.addArgumentRow(name, baseTypeName, '')
            # TODO : Add code to add argument to current telecommand database
            self.change.emit()

    def deleteArgumentType(self):
        selectedRows = [item.row() for item in self.telecommandArgumentsTable.selectedItems()]
        if len(selectedRows):
            selectedRows = sorted(list(set(selectedRows)))
            dialog = TelecommandArgumentDeletionMessageBox(selectedRows)
            result = dialog.exec_()
            if result == QMessageBox.Yes:
                for row in reversed(selectedRows):
                    self.telecommandArgumentsTable.removeRow(row)
                    # TODO : Add telecommand argument deletion
                self.change.emit()

    def addTelecommandRow(self, name, debug, responseName, description):
        rowPosition = self.telecommandTable.rowCount()
        self.telecommandTable.insertRow(rowPosition)
        nameItem = QTableWidgetItem(name)
        descriptionItem = QTableWidgetItem(description)
        self.telecommandTable.setItem(rowPosition, 0, nameItem)
        self.telecommandTable.setItem(rowPosition, 4, descriptionItem)
        argumentButton = QPushButton('Arguments')
        argumentButton.clicked.connect(self.switchToArguments)
        self.telecommandTable.setCellWidget(rowPosition, 1, argumentButton)
        debugToggle = QPushButton()
        debugToggle.setCheckable(True)
        debugToggle.setChecked(debug)
        debugToggle.clicked.connect(self.changeDebugState)
        self.telecommandTable.setCellWidget(rowPosition, 2, debugToggle)
        responseButton = QPushButton(responseName)
        responseButton.clicked.connect(self.changeTelecommandResponse)
        self.telecommandTable.setCellWidget(rowPosition, 3, responseButton)

    def addArgumentRow(self, name, baseTypeName, description):
        rowPosition = self.telecommandArgumentsTable.rowCount()
        self.telecommandArgumentsTable.insertRow(rowPosition)
        nameItem = QTableWidgetItem(name)
        typeButton = QPushButton(baseTypeName)
        typeButton.clicked.connect(self.changingArgumentType)
        descriptionItem = QTableWidgetItem(description)
        self.telecommandArgumentsTable.setItem(rowPosition, 0, nameItem)
        self.telecommandArgumentsTable.setCellWidget(rowPosition, 1, typeButton)
        self.telecommandArgumentsTable.setItem(rowPosition, 3, descriptionItem)

    def switchMode(self):
        currentWidget = self.stackedWidget.currentWidget()
        if currentWidget == self.telecommandTable:
            self.populateTelecommandArgumentsTable(self.selectedTelecommand)
            self.stackedWidget.setCurrentWidget(self.telecommandArgumentsTable)
            self.goBackButton.show()
        else:
            self.stackedWidget.setCurrentWidget(self.telecommandTable)
            self.goBackButton.hide()
        self.change.emit()


class TelecommandResponseDialog(QDialog):
    def __init__(self, database, telecommandIndex):
        super().__init__()
        self.setWindowTitle('TELECOMMAND RESPONSE EDITING')
        self.setWindowIcon(QIcon('sources/icons/PyStrato.png'))
        self.setModal(True)
        self.database, self.telecommandIndex = database, telecommandIndex
        # RESPONSE INFO
        telecommandType = self.database.telecommandTypes[telecommandIndex]
        if telecommandType.response:
            responseName = telecommandType.response.name
            responseDescription = telecommandType.response.description
            if isinstance(telecommandType.response, ConfigurationValueResponseType):
                responseType = 'config?'
            else:
                responseType = self.database.getTypeName(telecommandType.response.typeInfo)
        else:
            responseName, responseType, responseDescription = '', '', ''
        # ENTRIES & BUTTONS
        self.nameEdit = QLineEdit(responseName)
        self.typeEdit = QLineEdit(responseType)
        self.descriptionEdit = QLineEdit(responseDescription)
        self.okButton = QPushButton('OK')
        self.cancelButton = QPushButton('Cancel')
        self.okButton.clicked.connect(self.accept)
        self.cancelButton.clicked.connect(self.reject)
        # MAIN LAYOUT
        buttonLayout = QHBoxLayout()
        buttonLayout.addWidget(self.okButton)
        buttonLayout.addWidget(self.cancelButton)
        formLayout = QFormLayout()
        formLayout.addRow('Name :', self.nameEdit)
        formLayout.addRow('Type :', self.typeEdit)
        formLayout.addRow('Description :', self.descriptionEdit)
        mainLayout = QVBoxLayout(self)
        mainLayout.addLayout(formLayout)
        mainLayout.addLayout(buttonLayout)
        self.setLayout(mainLayout)


class TelecommandAdditionDialog(QDialog):
    def __init__(self, database):
        super().__init__()
        self.setWindowTitle('Add Telecommand Type')
        self.setWindowIcon(QIcon('sources/icons/PyStrato.png'))
        self.setModal(True)
        self.database = database
        self.telecommandTypeNames = [telecommand.id.name for telecommand in self.database.telecommandTypes]
        # ENTRIES & BUTTONS
        self.nameLabel = QLabel('Name:')
        self.nameLineEdit = QLineEdit()
        self.okButton = QPushButton('OK')
        self.cancelButton = QPushButton('Cancel')
        self.okButton.clicked.connect(self.verifyTelecommandName)
        self.cancelButton.clicked.connect(self.reject)
        # LAYOUT
        buttonLayout = QHBoxLayout()
        buttonLayout.addWidget(self.okButton)
        buttonLayout.addWidget(self.cancelButton)
        layout = QVBoxLayout(self)
        layout.addWidget(self.nameLabel)
        layout.addWidget(self.nameLineEdit)
        layout.addLayout(buttonLayout)
        self.setLayout(layout)

    def verifyTelecommandName(self):
        name = self.nameLineEdit.text()
        if name in self.telecommandTypeNames:
            QMessageBox.warning(self, 'Used Name', 'This telecommand name is already in use.')
        elif len(name) == 0:
            QMessageBox.warning(self, 'No Name Entered', 'No name was entered.')
        else:
            self.accept()


class TelecommandDeletionMessageBox(QMessageBox):
    def __init__(self, selectedRows):
        super().__init__()
        self.setModal(True)
        self.setWindowIcon(QIcon('sources/icons/PyStrato.png'))
        self.setIcon(QMessageBox.Question)
        self.setWindowTitle('Confirmation')
        self.setText(f'You are going to delete {len(selectedRows)} telecommand(s).\n Do you want to proceed?')
        self.addButton(QMessageBox.Yes)
        self.addButton(QMessageBox.No)
        self.setDefaultButton(QMessageBox.No)


class TelecommandArgumentAdditionDialog(QDialog):
    def __init__(self, database, telecommandType):
        super().__init__()
        self.setWindowTitle('Add Telecommand Argument')
        self.setWindowIcon(QIcon('sources/icons/PyStrato.png'))
        self.setModal(True)
        self.database, self.telecommandType = database, telecommandType
        self.baseTypesValues = [baseType.value for baseType in TypeInfo.BaseType]
        self.baseTypeNames = [baseType.name for baseType in TypeInfo.BaseType]
        self.argumentTypeNames = [dataPoint.name for dataPoint in telecommandType.data]
        # ENTRIES & BUTTONS
        self.nameLabel = QLabel('Name:')
        self.nameLineEdit = QLineEdit()
        self.baseTypeLabel = QLabel('Config:')
        self.baseTypeButton = QPushButton(self.baseTypeNames[0])
        self.baseTypeButton.clicked.connect(self.changingType)
        self.okButton = QPushButton('OK')
        self.cancelButton = QPushButton('Cancel')
        self.okButton.clicked.connect(self.verifyArgumentName)
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
        self.setLayout(layout)

    def changingType(self):
        baseType = self.baseTypeButton.text()
        dialog = TypeSelector(self.database, baseType, haveDataTypes=True)
        result = dialog.exec_()
        if result == QDialog.Accepted:
            if dialog.selectionSwitch.currentIndex() == 0:
                newType = dialog.baseTypesWidget.currentText()
            else:
                newType = dialog.unitsList.currentItem().text()
            self.baseTypeButton.setText(newType)

    def verifyArgumentName(self):
        name = self.nameLineEdit.text()
        if name in self.argumentTypeNames:
            QMessageBox.warning(self, 'Used Name', 'This argument name is already in use.')
        elif len(name) == 0:
            QMessageBox.warning(self, 'No Name Entered', 'No name was entered.')
        else:
            self.accept()


class TelecommandArgumentDeletionMessageBox(QMessageBox):
    def __init__(self, selectedRows):
        super().__init__()
        self.setModal(True)
        self.setWindowIcon(QIcon('sources/icons/PyStrato.png'))
        self.setIcon(QMessageBox.Question)
        self.setWindowTitle('Confirmation')
        self.setText(f'You are going to delete {len(selectedRows)} argument(s).\n Do you want to proceed?')
        self.addButton(QMessageBox.Yes)
        self.addButton(QMessageBox.No)
        self.setDefaultButton(QMessageBox.No)