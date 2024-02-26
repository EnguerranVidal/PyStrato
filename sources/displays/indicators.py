######################## IMPORTS ########################
import os
from typing import Dict, Optional
from functools import reduce
import operator

# ------------------- PyQt Modules -------------------- #
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

# --------------------- Sources ----------------------- #
from sources.common.utilities.fileSystem import loadSettings, nameGiving
from sources.common.widgets.Widgets import ArgumentSelector
from sources.common.widgets.basic import BasicDisplay
from sources.databases.units import DefaultUnitsCatalogue


######################## CLASSES ########################
class SingleIndicator(BasicDisplay):
    def __init__(self, path, parent=None):
        super().__init__(path, parent)
        self.textAlignment = 0
        self.lastValue = None
        self.argument, self.argumentUnit, self.showUnit = '', None, False
        self.catalogue = DefaultUnitsCatalogue()
        self.indicatorLabel = QLabel('')
        self.settingsWidget = SingleIndicatorEditDialog(self.currentDir, self)

        gridLayout = QGridLayout()
        gridLayout.addWidget(self.indicatorLabel)
        self.setLayout(gridLayout)

    def getDescription(self):
        font = self.indicatorLabel.font()
        fontFamily = font.family()
        fontSize = font.pointSize()
        description = {'DISPLAY_TYPE': 'SINGLE_INDICATOR',
                       'ARGUMENT': self.argument,
                       'SHOW_UNIT': int(self.showUnit),
                       'FONT_FAMILY': fontFamily,
                       'FONT_SIZE': fontSize,
                       'TEXT_PLACEMENT': self.textAlignment
                       }
        return description

    def applyDescription(self, description):
        self.argument = description['ARGUMENT']
        self.showUnit = bool(description['SHOW_UNIT'])
        font = QFont(description['FONT_FAMILY'])
        fontSize = description['FONT_SIZE']
        font.setPointSize(fontSize)
        self.indicatorLabel.setAutoFillBackground(True)
        self.indicatorLabel.setFont(font)
        self.textAlignment = description['TEXT_PLACEMENT']
        if self.textAlignment == 0:
            self.indicatorLabel.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        elif self.textAlignment == 1:
            self.indicatorLabel.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        else:
            self.indicatorLabel.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        if self.argument != '':
            self.retrieveArgumentUnit(self.argument)
        self.settingsWidget = SingleIndicatorEditDialog(self.currentDir, self)
        self.updateContent()

    def generateSettingsWidget(self):
        self.settingsWidget = SingleIndicatorEditDialog(self.currentDir, self)

    def applyChanges(self, editWidget):
        font = QFont(editWidget.fontModelComboBox.currentText())
        fontSize = editWidget.fontSizeSpinBox.value()
        font.setPointSize(fontSize)
        self.indicatorLabel.setAutoFillBackground(True)
        self.indicatorLabel.setFont(font)
        # Text Alignment
        if editWidget.positionLeftButton.isChecked():
            self.indicatorLabel.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            self.textAlignment = 0
        elif editWidget.positionCenterButton.isChecked():
            self.indicatorLabel.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
            self.textAlignment = 1
        else:
            self.indicatorLabel.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.textAlignment = 2
        self.showUnit = editWidget.unitCheckbox.isChecked()
        self.argumentUnit = editWidget.argumentUnit
        self.argument = editWidget.argumentEdit.text()
        self.updateContent()

    def updateContent(self, content=None):
        self.generalSettings = loadSettings('settings')
        argumentMapping = self.argument.split('/')
        if argumentMapping != ['']:
            if content is None:
                value = ''
            else:
                value = content.retrieveStoredContent(argumentMapping)
            if len(value) > 0:
                displayedText = str(value[-1])
                self.lastValue = value[-1]
            else:
                if self.argumentUnit is not None:
                    if issubclass(self.argumentUnit.type, float):
                        displayedText = '____.__'
                    else:
                        displayedText = '____'
                else:
                    displayedText = '____'
            self.lastValue = displayedText
            if self.showUnit:
                symbol = self.catalogue.getSymbol(self.argumentUnit.name)
                if symbol is not None:
                    displayedText += ' ' + symbol
                else:
                    displayedText += ' ' + self.argumentUnit.name
            self.indicatorLabel.setText(displayedText)

    def retrieveArgumentUnit(self, argument):

        def getUnit(level, keys):
            for key in keys:
                if key in level:
                    level = level[key]
                else:
                    return None
            if isinstance(level, dict):
                return None
            return level

        dialog = ArgumentSelector(self.currentDir, self)
        argument = argument.split('/')
        database, telemetry, argument = argument[0], argument[1], argument[2:]
        selectedTypes, selectedUnits = dialog.databases[database].nestedPythonTypes(telemetry, (int, float))
        unitName = getUnit(selectedUnits, argument)
        self.argumentUnit = dialog.databases[database].units[unitName][0] if unitName is not None else None


class SingleIndicatorEditDialog(QWidget):
    def __init__(self, path, parent: SingleIndicator = None):
        super().__init__(parent)
        self.argumentUnit = parent.argumentUnit
        self.currentDir = path

        # ARGUMENT DISPLAY
        self.argumentEdit = QLineEdit()
        self.argumentEdit.setText(parent.argument)
        self.argumentEdit.setPlaceholderText("Enter value here")
        self.argumentButton = QPushButton("Select value")
        self.argumentButton.clicked.connect(self.openArgumentSelector)

        # FONT & SHOWING UNIT
        currentFont = parent.indicatorLabel.font()
        currentFontSize = currentFont.pointSize()
        self.unitCheckbox = QCheckBox("Show Unit")
        self.unitCheckbox.setChecked(parent.showUnit)
        fontSizeLabel = QLabel("Font Size:")
        self.fontSizeSpinBox = QSpinBox()
        self.fontSizeSpinBox.setRange(8, 72)
        self.fontSizeSpinBox.setValue(currentFontSize)
        self.fontSizeSpinBox.setSingleStep(2)
        fontModelLabel = QLabel("Font Model:")
        self.fontModelComboBox = QFontComboBox()
        self.fontModelComboBox.setCurrentFont(currentFont)

        # POSITIONING BUTTONS
        self.positionButtonGroup = QButtonGroup(self)
        self.settings = loadSettings('settings')
        themeFolder = 'dark-theme' if self.settings['DARK_THEME'] else 'light-theme'
        self.positionLeftButton = QPushButton()
        self.positionLeftButton.setIcon(QIcon(f'sources/icons/{themeFolder}/icons8-align-left-96.png'))
        self.positionLeftButton.setIconSize(QSize(20, 20))
        self.positionLeftButton.setCheckable(True)
        self.positionCenterButton = QPushButton()
        self.positionCenterButton.setIcon(QIcon(f'sources/icons/{themeFolder}/icons8-align-center-96.png'))
        self.positionCenterButton.setIconSize(QSize(20, 20))
        self.positionCenterButton.setCheckable(True)
        self.positionRightButton = QPushButton()
        self.positionRightButton.setIcon(QIcon(f'sources/icons/{themeFolder}/icons8-align-right-96.png'))
        self.positionRightButton.setIconSize(QSize(20, 20))
        self.positionRightButton.setCheckable(True)
        self.positionButtonGroup.addButton(self.positionLeftButton)
        self.positionButtonGroup.addButton(self.positionCenterButton)
        self.positionButtonGroup.addButton(self.positionRightButton)
        self.positionButtonGroup.setExclusive(True)
        alignment = parent.indicatorLabel.alignment()
        if alignment & Qt.AlignLeft:
            self.positionLeftButton.setChecked(True)
        elif alignment & Qt.AlignHCenter:
            self.positionCenterButton.setChecked(True)
        elif alignment & Qt.AlignRight:
            self.positionRightButton.setChecked(True)

        # MAIN LAYOUT
        valueLayout = QHBoxLayout()
        valueLayout.addWidget(QLabel("Value: "))
        valueLayout.addWidget(self.argumentEdit)
        valueLayout.addWidget(self.argumentButton)
        positionLayout = QHBoxLayout()
        positionLayout.addWidget(self.positionLeftButton)
        positionLayout.addWidget(self.positionCenterButton)
        positionLayout.addWidget(self.positionRightButton)
        fontLayout = QGridLayout()
        fontLayout.addWidget(fontSizeLabel, 0, 0)
        fontLayout.addWidget(self.fontSizeSpinBox, 0, 1)
        fontLayout.addWidget(fontModelLabel, 1, 0)
        fontLayout.addWidget(self.fontModelComboBox, 1, 1)
        mainLayout = QVBoxLayout()
        mainLayout.addLayout(valueLayout)
        mainLayout.addWidget(self.unitCheckbox)
        mainLayout.addLayout(positionLayout)
        mainLayout.addLayout(fontLayout)
        self.setLayout(mainLayout)
        self.hide()

    def changeTheme(self, darkTheme=False):
        themeFolder = 'dark-theme' if darkTheme else 'light-theme'
        self.positionLeftButton.setIcon(QIcon(f'sources/icons/{themeFolder}/icons8-align-left-96.png'))
        self.positionCenterButton.setIcon(QIcon(f'sources/icons/{themeFolder}/icons8-align-center-96.png'))
        self.positionRightButton.setIcon(QIcon(f'sources/icons/{themeFolder}/icons8-align-right-96.png'))

    def openArgumentSelector(self):
        dialog = ArgumentSelector(self.currentDir, self)
        result = dialog.exec_()
        if result == QDialog.Accepted:
            self.argumentUnit = dialog.argumentUnit
            if self.argumentUnit is None:
                self.unitCheckbox.setEnabled(False)
                self.unitCheckbox.setChecked(False)
            else:
                self.unitCheckbox.setEnabled(True)
                self.unitCheckbox.setChecked(True)
            self.argumentEdit.setText(dialog.selectedArgument)
            self.argumentEdit.adjustSize()


############################## GRID INDICATOR ##############################
class GridIndicator(BasicDisplay):
    def __init__(self, path, parent=None):
        super().__init__(path, parent)
        self.bgColor = '#f0f0f0'
        self.labelGridLayout = QGridLayout()
        self.setLayout(self.labelGridLayout)
        self.nbRows, self.nbColumns = 1, 1
        firstIndicator = LabeledIndicator(self.currentDir, 'Value 0', self)
        self.indicators = {(0, 0): firstIndicator}
        self.labelGridLayout.addWidget(self.indicators[(0, 0)], 0, 0, 1, 1)
        self.settingsWidget = GridIndicatorEditDialog(self.currentDir, self)

    def getDescription(self):
        gridDescription = {'DISPLAY_TYPE': 'GRID_INDICATOR', 'DIMENSIONS': [self.nbRows, self.nbColumns]}
        for i in range(self.nbRows):
            for j in range(self.nbColumns):
                indicator = self.indicators[(i, j)]
                font = indicator.label.font()
                fontFamily = font.family()
                fontSize = font.pointSize()
                description = {'NAME': indicator.title(),
                               'ARGUMENT': indicator.argument,
                               'SHOW_UNIT': int(indicator.showUnit),
                               'FONT_FAMILY': fontFamily,
                               'FONT_SIZE': fontSize,
                               'TEXT_PLACEMENT': indicator.textAlignment}
                gridDescription[f'{i},{j}'] = description
        return gridDescription

    def applyDescription(self, description):
        while self.labelGridLayout.count() > 0:
            widget = self.labelGridLayout.itemAt(0).widget()
            self.labelGridLayout.removeWidget(widget)
            widget.setParent(None)
        self.nbRows, self.nbColumns = description['DIMENSIONS']
        for i in range(self.nbRows):
            for j in range(self.nbColumns):
                indicatorDescription = description[f'{i},{j}']
                indicator = LabeledIndicator(self.currentDir, '', self)
                indicator.applyDescription(indicatorDescription)
                self.indicators[(i, j)] = indicator
                self.labelGridLayout.addWidget(self.indicators[(i, j)], i, j, 1, 1)
        self.settingsWidget = GridIndicatorEditDialog(self.currentDir, self)

    def generateSettingsWidget(self):
        self.settingsWidget = GridIndicatorEditDialog(self.currentDir, self)

    def fillGrid(self, editWidget=None):
        if editWidget is None:
            editWidget = self.settingsWidget
        # Removing Old Widgets
        while self.labelGridLayout.count() > 0:
            widget = self.labelGridLayout.itemAt(0).widget()
            self.labelGridLayout.removeWidget(widget)
            widget.setParent(None)
        # Adding New Widgets
        for i in range(self.nbRows):
            for j in range(self.nbColumns):
                labelEditor = editWidget.labelEditors[(i, j)]
                if (i, j) not in self.indicators:
                    self.indicators[(i, j)] = LabeledIndicator(self.currentDir, labelEditor.name, self)
                    self.indicators[(i, j)].applyEditorSettings(self.settingsWidget.labelEditors[(i, j)])
                self.labelGridLayout.addWidget(self.indicators[(i, j)], i, j, 1, 1)
                self.indicators[(i, j)].applyEditorSettings(labelEditor)

    def applyChanges(self, editWidget=None):
        if editWidget is None:
            editWidget = self.settingsWidget
        self.nbRows = editWidget.rowSpinBox.value()
        self.nbColumns = editWidget.columnSpinBox.value()
        # Fill and update Grid
        self.fillGrid(editWidget)
        self.updateContent()

    def updateContent(self, content=None):
        for i in range(self.nbRows):
            for j in range(self.nbColumns):
                self.indicators[(i, j)].updateLabelContent(content)


class GridIndicatorEditDialog(QWidget):
    def __init__(self, path, parent: GridIndicator):
        super().__init__(parent)
        self.currentDir = path
        self.labelEditors = {}  # type: Dict[tuple[int, int], LabelEditor]
        self.nbRows = parent.labelGridLayout.rowCount()
        self.nbColumns = parent.labelGridLayout.columnCount()

        # ROW AND COLUMN SPIN BOXES
        self.columnSpinBox = QSpinBox(self)
        self.rowSpinBox = QSpinBox(self)
        self.rowSpinBox.setRange(1, 50)
        self.columnSpinBox.setRange(1, 50)
        self.rowSpinBox.setValue(self.nbRows)
        self.columnSpinBox.setValue(self.nbColumns)
        self.rowSpinBox.setFixedSize(50, 25)
        self.columnSpinBox.setFixedSize(50, 25)

        # GRID EDITOR
        self.centralDisplay = QStackedWidget(self)
        self.gridEditor = QWidget(self)
        self.gridEditor.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.gridLayout = QGridLayout()
        self.gridEditor.setLayout(self.gridLayout)

        # LABEL EDITORS
        for row in range(self.nbRows):
            for column in range(self.nbColumns):
                indicator: LabeledIndicator = parent.labelGridLayout.itemAtPosition(row, column).widget()
                editor = LabelEditor(self.currentDir, indicator.title(), indicator)
                editor.goBackToGrid.connect(self.openGridEditor)
                self.labelEditors[row, column] = editor
                button = QPushButton()
                button.setObjectName(f"{row}_{column}")
                button.setFixedSize(50, 50)
                button.clicked.connect(self.openLabelEditor)
                self.gridLayout.addWidget(button, row, column)
        self.gridEditor.setFixedSize(self.nbColumns * 50 + 20, self.nbRows * 50 + 20)

        # self.gridEditor.openLabelEditor.connect(self.openLabelEditor)
        self.columnSpinBox.valueChanged.connect(self.extendIndicatorGrid)
        self.rowSpinBox.valueChanged.connect(self.extendIndicatorGrid)
        self.centralDisplay.addWidget(self.gridEditor)

        # MAIN LAYOUT
        spinBoxLayout = QHBoxLayout()
        spinBoxLayout.addWidget(QLabel("Columns:"))
        spinBoxLayout.addWidget(self.columnSpinBox)
        spinBoxLayout.addWidget(QLabel("Rows:"))
        spinBoxLayout.addWidget(self.rowSpinBox)
        mainLayout = QGridLayout()
        mainLayout.addLayout(spinBoxLayout, 0, 0, Qt.AlignLeft)
        mainLayout.addWidget(self.centralDisplay, 1, 0, Qt.AlignCenter)
        self.setLayout(mainLayout)
        self.hide()

    def extendIndicatorGrid(self):
        # ROW ADDITION / EXTENSION
        if self.rowSpinBox.value() > self.nbRows:
            newRowCount = self.rowSpinBox.value()
            for row in range(self.nbRows, newRowCount):
                for column in range(self.nbColumns):
                    if self.labelEditors.get((row, column), None) is None:
                        labelNames = [labelEditor.name for labelEditor in self.labelEditors.values()]
                        editor = LabelEditor(self.currentDir, nameGiving(labelNames, baseName='Value', firstName=False))
                        editor.goBackToGrid.connect(self.openGridEditor)
                        self.labelEditors[(row, column)] = editor
            self.nbRows = newRowCount
        # COLUMN ADDITION / EXTENSION
        if self.columnSpinBox.value() > self.nbColumns:
            newColumnCount = self.columnSpinBox.value()
            for row in range(self.nbRows):
                for column in range(self.nbColumns, newColumnCount):
                    if self.labelEditors.get((row, column), None) is None:
                        labelNames = [labelEditor.name for labelEditor in self.labelEditors.values()]
                        editor = LabelEditor(self.currentDir, nameGiving(labelNames, baseName='Value', firstName=False))
                        editor.goBackToGrid.connect(self.openGridEditor)
                        self.labelEditors[(row, column)] = editor
            self.nbColumns = newColumnCount
        self.updateGrid()

    def updateGrid(self):
        rows = self.rowSpinBox.value()
        columns = self.columnSpinBox.value()
        while self.gridLayout.count() > 0:
            widget = self.gridLayout.itemAt(0).widget()
            self.gridLayout.removeWidget(widget)
            widget.setParent(None)
        for i in range(rows):
            self.gridLayout.setRowStretch(i, 1)
        for i in range(columns):
            self.gridLayout.setColumnStretch(i, 1)
        for row in range(rows):
            for column in range(columns):
                button = QPushButton()
                button.setFixedSize(50, 50)
                button.setObjectName(f"{row}_{column}")
                button.clicked.connect(self.openLabelEditor)
                self.gridLayout.addWidget(button, row, column)
        self.gridEditor.setFixedSize(columns * 50 + 20, rows * 50 + 20)

    def openGridEditor(self):
        self.updateGrid()
        index = self.centralDisplay.indexOf(self.gridEditor)
        self.centralDisplay.setCurrentIndex(index)

    def openLabelEditor(self):
        button = self.sender()
        row, column = map(int, button.objectName().split("_"))
        index = self.centralDisplay.indexOf(self.labelEditors[(row, column)])
        if self.centralDisplay.indexOf(self.labelEditors[(row, column)]) == -1:
            self.centralDisplay.addWidget(self.labelEditors[(row, column)])
            index = self.centralDisplay.indexOf(self.labelEditors[(row, column)])
        self.centralDisplay.setCurrentIndex(index)


class LabeledIndicator(QGroupBox):
    def __init__(self, path, name: str, parent: GridIndicator):
        super().__init__(parent)
        self.currentDir = path
        self.textAlignment = 0
        self.lastValue = None
        self.catalogue = DefaultUnitsCatalogue()
        self.generalSettings = loadSettings('settings')
        self.argument = ''
        self.argumentUnit = None
        self.showUnit = False
        self.setTitle(name)
        self.parentWidget = parent
        self.label = QLabel()
        font = self.label.font()
        font.setPointSize(8)
        self.label.setFont(font)
        layout = QVBoxLayout()
        layout.addWidget(self.label)
        self.setLayout(layout)

    def applyEditorSettings(self, labelEditor):
        font = QFont(labelEditor.fontModelComboBox.currentText())
        fontSize = labelEditor.fontSizeSpinBox.value()
        font.setPointSize(fontSize)
        self.label.setAutoFillBackground(True)
        self.label.setFont(font)
        if labelEditor.positionLeftButton.isChecked():
            self.label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            self.textAlignment = 0
        elif labelEditor.positionCenterButton.isChecked():
            self.label.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
            self.textAlignment = 1
        elif labelEditor.positionRightButton.isChecked():
            self.label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.textAlignment = 2
        self.showUnit = labelEditor.unitCheckbox.isChecked()
        self.argumentUnit = labelEditor.argumentUnit
        self.argument = labelEditor.argumentEdit.text()
        self.setTitle(labelEditor.name)
        self.updateLabelContent()

    def updateLabelContent(self, content=None):
        self.generalSettings = loadSettings('settings')
        argumentMapping = self.argument.split('/')
        if argumentMapping != ['']:  # There is an argument in the parameters
            if content is None:
                value = ''
            else:
                value = content.retrieveStoredContent(argumentMapping)
            if len(value) > 0:
                displayedText = str(value[-1])
                self.lastValue = value[-1]
            else:
                if self.argumentUnit is not None:
                    if issubclass(self.argumentUnit.type, float):
                        displayedText = '____.__'
                    else:
                        displayedText = '____'
                else:
                    displayedText = '____'
            self.lastValue = displayedText
            if self.showUnit:
                symbol = self.catalogue.getSymbol(self.argumentUnit.name)
                if symbol is not None:
                    displayedText += ' ' + symbol
                else:
                    displayedText += ' ' + self.argumentUnit.name
            self.label.setText(displayedText)

    def applyDescription(self, description):
        self.setTitle(description['NAME'])
        self.argument = description['ARGUMENT']
        self.showUnit = bool(description['SHOW_UNIT'])
        font = QFont(description['FONT_FAMILY'])
        fontSize = description['FONT_SIZE']
        font.setPointSize(fontSize)
        self.label.setAutoFillBackground(True)
        self.label.setFont(font)
        self.textAlignment = description['TEXT_PLACEMENT']
        if self.textAlignment == 0:
            self.label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        elif self.textAlignment == 1:
            self.label.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        else:
            self.label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        if self.argument != '':
            self.retrieveArgumentUnit(self.argument)
        self.updateLabelContent()

    def retrieveArgumentUnit(self, argument):

        def getUnit(level, keys):
            for key in keys:
                if key in level:
                    level = level[key]
                else:
                    return None
            if isinstance(level, dict):
                return None
            return level

        dialog = ArgumentSelector(self.currentDir, self)
        argument = argument.split('/')
        database, telemetry, argument = argument[0], argument[1], argument[2:]
        selectedTypes, selectedUnits = dialog.databases[database].nestedPythonTypes(telemetry, (int, float))
        unitName = getUnit(selectedUnits, argument)
        self.argumentUnit = dialog.databases[database].units[unitName][0] if unitName is not None else None


class LabelEditor(QWidget):
    goBackToGrid = pyqtSignal()

    def __init__(self, path, name='', indicator: Optional[LabeledIndicator] = None):
        super().__init__()
        self.hide()
        self.indicator, self.name = indicator, name
        self.argumentUnit = indicator.argumentUnit if self.indicator is not None else None
        self.currentDir = path

        # ARGUMENT EDIT AND SELECTOR
        self.argumentEdit = QLineEdit()
        self.argumentEdit.setText(indicator.argument if self.indicator is not None else '')
        self.argumentEdit.setPlaceholderText("Enter value here")
        self.selectionButton = QPushButton("Select value")
        self.selectionButton.clicked.connect(self.openArgumentSelector)

        # CURRENT FONT & UNIT
        label = QLabel()
        currentFont = indicator.label.font() if self.indicator is not None else label.font()
        currentFontSize = currentFont.pointSize()
        self.unitCheckbox = QCheckBox("Show Unit")
        self.unitCheckbox.setChecked(indicator.showUnit if self.indicator is not None else False)
        fontSizeLabel = QLabel("Font Size:")
        self.fontSizeSpinBox = QSpinBox()
        self.fontSizeSpinBox.setRange(8, 72)
        self.fontSizeSpinBox.setValue(currentFontSize)
        self.fontSizeSpinBox.setSingleStep(2)
        fontModelLabel = QLabel("Font Model:")
        self.fontModelComboBox = QFontComboBox()
        self.fontModelComboBox.setCurrentFont(currentFont)

        # POSITIONING BUTTONS
        self.positionButtonGroup = QButtonGroup(self)
        self.settings = loadSettings('settings')
        themeFolder = 'dark-theme' if self.settings['DARK_THEME'] else 'light-theme'
        self.positionLeftButton = QPushButton()
        self.positionLeftButton.setIcon(QIcon(f'sources/icons/{themeFolder}/icons8-align-left-96.png'))
        self.positionLeftButton.setIconSize(QSize(20, 20))
        self.positionLeftButton.setCheckable(True)
        self.positionCenterButton = QPushButton()
        self.positionCenterButton.setIcon(QIcon(f'sources/icons/{themeFolder}/icons8-align-center-96.png'))
        self.positionCenterButton.setIconSize(QSize(20, 20))
        self.positionCenterButton.setCheckable(True)
        self.positionRightButton = QPushButton()
        self.positionRightButton.setIcon(QIcon(f'sources/icons/{themeFolder}/icons8-align-right-96.png'))
        self.positionRightButton.setIconSize(QSize(20, 20))
        self.positionRightButton.setCheckable(True)
        self.positionButtonGroup.addButton(self.positionLeftButton)
        self.positionButtonGroup.addButton(self.positionCenterButton)
        self.positionButtonGroup.addButton(self.positionRightButton)
        self.positionButtonGroup.setExclusive(True)
        alignment = indicator.label.alignment() if self.indicator is not None else label.alignment()
        if alignment & Qt.AlignLeft:
            self.positionLeftButton.setChecked(True)
        elif alignment & Qt.AlignHCenter:
            self.positionCenterButton.setChecked(True)
        elif alignment & Qt.AlignRight:
            self.positionRightButton.setChecked(True)

        # TOP NAME AND RETURN BUTTON
        self.returnButton = QPushButton()
        self.returnButton.setIcon(QIcon(f'sources/icons/{themeFolder}/icons8-back-96'))
        self.returnButton.setIconSize(QSize(20, 20))
        self.returnButton.setStyleSheet("background-color: transparent;")
        self.returnButton.clicked.connect(self.returnButtonPressed)
        self.nameLineEdit = QLineEdit(self)
        self.nameLineEdit.setText(self.name)
        self.nameLineEdit.textChanged.connect(self.onLineEditChange)

        # MAIN LAYOUT
        topLayout = QHBoxLayout()
        topLayout.addWidget(self.returnButton)
        topLayout.addWidget(self.nameLineEdit)
        valueLayout = QHBoxLayout()
        valueLayout.addWidget(QLabel("Value: "))
        valueLayout.addWidget(self.argumentEdit)
        valueLayout.addWidget(self.selectionButton)
        positionLayout = QHBoxLayout()
        positionLayout.addWidget(self.positionLeftButton)
        positionLayout.addWidget(self.positionCenterButton)
        positionLayout.addWidget(self.positionRightButton)
        fontLayout = QGridLayout()
        fontLayout.addWidget(fontSizeLabel, 0, 0)
        fontLayout.addWidget(self.fontSizeSpinBox, 0, 1)
        fontLayout.addWidget(fontModelLabel, 1, 0)
        fontLayout.addWidget(self.fontModelComboBox, 1, 1)
        mainLayout = QVBoxLayout()
        mainLayout.addLayout(topLayout)
        mainLayout.addLayout(valueLayout)
        mainLayout.addWidget(self.unitCheckbox)
        mainLayout.addLayout(positionLayout)
        mainLayout.addLayout(fontLayout)
        self.setLayout(mainLayout)

    def onLineEditChange(self):
        self.name = self.nameLineEdit.text()

    def returnButtonPressed(self):
        self.goBackToGrid.emit()

    def changeTheme(self, darkTheme=False):
        themeFolder = 'dark-theme' if darkTheme else 'light-theme'
        self.positionLeftButton.setIcon(QIcon(f'sources/icons/{themeFolder}/icons8-align-left-96.png'))
        self.positionCenterButton.setIcon(QIcon(f'sources/icons/{themeFolder}/icons8-align-center-96.png'))
        self.positionRightButton.setIcon(QIcon(f'sources/icons/{themeFolder}/icons8-align-right-96.png'))
        self.returnButton.setIcon(QIcon(f'sources/icons/{themeFolder}/icons8-back-96'))

    def openArgumentSelector(self):
        dialog = ArgumentSelector(self.currentDir, self)
        result = dialog.exec_()
        if result == QDialog.Accepted:
            self.argumentUnit = dialog.argumentUnit
            if self.argumentUnit is None:
                self.unitCheckbox.setEnabled(False)
                self.unitCheckbox.setChecked(False)
            else:
                self.unitCheckbox.setEnabled(True)
                self.unitCheckbox.setChecked(True)
            self.argumentEdit.setText(dialog.selectedArgument)
            self.argumentEdit.adjustSize()
