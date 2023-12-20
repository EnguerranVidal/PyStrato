######################## IMPORTS ########################
# ------------------- PyQt Modules -------------------- #
from PyQt5.QtWidgets import *

# --------------------- Sources ----------------------- #
from sources.common.utilities.FileHandling import loadSettings
from sources.databases.units import DefaultUnitsCatalogue


######################## CLASSES ########################
class BasicDisplay(QWidget):
    def __init__(self, path, parent=None):
        super().__init__(parent)
        self.generalSettings = loadSettings('settings')
        self.catalogue = DefaultUnitsCatalogue()
        self.settingsWidget = QWidget()
        self.currentDir = path
        self.display = None

    def applyChanges(self, editWidget):
        pass

    def updateContent(self, content):
        pass

    def changeTheme(self):
        pass

    @staticmethod
    def getDescription():
        return {'DISPLAY_TYPE': 'BASIC_DISPLAY'}

    def applyDescription(self, description):
        pass
