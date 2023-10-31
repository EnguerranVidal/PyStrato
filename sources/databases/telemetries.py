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

            # Add a button to switch to telemetry arguments for this telemetry type
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

    def changingArgumentType(self):
        senderWidget: QPushButton = self.sender()
        baseType = senderWidget.text()
        row = self.telemetryArgumentsTable.indexAt(senderWidget.pos()).row()
        dialog = TypeSelector(self.database, baseType, haveDataTypes=True,
                              telemetryTypeName=self.selectedTelemetry.id.name)
        result = dialog.exec_()
        if result == QDialog.Accepted:
            pass
        # TODO : Change code for configuration type change

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

    def switchToArguments(self):
        senderWidget: QPushButton = self.sender()
        row = self.telemetryTable.indexAt(senderWidget.pos()).row()
        self.selectedTelemetry = self.database.telemetryTypes[row]
        print(self.selectedTelemetry.id.name)
        self.switchMode()
