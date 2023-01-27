######################## IMPORTS ########################
import os
from typing import List, Dict, Any, Optional, Generic, Type, Callable, Union
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
        self.hide()

    def openArgumentSelector(self):
        self.curveArgumentSelector = ArgumentSelector(self.currentDir, self)
        self.curveArgumentSelector.selected.connect(self.argumentSelected)
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


############################## GRID INDICATOR ##############################
class GridIndicator(BasicDisplay):
    def __init__(self, path, parent=None):
        super().__init__(path, parent)

        self.labelGridLayout = QGridLayout()
        self.setLayout(self.labelGridLayout)
        self.settingsWidget = GridIndicatorEditDialog(self.currentDir, self)

    def fillGrid(self):
        rows = self.parentWidget.rowSpinBox.value()
        columns = self.parentWidget.columnSpinBox.value()
        while self.grid.count() > 0:
            widget = self.grid.itemAt(0).widget()
            self.grid.removeWidget(widget)
            widget.setParent(None)


class GridIndicatorEditDialog(QWidget):
    def __init__(self, path, parent: GridIndicator = None):
        super().__init__(parent)
        self.currentDir = path
        self.labelEditors = [[None]]  # type: List[List]
        self.columnSpinBox = QSpinBox()
        self.rowSpinBox = QSpinBox()

        # Set the range and default values for the spin boxes
        self.columnSpinBox.setRange(1, 50)
        self.columnSpinBox.setValue(1)
        self.columnSpinBox.setFixedSize(50, 25)

        self.rowSpinBox.setRange(1, 50)
        self.rowSpinBox.setValue(1)
        self.rowSpinBox.setFixedSize(50, 25)

        # Create a horizontal layout for the spin boxes
        self.spinBoxWidget = QWidget()
        spinBoxLayout = QHBoxLayout()
        spinBoxLayout.addWidget(QLabel("Columns:"))
        spinBoxLayout.addWidget(self.columnSpinBox)
        spinBoxLayout.addWidget(QLabel("Rows:"))
        spinBoxLayout.addWidget(self.rowSpinBox)
        self.spinBoxWidget.setLayout(spinBoxLayout)
        self.spinBoxWidget.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        # ------------- CENTRAL WIDGET ------------- #
        self.gridEditor = GridEditor(self)
        self.columnSpinBox.valueChanged.connect(self.gridEditor.updateGrid)
        self.rowSpinBox.valueChanged.connect(self.gridEditor.updateGrid)

        # Main Window
        self.mainWidget = QMainWindow()
        self.mainWidget.setCentralWidget(self.gridEditor)

        # Create the main layout and add the spin box layout
        self.mainLayout = QGridLayout()
        self.mainLayout.addWidget(self.spinBoxWidget, 0, 0, Qt.AlignLeft)
        self.mainLayout.addWidget(self.mainWidget, 1, 0, Qt.AlignCenter)
        self.setLayout(self.mainLayout)

        self.hide()

    def openLabelEditor(self, i: int, j: int):
        self.mainWidget.setCentralWidget(LabelEditor)


class GridEditor(QWidget):
    def __init__(self, parent: GridIndicatorEditDialog = None):
        super().__init__(parent)
        # Create the grid layout
        self.parentWidget = parent
        self.grid = QGridLayout()
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        # Set the grid layout as the widget inside the scroll area
        self.setLayout(self.grid)
        self.updateGrid()

    def updateGrid(self):
        rows = self.parentWidget.rowSpinBox.value()
        columns = self.parentWidget.columnSpinBox.value()
        while self.grid.count() > 0:
            widget = self.grid.itemAt(0).widget()
            self.grid.removeWidget(widget)
            widget.setParent(None)
        for i in range(rows):
            self.grid.setRowStretch(i, 1)
        for i in range(columns):
            self.grid.setColumnStretch(i, 1)
        for row in range(rows):
            for column in range(columns):
                button = QPushButton()
                button.setFixedSize(50, 50)
                self.grid.addWidget(button, row, column)
        self.setFixedSize(columns * 50 + 20, rows * 50 + 20)


class LabelEditor(QWidget):
    def __init__(self, path, label: QLabel = None):
        super().__init__()
        self.nameLineEdit = None
        self.currentDir = path
        self.curveArgumentSelector = None
        self.selectedUnit = None

        # Create the QLineEdit and set its placeholder text
        self.lineEdit = QLineEdit()
        self.lineEdit.setPlaceholderText("Enter value here")

        # Create the QPushButton and set its text
        self.button = QPushButton("Select value")
        self.button.clicked.connect(self.openArgumentSelector)

        # Create the QLabel and set its text
        self.valueLabel = QLabel("Value: ")

        # Create a layout and add the QLineEdit, QPushButton, and QLabel
        valueLayout = QHBoxLayout()
        valueLayout.addWidget(self.valueLabel)
        valueLayout.addWidget(self.lineEdit)
        valueLayout.addWidget(self.button)

        # Get the current font, font size, font color, and background color of the indicatorLabel
        currentFont = label.font()
        currentFontSize = currentFont.pointSize()
        currentFontColor = label.palette().color(QPalette.WindowText)

        # Unit and Font Color
        unitAndColorLayout = QHBoxLayout()
        self.unitCheckbox = QCheckBox("Show Unit")
        self.fontColor = ColorEditor('Font Color', color=currentFontColor.name())
        unitAndColorLayout.addWidget(self.unitCheckbox)
        unitAndColorLayout.addWidget(self.fontColor)

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
        # Position in Layout+
        positionLayout = QHBoxLayout()
        positionLayout.addWidget(self.positionLeftButton)
        positionLayout.addWidget(self.positionCenterButton)
        positionLayout.addWidget(self.positionRightButton)
        # Check Alignment
        alignment = label.alignment()
        if alignment & Qt.AlignLeft:
            self.positionLeftButton.setChecked(True)
        elif alignment & Qt.AlignHCenter:
            self.positionCenterButton.setChecked(True)
        elif alignment & Qt.AlignRight:
            self.positionRightButton.setChecked(True)

        # Create a QSpinBox for selecting font size
        fontSizeLabel = QLabel("Font Size:")
        self.fontSizeSpinBox = QSpinBox()
        self.fontSizeSpinBox.setRange(8, 72)
        self.fontSizeSpinBox.setValue(currentFontSize)
        self.fontSizeSpinBox.setSingleStep(2)
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

        # --------- Top Layout --------
        self.topLayout = QHBoxLayout()
        # Create the return button and set its icon
        self.returnButton = QPushButton()
        self.returnButton.setFlat(True)
        self.returnButton.setIcon(QIcon('sources/icons/light-theme/icons8-back-96'))
        self.returnButton.setIconSize(QSize(20, 20))
        # Create the name valueLabel and set its text
        self.nameLabel = QLabel("Indicator")
        self.nameLabel.setAlignment(Qt.AlignCenter)
        self.nameLabel.mouseDoubleClickEvent = self.onNameLabelDoubleClick
        # Create the checkbox
        self.checkbox = QCheckBox()
        # Add the widgets to the top layout
        self.topLayout.addWidget(self.returnButton)
        self.topLayout.addWidget(self.nameLabel)
        self.topLayout.addWidget(self.checkbox)
        self.topLayout.addStretch()

        # Add the top layout to the main layout
        mainLayout = QVBoxLayout()
        mainLayout.addLayout(self.topLayout)
        mainLayout.addLayout(valueLayout)
        mainLayout.addLayout(unitAndColorLayout)
        mainLayout.addLayout(positionLayout)
        mainLayout.addLayout(fontLayout)
        self.setLayout(mainLayout)

    def onNameLabelDoubleClick(self, event):
        self.nameLineEdit = QLineEdit()
        self.nameLineEdit.setText(self.nameLabel.text())
        self.nameLineEdit.returnPressed.connect(self.onLineEditReturnPressed)
        self.topLayout.replaceWidget(self.nameLabel, self.nameLineEdit)
        self.nameLineEdit.show()
        self.nameLabel.hide()

    def onLineEditReturnPressed(self):
        self.nameLabel.setText(self.nameLineEdit.text())
        self.topLayout.replaceWidget(self.nameLineEdit, self.nameLabel)
        self.nameLineEdit.hide()
        self.nameLabel.show()


class LabeledIndicator(QGroupBox):
    def __init__(self, name: str, editor: LabelEditor, parent: GridIndicator = None):
        super().__init__(parent)
        self.setTitle(name)
        self.parentWidget = parent
        self.editor = editor
        self.label = QLabel()
        layout = QVBoxLayout()
        layout.addWidget(self.label)
        self.setLayout(layout)
        self.applyEditorSettings(self.editor)

    def applyEditorSettings(self, editor: LabelEditor):
        backgroundColor = self.parentWidget.backgroundColor.colorLabel.text()
        fontColor = editor.fontColor.colorLabel.text()
        font = QFont(editor.fontModelComboBox.currentText())
        fontSize = editor.fontSizeSpinBox.value()
        font.setPixelSize(fontSize * QFontMetricsF(font).height() / font.pointSizeF())

        self.label.setAutoFillBackground(True)
        self.label.setFont(font)
        self.label.setAutoFillBackground(True)
        self.label.setFont(font)
        self.label.setStyleSheet("background-color: " + backgroundColor + "; color: " + fontColor + ";")
        bgColor = QColor(backgroundColor)

        # Set the background color of the SingleIndicator widget
        palette = self.palette()
        palette.setColor(self.backgroundRole(), bgColor)
        self.setPalette(palette)

        # Text Alignment
        if editor.positionLeftButton.isChecked():
            self.label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        elif editor.positionCenterButton.isChecked():
            self.label.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        elif editor.positionRightButton.isChecked():
            self.label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
