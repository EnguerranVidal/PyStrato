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
        self.plotWidget.setBackground('w')
        layout.addWidget(self.plotWidget)

        self.settingsWidget = CustomGraphEditDialog(self)

        x_values = [1, 2, 3]
        y_values = [8, 5, 10]
        # self.plotWidget.plot(x_values, y_values)

    def applyChanges(self, editWidget):
        backgroundColor = editWidget.backgroundColorFrame.colorLabel.text()
        self.plotWidget.setBackground(backgroundColor)


class CustomGraphEditDialog(QWidget):
    def __init__(self, parent: CustomGraph = None):
        super().__init__(parent)
        # Create the curves Tab Widget
        self.tabWidget = QTabWidget()
        self.tabWidget.addTab(CurveEditor(0, self), "Tab 1")
        self.tabWidget.addTab(CurveEditor(1, self), "Tab 2")
        self.tabWidget.setMovable(True)

        # Create a custom color frame widget
        plotItem = parent.plotWidget.getPlotItem()
        viewBox = plotItem.getViewBox()
        color = viewBox.background.brush().color().getRgb()
        r, g, b, a = color
        color = (r / 255, g / 255, b / 255, a / 255)
        color = QColor(*color)
        hexString = color.name()
        self.backgroundColorFrame = ColorEditor('Background Color', hexString, self)

        # Add the color frame to the layout
        layout = QVBoxLayout()
        layout.addWidget(self.tabWidget)
        layout.addWidget(self.backgroundColorFrame)
        self.setLayout(layout)


class CurveEditor(QWidget):
    def __init__(self, curveIndex: int, parent=None):
        super().__init__(parent)
        self.lineEditX = QLineEdit()
        self.lineEditY = QLineEdit()
        # TODO Finish Curve Editor

        layout = QGridLayout()
        layout.addWidget(QLabel("X:"), 0, 0)
        layout.addWidget(self.lineEditX, 0, 1)
        layout.addWidget(QLabel("Y:"), 1, 0)
        layout.addWidget(self.lineEditY, 1, 1)
        self.setLayout(layout)


class ColorEditor(QFrame):
    def __init__(self, name, color='#FFFFFF', parent=None):
        super().__init__(parent)
        self.name = name

        # Create a color button widget and set its initial color to the specified color
        self.colorButton = QPushButton()
        self.colorButton.setMinimumSize(QSize(20, 20))
        self.colorButton.setMaximumSize(QSize(20, 20))
        self.colorButton.setStyleSheet(f"background-color: {color};")

        # Create a label to display the hex code of the selected color and set its initial text to the specified color
        self.colorLabel = QLabel(color)
        self.colorButton.clicked.connect(self.onClick)

        # Add the color button and label to the layout
        layout = QHBoxLayout()
        layout.addWidget(self.colorButton)
        layout.addWidget(self.colorLabel)
        self.setLayout(layout)

    def onClick(self):
        color = QColorDialog.getColor()
        self.colorButton.setStyleSheet(f"background-color: {color.name()};")
        self.colorLabel.setText(color.name())


class SplitViewGraph(BasicDisplay):
    def __init__(self, parent=None):
        super().__init__(parent)
        # TODO SPLIT VIEW 2D GRAPH



# TODO MULTI-CURVES 2D GRAPH
# TODO 3D GRAPH
