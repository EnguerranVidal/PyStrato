######################## IMPORTS ########################
import os
from typing import Optional
import pyqtgraph as pg

# ------------------- PyQt Modules -------------------- #
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

# --------------------- Sources ----------------------- #
from sources.common.FileHandling import load_settings
from sources.common.balloondata import BalloonPackageDatabase
from sources.common.Widgets import BasicDisplay, ArgumentSelectorWidget


######################## CLASSES ########################
class SingleIndicator(BasicDisplay):
    def __init__(self, path, parent=None):
        super().__init__(path, parent)
        self.settingsWidget = SingleIndicatorEditDialog(self.currentDir, self)

        self.indicatorLabel = QLabel()

    def applyChanges(self, editWidget):
        pass


class GridIndicator(BasicDisplay):
    def __init__(self, path, parent=None):
        super().__init__(path, parent)
        layout = QGridLayout(self)


class SingleIndicatorEditDialog(QWidget):
    def __init__(self, path, parent: SingleIndicator = None):
        super().__init__(parent)
        self.currentDir = path




