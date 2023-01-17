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
from sources.displays.graphs import ColorEditor


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

        # Create the QLineEdit and set its placeholder text
        self.lineEdit = QLineEdit()
        self.lineEdit.setPlaceholderText("Enter value here")

        # Create the QPushButton and set its text
        self.button = QPushButton("Select value")
        self.button.clicked.connect(self.openArgumentSelector)

        # Create the QLabel and set its text
        self.label = QLabel("Label:")

        # Create a layout and add the QLineEdit, QPushButton, and QLabel
        valueLayout = QHBoxLayout(self)
        valueLayout.addWidget(self.label)
        valueLayout.addWidget(self.lineEdit)
        valueLayout.addWidget(self.button)

        # Colors (Font & Background)
        colorLayout = QHBoxLayout(self)
        self.fontColor = ColorEditor('Font Color', color='#000000', parent=self)
        self.backgroundColor = ColorEditor('Background Color', color='#FFFFFF', parent=self)
        colorLayout.addWidget(self.fontColor)
        colorLayout.addWidget(self.backgroundColor)

        mainLayout = QVBoxLayout(self)
        mainLayout.addLayout(valueLayout)

        self.setLayout(mainLayout)

    def openArgumentSelector(self):
        curveArgumentSelector = ArgumentSelector(self.currentDir, self)
        curveArgumentSelector.exec_()
        if curveArgumentSelector.selectedArgument is not None:
            self.lineEdit.setText(curveArgumentSelector.selectedArgument)