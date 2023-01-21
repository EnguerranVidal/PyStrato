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
        self.indicatorLabel = QLabel('bruh')
        self.settingsWidget = SingleIndicatorEditDialog(self.currentDir, self)

        gridLayout = QGridLayout()
        gridLayout.addWidget(self.indicatorLabel)
        self.setLayout(gridLayout)

    def applyChanges(self, editWidget):
        backgroundColor = editWidget.backgroundColor.colorLabel.text()
        fontColor = editWidget.fontColor.colorLabel.text()
        font = QFont(editWidget.fontModelComboBox.currentText())
        fontSize = editWidget.fontSizeSpinBox.value()
        font.setPixelSize(fontSize * QFontMetricsF(font).height() / font.pointSizeF())

        self.indicatorLabel.setAutoFillBackground(True)
        self.indicatorLabel.setFont(font)
        self.indicatorLabel.setAutoFillBackground(True)
        self.indicatorLabel.setFont(font)
        self.indicatorLabel.setStyleSheet("background-color: " + backgroundColor + "; color: " + fontColor + ";")
        bgColor = QColor(backgroundColor)

        # Set the background color of the SingleIndicator widget
        palette = self.palette()
        palette.setColor(self.backgroundRole(), bgColor)
        self.setPalette(palette)

        # Text Alignment
        if editWidget.positionLeftButton.isChecked():
            self.indicatorLabel.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        elif editWidget.positionCenterButton.isChecked():
            self.indicatorLabel.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        elif editWidget.positionRightButton.isChecked():
            self.indicatorLabel.setAlignment(Qt.AlignRight | Qt.AlignVCenter)


class GridIndicator(BasicDisplay):
    def __init__(self, path, parent=None):
        super().__init__(path, parent)
        layout = QGridLayout(self)


class SingleIndicatorEditDialog(QWidget):
    def __init__(self, path, parent: SingleIndicator = None):
        super().__init__(parent)
        self.curveArgumentSelector = None
        self.selectedUnit = None
        self.currentDir = path

        # Create the QLineEdit and set its placeholder text
        self.lineEdit = QLineEdit()
        self.lineEdit.setPlaceholderText("Enter value here")

        # Create the QPushButton and set its text
        self.button = QPushButton("Select value")
        self.button.clicked.connect(self.openArgumentSelector)

        # Create the QLabel and set its text
        self.label = QLabel("Value: ")

        # Create a layout and add the QLineEdit, QPushButton, and QLabel
        valueLayout = QHBoxLayout()
        valueLayout.addWidget(self.label)
        valueLayout.addWidget(self.lineEdit)
        valueLayout.addWidget(self.button)

        # Show Unit Checkbox
        self.unitCheckbox = QCheckBox("Show Unit")

        # Get the current font, font size, font color, and background color of the indicatorLabel
        currentFont = parent.indicatorLabel.font()
        currentFontSize = currentFont.pointSize()
        currentFontColor = parent.indicatorLabel.palette().color(QPalette.WindowText)
        currentBackgroundColor = parent.indicatorLabel.palette().color(QPalette.Window)

        # Colors (Font & Background)
        colorLayout = QGridLayout()
        self.fontColor = ColorEditor('Font Color', color=currentFontColor.name())
        self.backgroundColor = ColorEditor('Background Color', color=currentBackgroundColor.name())
        colorLayout.addWidget(self.fontColor, 0, 0)
        colorLayout.addWidget(self.backgroundColor, 0, 1)
        # Create a QSpinBox for selecting font size
        fontSizeLabel = QLabel("Font Size:")
        self.fontSizeSpinBox = QSpinBox()
        self.fontSizeSpinBox.setRange(8, 72)
        self.fontSizeSpinBox.setValue(currentFontSize)
        self.fontSizeSpinBox.setSingleStep(2)

        # --------- Positioning Buttons --------
        self.positionButtonGroup = QButtonGroup(self)
        # LEFT
        self.positionLeftButton = QPushButton()
        self.positionLeftButton.setIcon(QIcon('sources/icons/light-theme/icons8-align-left-96.png'))
        self.positionLeftButton.setIconSize(QSize(20, 20))
        self.positionLeftButton.setCheckable(True)
        # CENTER
        self.positionCenterButton = QPushButton()
        self.positionCenterButton.setIcon(QIcon('sources/icons/light-theme/icons8-align-center-96.png'))
        self.positionCenterButton.setIconSize(QSize(20, 20))
        self.positionCenterButton.setCheckable(True)
        # RIGHT
        self.positionRightButton = QPushButton()
        self.positionRightButton.setIcon(QIcon('sources/icons/light-theme/icons8-align-right-96.png'))
        self.positionRightButton.setIconSize(QSize(20, 20))
        self.positionRightButton.setCheckable(True)
        # Button Group
        self.positionButtonGroup.addButton(self.positionLeftButton)
        self.positionButtonGroup.addButton(self.positionCenterButton)
        self.positionButtonGroup.addButton(self.positionRightButton)
        self.positionButtonGroup.setExclusive(True)
        # Position in Layout
        positionLayout = QHBoxLayout()
        positionLayout.addWidget(self.positionLeftButton)
        positionLayout.addWidget(self.positionCenterButton)
        positionLayout.addWidget(self.positionRightButton)
        # Check Alignment
        alignment = parent.indicatorLabel.alignment()
        if alignment & Qt.AlignLeft:
            self.positionLeftButton.setChecked(True)
        elif alignment & Qt.AlignHCenter:
            self.positionCenterButton.setChecked(True)
        elif alignment & Qt.AlignRight:
            self.positionRightButton.setChecked(True)

        # Create a QFontComboBox for selecting font model
        fontModelLabel = QLabel("Font Model:")
        self.fontModelComboBox = QFontComboBox()
        self.fontModelComboBox.setCurrentFont(currentFont)

        # Add the font size and font model widgets to a layout
        fontLayout = QGridLayout()
        fontLayout.addWidget(fontSizeLabel, 0, 0)
        fontLayout.addWidget(self.fontSizeSpinBox, 0, 1)
        fontLayout.addWidget(fontModelLabel, 1, 0)
        fontLayout.addWidget(self.fontModelComboBox, 1, 1)

        mainLayout = QVBoxLayout()
        mainLayout.addLayout(valueLayout)
        mainLayout.addWidget(self.unitCheckbox)
        mainLayout.addLayout(colorLayout)
        mainLayout.addLayout(positionLayout)
        mainLayout.addLayout(fontLayout)
        self.setLayout(mainLayout)

    def openArgumentSelector(self):
        self.curveArgumentSelector = ArgumentSelector(self.currentDir, self)
        self.curveArgumentSelector.selected.connect(self.on_argument_selected)
        self.curveArgumentSelector.exec_()

    def argumentSelected(self):
        self.selectedUnit = self.curveArgumentSelector.argumentUnit
        if self.selectedUnit is None:
            self.unitCheckbox.setEnabled(False)
            self.unitCheckbox.setChecked(False)
        else:
            self.unitCheckbox.setEnabled(True)
            self.unitCheckbox.setChecked(True)
        self.lineEdit.setText(self.curveArgumentSelector.selectedArgument)
