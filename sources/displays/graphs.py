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
from sources.common.Widgets import BasicDisplay, ArgumentSelector
from sources.common.balloondata import BalloonPackageDatabase


######################## CLASSES ########################
class CustomGraph(BasicDisplay):
    def __init__(self, path, parent=None, backgroundColor='#ffffff'):
        super().__init__(path, parent)
        layout = QVBoxLayout(self)
        self.plotWidget = pg.PlotWidget(self)
        self.plotWidget.setBackground(backgroundColor)
        layout.addWidget(self.plotWidget)

        self.settingsWidget = CustomGraphEditDialog(self.currentDir, self)

        x_values = [1, 2, 3]
        y_values = [8, 5, 10]
        # self.plotWidget.plot(x_values, y_values)

    def applyChanges(self, editWidget):
        backgroundColor = editWidget.backgroundColorFrame.colorLabel.text()
        self.plotWidget.setBackground(backgroundColor)


class CustomGraphEditDialog(QWidget):
    def __init__(self, path, parent: CustomGraph = None):
        super().__init__(parent)
        self.currentDir = path
        # Create the curves Tab Widget
        self.tabWidget = QTabWidget()
        self.tabWidget.addTab(CurveEditor(0, self.currentDir, self), "Tab 1")
        self.tabWidget.addTab(CurveEditor(1, self.currentDir, self), "Tab 2")
        self.tabWidget.setMovable(True)

        # Create a custom color frame widget
        plotItem = parent.plotWidget.getPlotItem()
        viewBox = plotItem.getViewBox()
        color = viewBox.background.brush().color().getRgb()
        r, g, b, a = color
        color = (r / 255, g / 255, b / 255, a / 255)
        color = QColor(*color)
        hexString = color.name()
        self.backgroundColorFrame = ColorEditor('Background Color', color=hexString, parent=self)

        # Add the color frame to the layout
        layout = QVBoxLayout()
        layout.addWidget(self.tabWidget)
        layout.addWidget(self.backgroundColorFrame)
        self.setLayout(layout)


class CurveEditor(QWidget):
    def __init__(self, curveIndex: int, path, parent=None):
        super().__init__(parent)
        self.curveArgumentSelector = None
        self.currentDir = path
        # TODO Finish Curve Editor
        # Retrieving Curve parameters from parent and index

        # Setting editing widgets
        self.lineEditX = QLineEdit()
        self.lineEditY = QLineEdit()
        labelEditX = QLabel()
        labelEditX.setPixmap(QPixmap('sources/icons/light-theme/icons8-x-coordinate-96.png').scaled(25, 25))
        labelEditY = QLabel()
        labelEditY.setPixmap(QPixmap('sources/icons/light-theme/icons8-y-coordinate-96.png').scaled(25, 25))

        selectionButtonPixmap = QPixmap('sources/icons/light-theme/icons8-add-database-96.png').scaled(25, 25)
        self.buttonSelectorX = QPushButton()
        self.buttonSelectorX.setIcon(QIcon(selectionButtonPixmap))
        self.buttonSelectorY = QPushButton()
        self.buttonSelectorY.setIcon(QIcon(selectionButtonPixmap))
        self.buttonSelectorY.clicked.connect(self.openCurveArgumentSelector)

        nameLabel = QLabel('Name: ')
        self.nameEdit = QLineEdit()

        self.colorEditor = ColorEditor('Curve Color', color='#ffffff', parent=self)

        layout = QGridLayout()
        layout.addWidget(nameLabel, 0, 0, 1, 1)
        layout.addWidget(self.nameEdit, 0, 1, 1, 1)
        layout.addWidget(labelEditX, 1, 0)
        layout.addWidget(self.lineEditX, 1, 1)
        layout.addWidget(self.buttonSelectorX, 1, 2)
        layout.addWidget(labelEditY, 2, 0)
        layout.addWidget(self.lineEditY, 2, 1)
        layout.addWidget(self.buttonSelectorY, 2, 2)
        layout.addWidget(self.colorEditor, 3, 0, 1, 3)
        self.setLayout(layout)

    def openCurveArgumentSelector(self):
        self.curveArgumentSelector = ArgumentSelector(self.currentDir, self)
        self.curveArgumentSelector.selected.connect(self.argumentSelected)
        self.curveArgumentSelector.exec_()
    
    def argumentSelected(self):
        self.lineEditY.setText(self.curveArgumentSelector.selectedArgument)


class ColorEditor(QGroupBox):
    def __init__(self, name, color='#FFFFFF', parent=None):
        super().__init__(parent)
        self.setTitle(name)

        # Create a color button widget and set its initial color to the specified color
        self.colorButton = QPushButton()
        self.colorButton.setMinimumSize(QSize(20, 20))
        self.colorButton.setMaximumSize(QSize(20, 20))
        self.colorButton.setStyleSheet(f"background-color: {color};")

        # Create a label to display the hex code of the selected color and set its initial text to the specified color
        self.colorLabel = QLabel(color)
        self.colorButton.clicked.connect(self.changeColor)

        # Add the color button and label to the layout
        layout = QHBoxLayout()
        layout.addWidget(self.colorButton)
        layout.addWidget(self.colorLabel)
        self.setLayout(layout)

    def changeColor(self):
        color = QColorDialog.getColor()
        self.colorButton.setStyleSheet(f"background-color: {color.name()};")
        self.colorLabel.setText(color.name())


class SplitViewGraph(BasicDisplay):
    def __init__(self, parent=None):
        super().__init__(parent)
        # TODO SPLIT VIEW 2D GRAPH


# TODO MULTI-CURVES 2D GRAPH
# TODO 3D GRAPH
