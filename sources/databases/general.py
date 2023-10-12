######################## IMPORTS ########################
import os
from typing import Optional

# ------------------- PyQt Modules -------------------- #
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

# --------------------- Sources ----------------------- #
from sources.databases.balloondata import BalloonPackageDatabase
from sources.databases.units import UnitsEditorWidget
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

        self.unitsTab = UnitsEditorWidget(database=self.database)
        self.constantsTab = ConstantsWidget(database=self.database)
        self.configsTab = ConfigurationsWidget(database=self.database)
        self.dataTypesTab = QWidget()
        self.telemetriesTab = TelemetriesWidget(database=self.database)
        self.telecommandsTab = TelecommandsWidget(database=self.database)

        self.addTab(self.unitsTab, 'UNITS')
        self.addTab(self.constantsTab, 'CONSTANTS')
        self.addTab(self.configsTab, 'CONFIG')
        self.addTab(self.dataTypesTab, 'DATATYPES')
        self.addTab(self.telemetriesTab, 'TELEMETRIES')
        self.addTab(self.telecommandsTab, 'TELECOMMANDS')


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


