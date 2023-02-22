######################## IMPORTS ########################
import os
from typing import Optional
import pyqtgraph as pg
from functools import reduce
import operator

# ------------------- PyQt Modules -------------------- #
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

# --------------------- Sources ----------------------- #
from sources.common.FileHandling import load_settings
from sources.common.Widgets import BasicDisplay, ArgumentSelector
from sources.common.balloondata import BalloonPackageDatabase


######################## CLASSES ########################
class MultiCurveGraph(BasicDisplay):
    def __init__(self, path, parent=None, backgroundColor='#ffffff'):
        super().__init__(path, parent)
        self.curveProperties = []
        self.content = None
        self.styleDict = {'Solid': Qt.SolidLine, 'Dash': Qt.DashLine, 'Dot': Qt.DotLine,
                          'DashDot': Qt.DashDotLine, 'DashDotDot': Qt.DashDotDotLine}
        layout = QVBoxLayout(self)
        self.plotWidget = pg.PlotWidget(self)
        self.plotWidget.setBackground(backgroundColor)
        self.backgroundColor = backgroundColor
        layout.addWidget(self.plotWidget)
        self.settingsWidget = CustomGraphEditDialog(self.currentDir, self)

    def applyChanges(self, editWidget):
        editWidget = self.settingsWidget
        backgroundColor = editWidget.backgroundColorFrame.colorLabel.text()
        self.backgroundColor = backgroundColor
        self.curveProperties = []
        for i in range(editWidget.tabWidget.count()):
            properties, editor = {}, editWidget.tabWidget.widget(i)
            properties['ARGUMENTS'] = (editor.lineEditX.text(), editor.lineEditY.text())
            properties['COLOR'] = editor.linePropertiesEditor.lineColor
            properties['STYLE'] = editor.linePropertiesEditor.currentLineStyle
            properties['THICKNESS'] = editor.linePropertiesEditor.thickness
            self.curveProperties.append(properties)
        self.updateContent()

    def updateContent(self, content=None):
        self.generalSettings = load_settings('settings')
        self.plotWidget.setBackground(self.backgroundColor)
        if content is not None:
            self.content = content
            self.plotWidget.clear()
            for curve in self.curveProperties:
                color, lineStyle, thickness = QColor(curve['COLOR']), curve['STYLE'], curve['THICKNESS']
                style = self.styleDict[lineStyle]
                pen = pg.mkPen(color=color, width=thickness, style=style)
                argumentX, argumentY = curve['ARGUMENTS']
                argumentXMapping, argumentYMapping = argumentX.split('$'), argumentY.split('$')
                if argumentXMapping != [''] and argumentYMapping != ['']:  # Both arguments are defined.
                    valueX = reduce(operator.getitem, argumentXMapping, self.content.storage)
                    valueY = reduce(operator.getitem, argumentYMapping, self.content.storage)
                    if len(valueX) > 1 and len(valueY) > 1:
                        self.plotWidget.plot(valueX, valueY, pen=pen)


class CustomGraphEditDialog(QWidget):
    def __init__(self, path, graph: MultiCurveGraph = None):
        super().__init__(parent=graph)
        self.currentDir = path
        # Central Editing Widget for curves
        self.centralWidget = QStackedWidget(self)

        # ---------- Curve Editors and Buttons
        # Button Array
        buttonArrayLayout = QHBoxLayout()
        self.addCurveButton = QPushButton('Add Curve')
        self.removeCurveButton = QPushButton('Remove Curve')
        buttonArrayLayout.addWidget(self.addCurveButton)
        buttonArrayLayout.addWidget(self.removeCurveButton)
        # Curve Editors
        self.tabWidget = QTabWidget(self)
        self.tabWidget.addTab(CurveEditor(0, self.currentDir, self), "Curve 1")
        self.tabWidget.addTab(CurveEditor(1, self.currentDir, self), "Curve 2")
        self.tabWidget.setMovable(True)
        self.centralWidget.addWidget(self.tabWidget)

        # Initial Curve Adding Button
        self.addCurveButtonCentral = QPushButton('Add Curve')

        # BackGround Color and Showing Grid
        self.backgroundColorFrame = ColorEditor('Background Color', color=graph.backgroundColor, parent=self)
        self.backgroundColorFrame.colorChanged.connect(self.changeEditorsBackground)

        # Options Layout
        optionsLayout = QGridLayout()
        optionsLayout.addWidget(self.backgroundColorFrame, 0, 0, 1, 2)

        # Main Layout
        layout = QVBoxLayout()
        layout.addWidget(self.centralWidget)
        layout.addLayout(optionsLayout)
        self.setLayout(layout)

    def addNewCurve(self):
        bkColor = self.backgroundColorFrame.colorLabel.text()
        self.tabWidget.addTab(CurveEditor(0, self.currentDir, self), "Curve 1")

    def removeExistingCurve(self):
        pass

    def changeEditorsBackground(self):
        bkColor = self.backgroundColorFrame.colorLabel.text()
        for i in range(self.tabWidget.count()):
            editor = self.tabWidget.widget(i)
            if isinstance(editor, CurveEditor):
                editor.linePropertiesEditor.changeBackground(bkColor)


class CurveEditor(QWidget):
    def __init__(self, curveIndex: int, path, parent=None):
        super().__init__(parent)
        self.curveArgumentSelector = None
        self.currentDir = path
        # Retrieving Curve parameters from parent and index

        # Setting editing widgets
        self.lineEditX = QLineEdit()
        self.lineEditY = QLineEdit()
        selectionButtonPixmap = QPixmap('sources/icons/light-theme/icons8-add-database-96.png').scaled(25, 25)
        labelEditX = QLabel()
        labelEditX.setPixmap(QPixmap('sources/icons/light-theme/icons8-x-coordinate-96.png').scaled(25, 25))
        labelEditY = QLabel()
        labelEditY.setPixmap(QPixmap('sources/icons/light-theme/icons8-y-coordinate-96.png').scaled(25, 25))
        self.buttonSelectorX = QPushButton()
        self.buttonSelectorX.setIcon(QIcon(selectionButtonPixmap))
        self.buttonSelectorX.clicked.connect(self.openCurveArgumentSelectorX)
        self.buttonSelectorY = QPushButton()
        self.buttonSelectorY.setIcon(QIcon(selectionButtonPixmap))
        self.buttonSelectorY.clicked.connect(self.openCurveArgumentSelectorY)

        nameLabel = QLabel('Name: ')
        self.nameEdit = QLineEdit()

        bottomLayout = QHBoxLayout()
        self.linePropertiesEditor = LinePropertiesEditor(self)
        bottomLayout.addWidget(self.linePropertiesEditor)

        layout = QGridLayout()
        layout.addWidget(nameLabel, 0, 0, 1, 1)
        layout.addWidget(self.nameEdit, 0, 1, 1, 1)
        layout.addWidget(labelEditX, 1, 0)
        layout.addWidget(self.lineEditX, 1, 1)
        layout.addWidget(self.buttonSelectorX, 1, 2)
        layout.addWidget(labelEditY, 2, 0)
        layout.addWidget(self.lineEditY, 2, 1)
        layout.addWidget(self.buttonSelectorY, 2, 2)
        layout.addLayout(bottomLayout, 3, 0, 1, 3)
        self.setLayout(layout)

    def openCurveArgumentSelectorX(self):
        self.curveArgumentSelector = ArgumentSelector(self.currentDir, self)
        self.curveArgumentSelector.selected.connect(self.argumentSelectedX)
        self.curveArgumentSelector.exec_()

    def openCurveArgumentSelectorY(self):
        self.curveArgumentSelector = ArgumentSelector(self.currentDir, self)
        self.curveArgumentSelector.selected.connect(self.argumentSelectedY)
        self.curveArgumentSelector.exec_()

    def argumentSelectedX(self):
        self.lineEditX.setText(self.curveArgumentSelector.selectedArgument)

    def argumentSelectedY(self):
        self.lineEditY.setText(self.curveArgumentSelector.selectedArgument)


class LinePropertiesEditor(QWidget):
    def __init__(self, parent=None, lineStyle: str = 'Solid', thickness: int = 2,
                 lineColor: str = '#FF0000', bkColor: str = '#FFFFFF'):
        super().__init__(parent)
        # LINESTYLES
        self.lineColor = lineColor
        self.lineStyles = ['Solid', 'Dash', 'Dot', 'DashDot', 'DashDotDot']
        assert lineStyle in self.lineStyles, 'Specified line style \'' + lineStyle + ' is not recognized.'
        self.currentLineStyle = lineStyle
        self.lineStyleComboBox = QComboBox()
        for lineStyle in self.lineStyles:
            self.lineStyleComboBox.addItem(lineStyle)
        self.lineStyleComboBox.currentTextChanged.connect(self.updateLineDisplay)

        # THICKNESS
        self.thickness = thickness
        thicknessLabel = QLabel("Thickness")
        self.thicknessSpinBox = QSpinBox()
        self.thicknessSpinBox.setRange(1, 20)
        self.thicknessSpinBox.setValue(self.thickness)
        self.thicknessSpinBox.setSingleStep(1)
        self.thicknessSpinBox.valueChanged.connect(self.updateLineDisplay)

        # CURVE COLOR
        self.colorEditor = ColorEditor('Curve Color', color=self.lineColor, parent=self)
        self.colorEditor.colorChanged.connect(self.updateLineDisplay)

        # PLOT WIDGET
        self.backgroundColor = bkColor
        self.plotWidget = pg.PlotWidget()
        self.plotWidget.setBackground(QColor(255, 255, 255))
        self.plotWidget.setMouseEnabled(x=False, y=False)
        self.plotWidget.setMenuEnabled(False)
        self.plotWidget.setLabel('bottom', '')
        self.plotWidget.setLabel('left', '')
        self.plotWidget.showAxis('bottom', False)
        self.plotWidget.showAxis('left', False)
        self.plotWidget.setBackground(QColor(self.backgroundColor))
        self.plotWidget.setMaximumHeight(self.lineStyleComboBox.sizeHint().height())
        self.plotWidget.setMaximumWidth(self.lineStyleComboBox.sizeHint().width())
        self.plotWidget.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)  # Set the size policy
        self.plotWidget.plot([0, 1, 2, 3], [0, 1, 0, 1],
                             pen=self.createPen(self.currentLineStyle, width=self.thickness))

        # RIGHT LAYOUT
        rightLayout = QGridLayout()
        rightLayout.addWidget(self.lineStyleComboBox, 0, 0)
        rightLayout.addWidget(self.plotWidget, 1, 0)
        rightLayout.addWidget(thicknessLabel, 0, 1)
        rightLayout.addWidget(self.thicknessSpinBox, 1, 1)
        rightLayout.setContentsMargins(0, 0, 0, 0)
        rightLayout.setSpacing(0)

        # MAIN LAYOUT
        mainLayout = QHBoxLayout()
        mainLayout.addWidget(self.colorEditor)
        mainLayout.addLayout(rightLayout)
        mainLayout.setContentsMargins(0, 0, 0, 0)
        mainLayout.setSpacing(0)
        self.setLayout(mainLayout)

    @staticmethod
    def createPen(line_style, width=1, color='#FF0000'):
        color = QColor(color)
        style_dict = {
            'Solid': Qt.SolidLine,
            'Dash': Qt.DashLine,
            'Dot': Qt.DotLine,
            'DashDot': Qt.DashDotLine,
            'DashDotDot': Qt.DashDotDotLine
        }
        style = style_dict.get(line_style, None)
        if style is None:
            raise ValueError('Given line style', line_style, ' is not recognized.')
        return pg.mkPen(color=color, width=width, style=style)

    def changeBackground(self, bkColor):
        self.backgroundColor = bkColor
        self.updateLineDisplay()

    def updateLineDisplay(self):
        self.currentLineStyle = self.lineStyleComboBox.currentText()
        self.thickness = self.thicknessSpinBox.value()
        self.lineColor = self.colorEditor.colorLabel.text()
        self.plotWidget.clear()
        self.plotWidget.setBackground(QColor(self.backgroundColor))
        self.plotWidget.plot([0, 1, 2, 3], [0, 1, 0, 1],
                             pen=self.createPen(self.currentLineStyle, width=self.thickness, color=self.lineColor))


class ColorEditor(QGroupBox):
    colorChanged = pyqtSignal()

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
        self.colorChanged.emit()


class SplitViewGraph(BasicDisplay):
    def __init__(self, parent=None):
        super().__init__(parent)
        # TODO SPLIT VIEW 2D GRAPH

# TODO MULTI-CURVES 2D GRAPH
# TODO 3D GRAPH
