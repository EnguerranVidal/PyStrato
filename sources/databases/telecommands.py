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
class TelecommandsWidget(QMainWindow):
    def __init__(self, database: BalloonPackageDatabase):
        super(QMainWindow, self).__init__()
        self.newTelecommandWindow = None
        self.database = database

        self.centralWidget = QWidget(self)
        self.centralLayout = QVBoxLayout(self.centralWidget)

        # -------- Arguments Dock Widget and its Properties
        self.argumentsDockWidget = QDockWidget()
        self.selectedTelecommandIndex = None
        self.addDockWidget(Qt.RightDockWidgetArea, self.argumentsDockWidget)
        self.argumentsDockWidget.setFeatures(QDockWidget.DockWidgetClosable)
        self.argumentsDockWidget.hide()

        # -------- Scrollable Area to display Telemetries
        self.scrollArea = QScrollArea(self.centralWidget)
        self.scrollArea.setWidgetResizable(True)
        self.tableWidget = QWidget()
        self.tableWidget.setGeometry(QRect(0, 0, 780, 539))
        self.tableWidgetLayout = QGridLayout(self.tableWidget)
        self.tableWidgetLayout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
        self.scrollArea.setWidget(self.tableWidget)

        self.buttonWidget = QWidget()
        self.buttonAddTelemetry = QPushButton('+ ADD TELEMETRY', self.buttonWidget)
        self.buttonDeleteTelemetry = QPushButton('', self.buttonWidget)
        self.buttonDeleteTelemetry.setIcon(QIcon(QPixmap('sources/icons/light-theme/icons8-remove-96.png')))
        self.buttonLayout = QHBoxLayout(self.buttonWidget)
        self.buttonLayout.addWidget(self.buttonAddTelemetry)
        self.buttonLayout.addWidget(self.buttonDeleteTelemetry)

        self.buttonAddTelemetry.clicked.connect(self.addNewTelemetry)
        self.buttonDeleteTelemetry.clicked.connect(self.removeSelected)

        self.centralLayout.addWidget(self.buttonWidget)
        self.centralLayout.addWidget(self.scrollArea)
        self.setCentralWidget(self.centralWidget)

        self.rowWidgets = {'SELECTION': [], 'NAME': [], 'ARGUMENTS': [], 'DESCRIPTION': []}

        self.show()

    def fillTable(self):
        ### ADD HEADER ###
        self.tableWidgetLayout.addWidget(self.generateLabel(''), 0, 0, 1, 1)
        self.tableWidgetLayout.addWidget(self.generateLabel('NAME'), 0, 1, 1, 1)
        self.tableWidgetLayout.addWidget(self.generateLabel(''), 0, 2, 1, 1)
        self.tableWidgetLayout.addWidget(self.generateLabel('DESCRIPTION'), 0, 3, 1, 1)
        ### ADD ROWS ###
        for telemetryResponseType in self.database.telemetryTypes:
            self.addTelemetryRow(name=telemetryResponseType.id.name, description=telemetryResponseType.id.__doc__)

    def cleanTable(self):
        for i in reversed(range(1, self.tableWidgetLayout.count())):
            self.tableWidgetLayout.itemAt(i).widget().setParent(None)
        self.rowWidgets = {'SELECTION': [], 'NAME': [], 'ARGUMENTS': [], 'DESCRIPTION': []}

    def addTelemetryRow(self, name='', description=''):
        newRowCount = len(self.rowWidgets['SELECTION']) + 1
        self.rowWidgets['SELECTION'].append(self.generateCheckBox())
        self.rowWidgets['NAME'].append(self.generateLabel(name))
        self.rowWidgets['ARGUMENTS'].append(self.generateArgumentButton(newRowCount))
        self.rowWidgets['DESCRIPTION'].append(self.generateLineEdit(description))
        self.tableWidgetLayout.addWidget(self.rowWidgets['SELECTION'][-1], newRowCount, 0, 1, 1)
        self.tableWidgetLayout.addWidget(self.rowWidgets['NAME'][-1], newRowCount, 1, 1, 1)
        self.tableWidgetLayout.addWidget(self.rowWidgets['ARGUMENTS'][-1], newRowCount, 2, 1, 1)
        self.tableWidgetLayout.addWidget(self.rowWidgets['DESCRIPTION'][-1], newRowCount, 3, 1, 1)

    def generateLabel(self, textContent):
        label = QLabel(self.tableWidget)
        label.setText(textContent)
        # label.setFixedHeight(30)
        return label

    def generateArgumentButton(self, i):
        button = QPushButton('', self.tableWidget)
        button.setIcon(QIcon(QPixmap('sources/icons/stack-icon.svg')))
        button.clicked.connect(lambda: self.openTelemetryArguments(i))
        return button

    def generateLineEdit(self, textContent):
        lineEdit = QLineEdit(self.tableWidget)
        lineEdit.setText(textContent)
        lineEdit.textChanged.connect(self.descriptionChanged)
        return lineEdit

    def generateCheckBox(self):
        checkbox = QCheckBox(self.tableWidget)
        return checkbox

    def descriptionChanged(self):
        for i, (descriptionWidget, telemetryItem) in enumerate(
                zip(self.rowWidgets['DESCRIPTION'], self.database.telemetryTypes)):
            description = descriptionWidget.text()
            self.database.telemetryTypes[i] = dataclasses.replace(telemetryItem, description=description)

    def addNewTelemetry(self):
        self.newTelecommandWindow = NewTelecommandWindow(self.database)
        self.newTelecommandWindow.buttons.accepted.connect(self.acceptNewTelecommand)
        self.newTelecommandWindow.buttons.rejected.connect(self.newTelecommandWindow.close)
        self.newTelecommandWindow.show()

    def acceptNewTelecommand(self):
        name = self.newTelecommandWindow.nameEdit.text()
        pass

    def removeSelected(self):
        pass


class NewTelecommandWindow(QDialog):
    def __init__(self, database):
        super().__init__()
        self.database = database
        self.setWindowTitle('Add New Telecommand')
        # self.setWindowIcon(QIcon('sources/icons/PyGS.jpg'))
        self.resize(400, 100)
        self.dlgLayout = QVBoxLayout()
        self.formWidget = QWidget(self)
        self.formLayout = QFormLayout()
        self.nameEdit = QLineEdit()
        self.defaultValueEdit = QLineEdit()
        self.formLayout.addRow('Name:', self.nameEdit)
        self.formWidget.setLayout(self.formLayout)
        self.dlgLayout.addWidget(self.formWidget)
        self.buttons = QDialogButtonBox()
        self.buttons.setStandardButtons(QDialogButtonBox.Cancel | QDialogButtonBox.Ok)
        self.dlgLayout.addWidget(self.buttons)
        self.setLayout(self.dlgLayout)