######################## IMPORTS ########################
import os
from typing import Optional

# ------------------- PyQt Modules -------------------- #
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

# --------------------- Sources ----------------------- #
from sources.databases.balloondata import BalloonPackageDatabase

from sources.databases.units import UnitsWidget
from sources.databases.constants import ConstantsWidget
from sources.databases.configurations import ConfigurationsWidget
from sources.databases.telemetries import TelemetriesWidget
from sources.databases.telecommands import TelecommandsWidget


######################## CLASSES ########################
class DatabaseEditor(QTabWidget):
    def __init__(self, database: BalloonPackageDatabase):
        super(QTabWidget, self).__init__()
        self.database = database
        self.setTabPosition(QTabWidget.East)
        # self.setTabShape(QTabWidget.Triangular)

        self.unitsTab = QStackedWidget()
        self.constantsTab = QStackedWidget()
        self.configsTab = QStackedWidget()
        self.dataTypesTab = QStackedWidget()
        self.telemetriesTab = QStackedWidget()
        self.telecommandsTab = QStackedWidget()

        self.plusIcon = QIcon('sources/icons/light-theme/icons8-add-96.png')

        if len(database.units) != 0:
            self.unitsEditor = UnitsWidget(database=self.database)
            self.unitsTab.addWidget(self.unitsEditor)
        else:
            noUnitWidget = QWidget()
            noUnitLabel = QLabel('There is no unit in this database.')
            self.firstUnitButton = QPushButton()
            self.firstUnitButton.setIcon(self.plusIcon)
            self.firstUnitButton.setText('Add Unit')
            self.firstUnitButton.clicked.connect(self.firstUnit)
            noUnitLayout = QVBoxLayout()
            noUnitLayout.addWidget(noUnitLabel)
            noUnitLayout.addWidget(self.firstUnitButton)
            noUnitLayout.setAlignment(Qt.AlignCenter)
            noUnitWidget.setLayout(noUnitLayout)
            self.unitsTab.addWidget(noUnitWidget)

        if len(database.constants) != 0:
            self.constantsEditor = ConstantsWidget(database=self.database)
            self.constantsTab.addWidget(self.constantsEditor)
        else:
            noConstantWidget = QWidget()
            noConstantLabel = QLabel('There is no constant in this database.')
            self.firstConstantButton = QPushButton()
            self.firstConstantButton.setIcon(self.plusIcon)
            self.firstConstantButton.setText('Add Constant')
            self.firstConstantButton.clicked.connect(self.firstConstant)
            noConstantLayout = QVBoxLayout()
            noConstantLayout.addWidget(noConstantLabel)
            noConstantLayout.addWidget(self.firstConstantButton)
            noConstantLayout.setAlignment(Qt.AlignCenter)
            noConstantWidget.setLayout(noConstantLayout)
            self.constantsTab.addWidget(noConstantWidget)

        if len(database.configurations) != 0:
            self.configsEditor = ConfigurationsWidget(database=self.database)
            self.configsTab.addWidget(self.configsEditor)
        else:
            noConfigWidget = QWidget()
            noConfigLabel = QLabel('There is no configuration in this database.')
            self.firstConfigButton = QPushButton()
            self.firstConfigButton.setIcon(self.plusIcon)
            self.firstConfigButton.setText('Add Configuration')
            self.firstConfigButton.clicked.connect(self.firstConfiguration)
            noConfigLayout = QVBoxLayout()
            noConfigLayout.addWidget(noConfigLabel)
            noConfigLayout.addWidget(self.firstConfigButton)
            noConfigLayout.setAlignment(Qt.AlignCenter)
            noConfigWidget.setLayout(noConfigLayout)
            self.configsTab.addWidget(noConfigWidget)

        if len(database.dataTypes) != 0:
            self.dataTypesEditor = QWidget()
            self.dataTypesTab.addWidget(self.dataTypesEditor)
        else:
            noDataTypeWidget = QWidget()
            noDataTypeLabel = QLabel('There is no data type in this database.')
            self.firstDataTypeButton = QPushButton('Add Data Type')
            self.firstDataTypeButton.setIcon(self.plusIcon)
            self.firstDataTypeButton.clicked.connect(self.firstDataType)
            noDataTypeLayout = QVBoxLayout()
            noDataTypeLayout.addWidget(noDataTypeLabel)
            noDataTypeLayout.addWidget(self.firstDataTypeButton)
            noDataTypeLayout.setAlignment(Qt.AlignCenter)
            noDataTypeWidget.setLayout(noDataTypeLayout)
            self.dataTypesTab.addWidget(noDataTypeWidget)

        if len(database.telemetryTypes) != 0:
            self.telemetriesEditor = TelemetriesWidget(database=self.database)
            self.telemetriesTab.addWidget(self.telemetriesEditor)
        else:
            noTelemetryWidget = QWidget()
            noTelemetryLabel = QLabel('There is no telemetry in this database.')
            self.firstTelemetryButton = QPushButton('+ Add Telemetry')
            self.firstTelemetryButton.clicked.connect(self.firstTelemetry)
            noTelemetryLayout = QVBoxLayout()
            noTelemetryLayout.addWidget(noTelemetryLabel)
            noTelemetryLayout.addWidget(self.firstTelemetryButton)
            noTelemetryLayout.setAlignment(Qt.AlignCenter)
            noTelemetryWidget.setLayout(noTelemetryLayout)
            self.telemetriesTab.addWidget(noTelemetryWidget)

        if len(database.telecommandTypes) != 0:
            self.telecommandsEditor = TelecommandsWidget(database=self.database)
            self.telecommandsTab.addWidget(self.telecommandsEditor)
        else:
            noTelecommandWidget = QWidget()
            noTelecommandLabel = QLabel('There is no telecommand in this database.')
            self.firstTelecommandButton = QPushButton('+ Add Telecommand')
            self.firstTelecommandButton.clicked.connect(self.firstTelecommand)
            noTelecommandLayout = QVBoxLayout()
            noTelecommandLayout.addWidget(noTelecommandLabel)
            noTelecommandLayout.addWidget(self.firstTelecommandButton)
            noTelecommandLayout.setAlignment(Qt.AlignCenter)
            noTelecommandWidget.setLayout(noTelecommandLayout)
            self.telecommandsTab.addWidget(noTelecommandWidget)

        self.addTab(self.unitsTab, 'UNITS')
        self.addTab(self.constantsTab, 'CONSTANTS')
        self.addTab(self.configsTab, 'CONFIG')
        self.addTab(self.dataTypesTab, 'DATATYPES')
        self.addTab(self.telemetriesTab, 'TELEMETRIES')
        self.addTab(self.telecommandsTab, 'TELECOMMANDS')

    def firstUnit(self):
        self.unitsEditor = UnitsWidget(database=self.database)
        self.unitsTab.addWidget(self.unitsEditor)

    def firstConstant(self):
        pass

    def firstConfiguration(self):
        self.configsEditor = ConfigurationsWidget(database=self.database)
        self.configsTab.addWidget(self.configsEditor)
        self.configsEditor.addNewConfig()
        self.configsTab.setCurrentIndex(1)

    def firstDataType(self):
        pass

    def firstTelemetry(self):
        pass

    def firstTelecommand(self):
        pass


class PacketTabWidget(QMainWindow):
    def __init__(self, path):
        super(QWidget, self).__init__()
        self.hide()
        self.currentDirectory = path
        self.formatPath = os.path.join(self.currentDirectory, "formats")
        self.databases = {}

        self.databasesTabWidget = QTabWidget()
        self.setCentralWidget(self.databasesTabWidget)

    def newFormat(self, name):
        pass

    def openFormat(self, path):
        database = BalloonPackageDatabase(path)
        name = os.path.basename(path)
        # Creating Tab in Editing Tabs
        self.databases[name] = database
        editor = DatabaseEditor(self.databases[name])
        self.databasesTabWidget.addTab(editor, name)

    def saveFormat(self, path=None):
        pass

    def saveAllFormats(self):
        pass

    @staticmethod
    def _saveDatabase(database: BalloonPackageDatabase, path: Optional[str] = None):
        pass

    def _closeDatabase(self, index: int):
        pass

    def closeFormat(self):
        pass

    def closeAllFormat(self):
        pass


