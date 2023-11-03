######################## IMPORTS ########################
import dataclasses
from ecom.datatypes import TypeInfo

# ------------------- PyQt Modules -------------------- #
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

# --------------------- Sources ----------------------- #
from sources.common.widgets.Widgets import TypeSelector
from sources.databases.balloondata import BalloonPackageDatabase


######################## CLASSES ########################
class TelemetryEditorWidget(QWidget):
    change = pyqtSignal()

    def __init__(self, database):
        super().__init__()
        self.selectedTelemetry = None
        self.database = database

        # Telemetry Table
        self.telemetryTable = QTableWidget(self)
        self.telemetryTable.setColumnCount(3)  # Added one more column for the "Arguments" button
        self.telemetryTable.setHorizontalHeaderLabels(['Name', '', 'Description'])
        self.telemetryTable.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.telemetryTable.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.telemetryTable.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.populateTelemetryTable()

        # Telemetry Arguments Table
        self.telemetryArgumentsTable = QTableWidget(self)
        self.telemetryArgumentsTable.setColumnCount(3)
        self.telemetryArgumentsTable.setHorizontalHeaderLabels(['Name', 'Type', 'Description'])
        self.telemetryArgumentsTable.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.telemetryArgumentsTable.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.telemetryArgumentsTable.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)

        # Go Back Button
        self.goBackButton = QPushButton('Go Back to Telemetry Types', self)
        self.goBackButton.clicked.connect(self.switchMode)
        self.goBackButton.hide()  # Initially hide the "Go Back" button

        # Stacked Widget
        self.stackedWidget = QStackedWidget(self)
        self.stackedWidget.addWidget(self.telemetryTable)
        self.stackedWidget.addWidget(self.telemetryArgumentsTable)

        # Layout
        layout = QVBoxLayout(self)
        layout.addWidget(self.goBackButton)
        layout.addWidget(self.stackedWidget)

    def populateTelemetryTable(self):
        self.telemetryTable.setRowCount(0)
        for telemetry in self.database.telemetryTypes:
            rowPosition = self.telemetryTable.rowCount()
            self.telemetryTable.insertRow(rowPosition)
            nameItem = QTableWidgetItem(telemetry.id.name)
            descriptionItem = QTableWidgetItem(getattr(telemetry.id, '__doc__', ''))
            self.telemetryTable.setItem(rowPosition, 0, nameItem)
            self.telemetryTable.setItem(rowPosition, 2, descriptionItem)

            # Add Argument Switch Buttons
            switchButton = QPushButton('Arguments')
            switchButton.clicked.connect(self.switchToArguments)
            self.telemetryTable.setCellWidget(rowPosition, 1, switchButton)
        self.telemetryTable.resizeColumnsToContents()

    def populateTelemetryArgumentsTable(self, telemetry):
        self.telemetryArgumentsTable.setRowCount(0)
        for dataPoint in telemetry.data:
            rowPosition = self.telemetryArgumentsTable.rowCount()
            self.telemetryArgumentsTable.insertRow(rowPosition)
            dataPointType = self.database.getTypeName(dataPoint.type)
            nameItem = QTableWidgetItem(dataPoint.name)
            typeButton = QPushButton(dataPointType)
            typeButton.clicked.connect(self.changingArgumentType)
            descriptionItem = QTableWidgetItem(dataPoint.description)

            self.telemetryArgumentsTable.setItem(rowPosition, 0, nameItem)
            self.telemetryArgumentsTable.setCellWidget(rowPosition, 1, typeButton)
            self.telemetryArgumentsTable.setItem(rowPosition, 2, descriptionItem)
        self.telemetryArgumentsTable.resizeColumnsToContents()
        self.change.emit()

    def changingArgumentType(self):
        senderWidget: QPushButton = self.sender()
        baseType = senderWidget.text()
        row = self.telemetryArgumentsTable.indexAt(senderWidget.pos()).row()
        dialog = TypeSelector(self.database, baseType, haveDataTypes=True, telemetryTypeName=self.selectedTelemetry.id.name)
        result = dialog.exec_()
        if result == QDialog.Accepted:
            # TODO : Add code for configuration type change
            self.change.emit()

    def addTelemetryRow(self, name, description=''):
        rowPosition = self.telemetryTable.rowCount()
        self.telemetryTable.insertRow(rowPosition)
        nameItem = QTableWidgetItem(name)
        descriptionItem = QTableWidgetItem(description)
        self.telemetryTable.setItem(rowPosition, 0, nameItem)
        self.telemetryTable.setItem(rowPosition, 1, descriptionItem)

    def switchMode(self):
        currentWidget = self.stackedWidget.currentWidget()
        if currentWidget == self.telemetryTable:
            self.populateTelemetryArgumentsTable(self.selectedTelemetry)
            self.stackedWidget.setCurrentWidget(self.telemetryArgumentsTable)
            self.goBackButton.show()
        else:
            self.stackedWidget.setCurrentWidget(self.telemetryTable)
            self.goBackButton.hide()
        self.change.emit()

    def switchToArguments(self):
        senderWidget: QPushButton = self.sender()
        row = self.telemetryTable.indexAt(senderWidget.pos()).row()
        self.selectedTelemetry = self.database.telemetryTypes[row]
        print(self.selectedTelemetry.id.name)
        self.switchMode()


class TelemetryAdditionDialog(QDialog):
    def __init__(self, database):
        super().__init__()
        self.setWindowTitle('Add Telemetry Type')
        self.setWindowIcon(QIcon('sources/icons/PyStrato.png'))
        self.setModal(True)
        self.database = database
        self.telemetryTypeNames = [telemetry.id.name for telemetry in self.database.telemetryTypes]
        # ENTRIES & BUTTONS
        self.nameLabel = QLabel('Name:')
        self.nameLineEdit = QLineEdit()
        self.okButton = QPushButton('OK')
        self.cancelButton = QPushButton('Cancel')
        self.okButton.clicked.connect(self.verifyTelemetryName)
        self.cancelButton.clicked.connect(self.reject)
        # LAYOUT
        buttonLayout = QHBoxLayout()
        buttonLayout.addWidget(self.okButton)
        buttonLayout.addWidget(self.cancelButton)
        layout = QVBoxLayout(self)
        layout.addLayout(self.nameLabel)
        layout.addLayout(self.nameLineEdit)
        layout.addLayout(buttonLayout)
        self.setLayout(layout)

    def verifyTelemetryName(self):
        name = self.nameLineEdit.text()
        if name in self.telemetryTypeNames:
            QMessageBox.warning(self, 'Used Name', 'This telemetry name is already in use.')
        elif len(name) == 0:
            QMessageBox.warning(self, 'No Name Entered', 'No name was entered.')
        else:
            self.accept()


class TelemetryDeletionMessageBox(QMessageBox):
    def __init__(self, selectedRows):
        super().__init__()
        self.setModal(True)
        self.setWindowIcon(QIcon('sources/icons/PyStrato.png'))
        self.setIcon(QMessageBox.Question)
        self.setWindowTitle('Confirmation')
        self.setText(f'You are going to delete {len(selectedRows)} telemetry(s).\n Do you want to proceed?')
        self.addButton(QMessageBox.Yes)
        self.addButton(QMessageBox.No)
        self.setDefaultButton(QMessageBox.No)


class TelemetryArgumentAdditionDialog(QDialog):
    def __init__(self, database, telemetryType):
        super().__init__()
        self.setWindowTitle('Add Telemetry Argument')
        self.setWindowIcon(QIcon('sources/icons/PyStrato.png'))
        self.setModal(True)
        self.database, self.telemetryType = database, telemetryType
        telemetryTypeIndex = [index for index, telemetry in enumerate(self.database.telemetryTypes) if telemetry.id.name == self.telemetryType]
        self.argumentTypeNames = [dataPoint.name for dataPoint in self.database.telemetryTypes[telemetryTypeIndex[0]].data]
        # ENTRIES & BUTTONS
        self.nameLabel = QLabel('Name:')
        self.nameLineEdit = QLineEdit()
        self.okButton = QPushButton('OK')
        self.cancelButton = QPushButton('Cancel')
        self.okButton.clicked.connect(self.verifyTelemetryName)
        self.cancelButton.clicked.connect(self.reject)
        # LAYOUT
        buttonLayout = QHBoxLayout()
        buttonLayout.addWidget(self.okButton)
        buttonLayout.addWidget(self.cancelButton)
        layout = QVBoxLayout(self)
        layout.addLayout(self.nameLabel)
        layout.addLayout(self.nameLineEdit)
        layout.addLayout(buttonLayout)
        self.setLayout(layout)

    def verifyTelemetryName(self):
        name = self.nameLineEdit.text()
        if name in self.argumentTypeNames:
            QMessageBox.warning(self, 'Used Name', 'This argument name is already in use.')
        elif len(name) == 0:
            QMessageBox.warning(self, 'No Name Entered', 'No name was entered.')
        else:
            self.accept()


class TelemetryArgumentDeletionMessageBox(QMessageBox):
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
