######################## IMPORTS ########################
import pyqtgraph as pg
from functools import reduce
import operator

# ------------------- PyQt Modules -------------------- #
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

# --------------------- Sources ----------------------- #
from sources.common.utilities.FileHandling import loadSettings, nameGiving
from sources.common.widgets.Widgets import ArgumentSelector
from sources.common.widgets.basic import BasicDisplay


######################## CLASSES ########################
class MultiCurveGraph(BasicDisplay):
    def __init__(self, path, parent=None):
        super().__init__(path, parent)
        self.curveProperties = []
        self.content, self.settings = None, loadSettings('settings')
        self.styleDict = {'Solid': Qt.SolidLine, 'Dash': Qt.DashLine, 'Dot': Qt.DotLine,
                          'DashDot': Qt.DashDotLine, 'DashDotDot': Qt.DashDotDotLine}
        layout = QVBoxLayout(self)

        # Plot Widget
        self.plotWidget = pg.PlotWidget(self)
        self.plotWidget.setBackground("k" if self.settings['DARK_THEME'] else "w")
        self.plotWidget.addLegend()

        # Parameters
        self.showLegend = False
        layout.addWidget(self.plotWidget)
        self.settingsWidget = MultiCurveGraphEditDialog(self.currentDir, self)

    def getDescription(self):
        graphDescription = {'DISPLAY_TYPE': 'MULTI_CURVE_GRAPH', 'NB_CURVES': len(self.curveProperties)}
        for i in range(len(self.curveProperties)):
            graphDescription[i] = self.curveProperties[i]
        return graphDescription

    def changeTheme(self):
        self.settings = loadSettings('settings')
        self.plotWidget.setBackground("k" if self.settings['DARK_THEME'] else "w")
        self.settingsWidget.changeTheme(darkTheme=self.settings['DARK_THEME'])

    def applyChanges(self, editWidget):
        editWidget = self.settingsWidget
        self.showLegend = editWidget.showLegendCheckBox.isChecked()
        # TODO Add Legend ShowCase
        if self.showLegend:
            pass
        else:
            pass
        self.curveProperties = []
        for i in range(editWidget.tabWidget.count()):
            properties, editor = {}, editWidget.tabWidget.widget(i)
            properties['ARGUMENTS'] = [editor.lineEditX.text(), editor.lineEditY.text()]
            properties['COLOR'] = editor.lineProperties.lineColor
            properties['STYLE'] = editor.lineProperties.currentLineStyle
            properties['THICKNESS'] = editor.lineProperties.thickness
            properties['NAME'] = editor.name
            self.curveProperties.append(properties)
        self.updateContent()

    def applyDescription(self, description):
        self.curveProperties = []
        for curve in range(description['NB_CURVES']):
            self.curveProperties.append(description[str(curve)])
        self.settingsWidget = MultiCurveGraphEditDialog(self.currentDir, self)

    def updateContent(self, content=None):
        self.generalSettings = loadSettings('settings')
        if content is not None:
            self.content = content
            self.plotWidget.clear()
            for curve in self.curveProperties:
                color, lineStyle, thickness = QColor(curve['COLOR']), curve['STYLE'], curve['THICKNESS']
                style = self.styleDict[lineStyle]
                pen = pg.mkPen(color=color, width=thickness, style=style)
                argumentX, argumentY = curve['ARGUMENTS']
                argumentXMapping, argumentYMapping = argumentX.split('/'), argumentY.split('/')
                if argumentXMapping != [''] and argumentYMapping != ['']:  # Both arguments are defined.
                    valueX = reduce(operator.getitem, argumentXMapping, self.content.storage)
                    valueY = reduce(operator.getitem, argumentYMapping, self.content.storage)
                    if len(valueX) > 1 and len(valueY) > 1:
                        self.plotWidget.plot(valueX, valueY, pen=pen)


class MultiCurveGraphEditDialog(QWidget):
    def __init__(self, path, parent: MultiCurveGraph):
        super().__init__(parent)
        self.currentDir = path
        self.hide()
        self.colorCycler = ColorCycler()
        # Central Editing Widget for curves
        self.centralWidget = QStackedWidget(self)

        # ---------- Curve Editors and Buttons
        # Button Array
        buttonArrayLayout = QHBoxLayout()
        self.addCurveButton = QPushButton('Add Curve')
        self.addCurveButton.clicked.connect(self.addNewCurve)
        self.removeCurveButton = QPushButton('Remove Curve')
        self.removeCurveButton.clicked.connect(self.removeExistingCurve)
        buttonArrayLayout.addWidget(self.addCurveButton)
        buttonArrayLayout.addWidget(self.removeCurveButton)
        # Curve Editors
        self.tabWidget = QTabWidget(self)
        self.tabWidget.setMovable(True)
        # Layout
        self.curveEditorsWidget = QWidget()
        curveEditorLayout = QGridLayout()
        curveEditorLayout.addWidget(self.addCurveButton, 0, 0, 1, 1)
        curveEditorLayout.addWidget(self.removeCurveButton, 0, 1, 1, 1)
        curveEditorLayout.addWidget(self.tabWidget, 1, 0, 2, 2)
        self.curveEditorsWidget.setLayout(curveEditorLayout)
        self.centralWidget.addWidget(self.curveEditorsWidget)

        # Initial Curve Adding Button
        self.addCurveButtonCentral = QPushButton('Add Curve')
        self.addCurveButtonCentral.clicked.connect(self.addNewCurve)
        self.centralWidget.addWidget(self.addCurveButtonCentral)
        self.centralWidget.setCurrentIndex(1)
        self.showLegendCheckBox = QCheckBox('Show Legend')

        # Add Curve Properties
        for curve in parent.curveProperties:
            self.addNewCurve(curve)

        # Main Layout
        layout = QVBoxLayout()
        layout.addWidget(self.centralWidget)
        layout.addWidget(self.showLegendCheckBox)
        self.setLayout(layout)

    def addNewCurve(self, properties=None):
        count = self.tabWidget.count()
        if count == 0:
            self.centralWidget.setCurrentIndex(0)
        if properties is None:
            names = [self.tabWidget.widget(i).name for i in range(self.tabWidget.count())]
            name = nameGiving(names, 'Curve', startingIndex=1, firstName=False)
            lineColor = self.colorCycler.next(0, inHexCode=True) if count == 0 else self.colorCycler.next(inHexCode=True)
            properties = {'NAME': name, 'THICKNESS': 2, 'COLOR': lineColor, 'STYLE': 'Solid', 'ARGUMENTS': ['', '']}
        curveEditor = CurveEditor(self.currentDir, properties)
        self.tabWidget.addTab(curveEditor, properties['NAME'])
        self.tabWidget.widget(count).nameChange.connect(self.changeTabNames)

    def changeTheme(self, darkTheme=False):
        for i in range(self.tabWidget.count()):
            curveEditor: CurveEditor = self.tabWidget.widget(i)
            curveEditor.lineProperties.plotWidget.setBackground("k" if darkTheme else "w")
            themeFolder = 'dark-theme' if darkTheme else 'light-theme'
            selectionButtonPixmap = QPixmap(f'sources/icons/{themeFolder}/icons8-add-database-96.png').scaled(25, 25)
            xPixMap = QPixmap(f'sources/icons/{themeFolder}/icons8-x-coordinate-96.png').scaled(25, 25)
            yPixMap = QPixmap(f'sources/icons/{themeFolder}/icons8-y-coordinate-96.png').scaled(25, 25)
            curveEditor.lineProperties.labelEditX.setPixmap(xPixMap)
            curveEditor.lineProperties.labelEditY.setPixmap(yPixMap)
            curveEditor.lineProperties.buttonSelectorX.setIcon(QIcon(selectionButtonPixmap))
            curveEditor.lineProperties.buttonSelectorY.setIcon(QIcon(selectionButtonPixmap))

    def removeExistingCurve(self):
        currentIndex = self.tabWidget.currentIndex()
        if self.tabWidget.count() > 0:
            self.tabWidget.removeTab(currentIndex)
            if self.tabWidget.count() == 0:
                self.centralWidget.setCurrentIndex(1)

    def changeTabNames(self):
        for i in range(self.tabWidget.count()):
            self.tabWidget.setTabText(i, self.tabWidget.widget(i).name)

    def changeEditorsBackground(self, bkColor):
        for i in range(self.tabWidget.count()):
            editor = self.tabWidget.widget(i)
            if isinstance(editor, CurveEditor):
                editor.lineProperties.changeBackground(bkColor)


class CurveEditor(QWidget):
    nameChange = pyqtSignal()

    def __init__(self, path, properties):
        super().__init__()
        self.currentDir = path
        self.name = properties['NAME']
        # TODO Get Parameters from parent and index or from .ini file

        # Setting editing widgets
        self.lineEditX = QLineEdit()
        self.lineEditX.setText(properties['ARGUMENTS'][0])
        self.lineEditY = QLineEdit()
        self.lineEditY.setText(properties['ARGUMENTS'][1])
        self.settings = loadSettings('settings')
        themeFolder = 'dark-theme' if self.settings['DARK_THEME'] else 'light-theme'
        selectionButtonPixmap = QPixmap(f'sources/icons/{themeFolder}/icons8-add-database-96.png').scaled(25, 25)
        xPixMap = QPixmap(f'sources/icons/{themeFolder}/icons8-x-coordinate-96.png').scaled(25, 25)
        yPixMap = QPixmap(f'sources/icons/{themeFolder}/icons8-y-coordinate-96.png').scaled(25, 25)
        self.labelEditX = QLabel()
        self.labelEditX.setPixmap(xPixMap)
        self.labelEditY = QLabel()
        self.labelEditY.setPixmap(yPixMap)
        self.buttonSelectorX = QPushButton()
        self.buttonSelectorY = QPushButton()
        self.buttonSelectorX.setIcon(QIcon(selectionButtonPixmap))
        self.buttonSelectorY.setIcon(QIcon(selectionButtonPixmap))
        self.buttonSelectorX.clicked.connect(self.openCurveArgumentSelectorX)
        self.buttonSelectorY.clicked.connect(self.openCurveArgumentSelectorY)

        nameLabel = QLabel('Name: ')
        self.nameEdit = QLineEdit()
        self.nameEdit.setText(self.name)
        self.nameEdit.textChanged.connect(self.nameChanged)

        bottomLayout = QHBoxLayout()
        self.lineProperties = LineEditor(self, properties['STYLE'], properties['THICKNESS'], properties['COLOR'])
        bottomLayout.addWidget(self.lineProperties)

        layout = QGridLayout()
        layout.addWidget(nameLabel, 0, 0, 1, 1)
        layout.addWidget(self.nameEdit, 0, 1, 1, 1)
        layout.addWidget(self.labelEditX, 1, 0)
        layout.addWidget(self.lineEditX, 1, 1)
        layout.addWidget(self.buttonSelectorX, 1, 2)
        layout.addWidget(self.labelEditY, 2, 0)
        layout.addWidget(self.lineEditY, 2, 1)
        layout.addWidget(self.buttonSelectorY, 2, 2)
        layout.addLayout(bottomLayout, 3, 0, 1, 3)
        self.setLayout(layout)

    def openCurveArgumentSelectorX(self):
        dialog = ArgumentSelector(self.currentDir, self)
        result = dialog.exec_()
        if result == QMessageBox.Accepted:
            self.lineEditX.setText(dialog.selectedArgument)
            self.lineEditX.adjustSize()

    def openCurveArgumentSelectorY(self):
        dialog = ArgumentSelector(self.currentDir, self)
        result = dialog.exec_()
        if result == QMessageBox.Accepted:
            self.lineEditY.setText(dialog.selectedArgument)
            self.lineEditY.adjustSize()

    def nameChanged(self):
        self.name = self.nameEdit.text()
        self.nameChange.emit()


class LineEditor(QWidget):
    def __init__(self, parent=None, lineStyle: str = 'Solid', thickness: int = 2, lineColor: str = '#FF0000'):
        super().__init__(parent)
        # LINE STYLES
        self.lineColor = lineColor
        self.lineStyles = ['Solid', 'Dash', 'Dot', 'DashDot', 'DashDotDot']
        assert lineStyle in self.lineStyles, 'Specified line style \'' + lineStyle + ' is not recognized.'
        self.currentLineStyle = lineStyle
        self.lineStyleComboBox = QComboBox()
        for lineStyle in self.lineStyles:
            self.lineStyleComboBox.addItem(lineStyle)
        self.lineStyleComboBox.setCurrentText(self.currentLineStyle)
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
        self.plotWidget = pg.PlotWidget()
        self.plotWidget.setMouseEnabled(x=False, y=False)
        self.plotWidget.setMenuEnabled(False)
        self.plotWidget.setLabel('bottom', '')
        self.plotWidget.setLabel('left', '')
        self.plotWidget.showAxis('bottom', False)
        self.plotWidget.showAxis('left', False)
        self.plotWidget.setMaximumHeight(self.lineStyleComboBox.sizeHint().height())
        self.plotWidget.setMaximumWidth(self.lineStyleComboBox.sizeHint().width())
        self.plotWidget.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.plotWidget.plot([0, 1, 2, 3], [0, 1, 0, 1], pen=self.createPen(self.currentLineStyle, width=self.thickness, color=self.lineColor))

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
        style_dict = {'Solid': Qt.SolidLine, 'Dash': Qt.DashLine, 'Dot': Qt.DotLine, 'DashDot': Qt.DashDotLine, 'DashDotDot': Qt.DashDotDotLine}
        style = style_dict.get(line_style, None)
        if style is None:
            raise ValueError('Given line style', line_style, ' is not recognized.')
        return pg.mkPen(color=color, width=width, style=style)

    def updateLineDisplay(self):
        self.currentLineStyle = self.lineStyleComboBox.currentText()
        self.thickness = self.thicknessSpinBox.value()
        self.lineColor = self.colorEditor.colorLabel.text()
        self.plotWidget.clear()
        self.plotWidget.plot([0, 1, 2, 3], [0, 1, 0, 1], pen=self.createPen(self.currentLineStyle, width=self.thickness, color=self.lineColor))


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


class ColorCycler:
    CYCLE = [(31, 119, 180), (255, 127, 14), (44, 160, 44), (214, 39, 40), (148, 103, 189),
             (140, 86, 75), (227, 119, 194), (127, 127, 127), (188, 189, 34), (23, 190, 207)]
    NB_COLORS = 10

    def __init__(self):
        self.step = 0

    def next(self, step=None, inHexCode=False):
        if step is not None:
            self.step = step
        value = self.CYCLE[self.step]
        self.step += 1
        if self.step == self.NB_COLORS:
            self.step = 0
        if inHexCode:
            return "#{:02x}{:02x}{:02x}".format(*value)
        return value

    def get(self, step, inHexCode=False):
        assert step < self.NB_COLORS
        if inHexCode:
            return "#{:02x}{:02x}{:02x}".format(*self.CYCLE[step])
        return self.CYCLE[step]
