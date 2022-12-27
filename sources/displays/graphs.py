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
from sources.common.Widgets import BasicDisplay


######################## CLASSES ########################
class CustomGraph(BasicDisplay):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self.plotWidget = pg.PlotWidget(self)
        layout.addWidget(self.plotWidget)

        x_values = [1, 2, 3]
        y_values = [8, 5, 10]
        self.plotWidget.plot(x_values, y_values)


class SplitViewGraph(BasicDisplay):
    def __init__(self, parent=None):
        super().__init__(parent)


# TODO SPLIT VIEW 2D GRAPH
# TODO MULTI-CURVES 2D GRAPH
# TODO 3D GRAPH
