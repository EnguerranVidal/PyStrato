######################## IMPORTS ########################
import dataclasses
from ecom.datatypes import TypeInfo

# ------------------- PyQt Modules -------------------- #
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

# --------------------- Sources ----------------------- #
from sources.common.Widgets import TypeSelector
from sources.databases.balloondata import BalloonPackageDatabase


######################## CLASSES ########################
class TelemetriesWidget(QStackedWidget):
    def __init__(self, database: BalloonPackageDatabase):
        super(QStackedWidget, self).__init__()
        self.newTelemetryWindow = None
        self.database = database

        self.telemetriesWidget = QWidget(self)
        self.telemetriesLayout = QVBoxLayout(self.telemetriesWidget)

        # -------- Scrollable Area to display Telemetries
        self.scrollArea = QScrollArea(self.telemetriesWidget)
        self.scrollArea.setWidgetResizable(True)
        self.tableWidget = QWidget()
        self.tableWidget.setGeometry(QRect(0, 0, 780, 539))
        self.tableWidgetLayout = QGridLayout(self.tableWidget)
        self.tableWidgetLayout.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.scrollArea.setWidget(self.tableWidget)

        self.buttonWidget = QWidget()
        self.buttonAddTelemetry = QPushButton(self.buttonWidget)
        self.buttonAddTelemetry.setIcon(QIcon('sources/icons/light-theme/icons8-add-96.png'))
        self.buttonAddTelemetry.setText('ADD TELEMETRY')
        self.buttonDeleteTelemetry = QPushButton('', self.buttonWidget)
        self.buttonDeleteTelemetry.setIcon(QIcon(QPixmap('sources/icons/light-theme/icons8-remove-96.png')))
        self.buttonLayout = QHBoxLayout(self.buttonWidget)
        self.buttonLayout.addWidget(self.buttonAddTelemetry)
        self.buttonLayout.addWidget(self.buttonDeleteTelemetry)

        self.buttonAddTelemetry.clicked.connect(self.addNewTelemetry)
        self.buttonDeleteTelemetry.clicked.connect(self.removeSelected)

        self.telemetriesLayout.addWidget(self.buttonWidget)
        self.telemetriesLayout.addWidget(self.scrollArea)

        self.mainLayout = QVBoxLayout()
        self.mainLayout.setAlignment(Qt.AlignCenter)
        self.setLayout(self.mainLayout)
        self.addWidget(self.telemetriesWidget)

        self.rowWidgets = {'SELECTION': [], 'NAME': [], 'ARGUMENTS': [], 'DESCRIPTION': []}
        self.argumentEditors = []

        self.fillTable()
        self.show()

    def fillTable(self):
        ### ADD HEADER ###
        self.tableWidgetLayout.addWidget(self.generateLabel(''), 0, 0, 1, 1)
        self.tableWidgetLayout.addWidget(self.generateLabel('NAME'), 0, 1, 1, 1)
        self.tableWidgetLayout.addWidget(self.generateLabel(''), 0, 2, 1, 1)
        self.tableWidgetLayout.addWidget(self.generateLabel('DESCRIPTION'), 0, 3, 1, 1)
        ### ADD ROWS ###
        for telemetryResponseType in self.database.telemetryTypes:
            telemetryName = telemetryResponseType.id.name
            self.addTelemetryRow(name=telemetryName, description=telemetryResponseType.id.__doc__)
            self.argumentEditors.append(None)

    def cleanTable(self):
        for i in reversed(range(1, self.tableWidgetLayout.count())):
            self.tableWidgetLayout.itemAt(i).widget().setParent(None)
        self.rowWidgets = {'SELECTION': [], 'NAME': [], 'ARGUMENTS': [], 'DESCRIPTION': []}

    def addTelemetryRow(self, name='', description=''):
        newRowCount = len(self.rowWidgets['SELECTION']) + 1
        self.rowWidgets['SELECTION'].append(self.generateCheckBox())
        self.rowWidgets['NAME'].append(self.generateLabel(name))
        self.rowWidgets['ARGUMENTS'].append(self.generateArgumentButton(newRowCount - 1))
        self.rowWidgets['DESCRIPTION'].append(self.generateLineEdit(description))
        self.tableWidgetLayout.addWidget(self.rowWidgets['SELECTION'][-1], newRowCount, 0, 1, 1)
        self.tableWidgetLayout.addWidget(self.rowWidgets['NAME'][-1], newRowCount, 1, 1, 1)
        self.tableWidgetLayout.addWidget(self.rowWidgets['ARGUMENTS'][-1], newRowCount, 2, 1, 1)
        self.tableWidgetLayout.addWidget(self.rowWidgets['DESCRIPTION'][-1], newRowCount, 3, 1, 1)

    def generateLabel(self, textContent):
        label = QLabel(self.tableWidget)
        label.setText(textContent)
        # label.setFixedHeight(30)
        return label

    def generateArgumentButton(self, i):
        button = QPushButton('', self.tableWidget)
        button.setIcon(QIcon(QPixmap('sources/icons/stack-icon.svg')))
        button.clicked.connect(lambda: self.openTelemetryArguments(i))
        return button

    def generateLineEdit(self, textContent):
        lineEdit = QLineEdit(self.tableWidget)
        lineEdit.setText(textContent)
        lineEdit.textChanged.connect(self.descriptionChanged)
        return lineEdit

    def generateCheckBox(self):
        checkbox = QCheckBox(self.tableWidget)
        return checkbox

    def descriptionChanged(self):
        for i, (descriptionWidget, telemetryItem) in enumerate(
                zip(self.rowWidgets['DESCRIPTION'], self.database.telemetryTypes)):
            description = descriptionWidget.text()
            self.database.telemetryTypes[i] = dataclasses.replace(telemetryItem, description=description)

    def addNewTelemetry(self):
        self.newTelemetryWindow = NewTelemetryWindow(self.database)
        self.newTelemetryWindow.buttons.accepted.connect(self.acceptNewTelemetry)
        self.newTelemetryWindow.buttons.rejected.connect(self.newTelemetryWindow.close)
        self.newTelemetryWindow.show()

    def acceptNewTelemetry(self):
        name = self.newTelemetryWindow.nameEdit.text()
        names = [telemetryResponseType.id.name for telemetryResponseType in self.database.telemetryTypes]
        if name in names:
            warning_dialog = QMessageBox()
            warning_dialog.setWindowTitle("Warning")
            warning_dialog.setWindowIcon(QIcon('sources/icons/PyGS.jpg'))
            warning_dialog.setText('This Telemetry name is already taken.')
            warning_dialog.setIcon(QMessageBox.Warning)
            warning_dialog.setStandardButtons(QMessageBox.Ok)
            warning_dialog.exec_()
            return
        else:
            self.database.addTelemetry(name=name)
            # TODO ERROR when adding telemetry : not recognizing 'name'
            self.addTelemetryRow(name, description='')

    def removeSelected(self):
        states = [checkbox.isChecked() for checkbox in self.rowWidgets['SELECTION']]
        telemetriesIndices = [i for i in range(len(states)) if states[i]]
        if len(telemetriesIndices) != 0:
            # -------- Removing selected units
            telemetriesIndices.reverse()
            for i in telemetriesIndices:
                self.database.telemetryTypes.pop(i)
            # -------- Refreshing Table
            self.cleanTable()
            self.fillTable()

    def openTelemetryArguments(self, i):
        if self.argumentEditors[i] is None:
            telemetryType = self.database.telemetryTypes[i]
            argumentEditor = TelemetryArgumentEditor(self.database, telemetryType)
            argumentEditor.goBackToTelemetry.connect(self.goBackToMainEditor)
            self.argumentEditors[i] = argumentEditor
        self.addWidget(self.argumentEditors[i])
        self.setCurrentWidget(self.argumentEditors[i])

    def goBackToMainEditor(self):
        self.setCurrentWidget(self.telemetriesWidget)


class TelemetryArgumentEditor(QWidget):
    goBackToTelemetry = pyqtSignal()

    def __init__(self, database: BalloonPackageDatabase, telemetryType):
        super(QWidget, self).__init__()
        self.configTypeSelector = None
        self.newArgumentWindow = None
        self.database = database
        self.basicTypes = [baseType.value for baseType in TypeInfo.BaseType]
        self.telemetryType = telemetryType
        self.telemetryName = self.telemetryType.id.name

        self.argumentsWidget = QWidget(self)
        self.argumentsLayout = QVBoxLayout(self.argumentsWidget)

        # -------- Scrollable Area to display Telemetries
        self.scrollArea = QScrollArea(self.argumentsWidget)
        self.scrollArea.setWidgetResizable(True)
        self.tableWidget = QWidget()
        self.tableWidget.setGeometry(QRect(0, 0, 780, 539))
        self.tableWidgetLayout = QGridLayout(self.tableWidget)
        self.tableWidgetLayout.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.scrollArea.setWidget(self.tableWidget)

        self.buttonWidget = QWidget()
        self.buttonAddArgument = QPushButton(self.buttonWidget)
        self.buttonAddArgument.setIcon(QIcon('sources/icons/light-theme/icons8-add-96.png'))
        self.buttonAddArgument.setText('ADD ARGUMENT')
        self.buttonDeleteArgument = QPushButton('', self.buttonWidget)
        self.buttonDeleteArgument.setIcon(QIcon(QPixmap('sources/icons/light-theme/icons8-remove-96.png')))
        self.buttonLayout = QHBoxLayout(self.buttonWidget)
        self.buttonLayout.addWidget(self.buttonAddArgument)
        self.buttonLayout.addWidget(self.buttonDeleteArgument)

        self.buttonAddArgument.clicked.connect(self.addNewArgument)
        self.buttonDeleteArgument.clicked.connect(self.removeSelected)

        self.argumentsLayout.addWidget(self.buttonWidget)
        self.argumentsLayout.addWidget(self.scrollArea)

        self.rowWidgets = {'SELECTION': [], 'NAME': [], 'TYPE': [], 'DESCRIPTION': []}

        # --------- Top Layout --------
        self.topLayout = QHBoxLayout()
        # Create the return button and set its icon
        self.returnButton = QPushButton()
        self.returnButton.setIcon(QIcon('sources/icons/light-theme/icons8-back-96'))
        self.returnButton.setIconSize(QSize(20, 20))
        self.returnButton.setStyleSheet("background-color: transparent;")
        self.returnButton.clicked.connect(self.returnButtonPressed)
        # Create the name valueLabel and set its text
        self.telemetryNameLabel = QLabel(self)
        self.telemetryNameLabel.setText(self.telemetryName)
        # Add the widgets to the top layout
        self.topLayout.addWidget(self.returnButton)
        self.topLayout.addWidget(self.telemetryNameLabel)

        self.mainLayout = QVBoxLayout()
        self.mainLayout.addLayout(self.topLayout)
        self.mainLayout.addWidget(self.argumentsWidget)
        self.setLayout(self.mainLayout)

        self.fillTable()
        self.show()

    def fillTable(self):
        ### ADD HEADER ###
        self.tableWidgetLayout.addWidget(self.generateLabel(''), 0, 0, 1, 1)
        self.tableWidgetLayout.addWidget(self.generateLabel('NAME'), 0, 1, 1, 1)
        self.tableWidgetLayout.addWidget(self.generateLabel(''), 0, 2, 1, 1)
        self.tableWidgetLayout.addWidget(self.generateLabel('DESCRIPTION'), 0, 3, 1, 1)
        ### ADD ROWS ###
        for dataPoint in self.telemetryType.data:
            dataPointName = dataPoint.name
            dataPointType = self.database.getTypeName(dataPoint.type)
            dataPointDescription = dataPoint.description
            self.addArgumentRow(name=dataPointName, configType=dataPointType, description=dataPointDescription)

    def cleanTable(self):
        for i in reversed(range(1, self.tableWidgetLayout.count())):
            self.tableWidgetLayout.itemAt(i).widget().setParent(None)
        self.rowWidgets = {'SELECTION': [], 'NAME': [], 'TYPE': [], 'DESCRIPTION': []}

    def addArgumentRow(self, name='', configType=TypeInfo.BaseType.INT8.value, description=''):
        newRowCount = len(self.rowWidgets['SELECTION']) + 1
        self.rowWidgets['SELECTION'].append(self.generateCheckBox())
        self.rowWidgets['NAME'].append(self.generateLabel(name))
        self.rowWidgets['TYPE'].append(self.generateArgumentTypeButton(configType, newRowCount - 1))
        self.rowWidgets['DESCRIPTION'].append(self.generateDescriptionEdit(description))
        self.tableWidgetLayout.addWidget(self.rowWidgets['SELECTION'][-1], newRowCount, 0, 1, 1)
        self.tableWidgetLayout.addWidget(self.rowWidgets['NAME'][-1], newRowCount, 1, 1, 1)
        self.tableWidgetLayout.addWidget(self.rowWidgets['TYPE'][-1], newRowCount, 2, 1, 1)
        self.tableWidgetLayout.addWidget(self.rowWidgets['DESCRIPTION'][-1], newRowCount, 3, 1, 1)

    def generateLabel(self, textContent):
        label = QLabel(self.tableWidget)
        label.setText(textContent)
        return label

    def generateArgumentTypeButton(self, textContent, i):
        typeButton = QPushButton(self.tableWidget)
        unitList = [unitName for unitName, unitVariants in self.database.units.items()]
        acceptedTypes = self.basicTypes + unitList + self.database.getSharedDataTypes()
        if textContent not in acceptedTypes:  # Degenerate Type
            typeButton.setStyleSheet('QPushButton {color: red;}')
        typeButton.setText(textContent)
        typeButton.clicked.connect(lambda: self.openAvailableTypes(i))
        return typeButton

    def generateDescriptionEdit(self, textContent):
        lineEdit = QLineEdit(self.tableWidget)
        lineEdit.setText(textContent)
        lineEdit.textChanged.connect(self.descriptionChanged)
        return lineEdit

    def generateCheckBox(self):
        checkbox = QCheckBox(self.tableWidget)
        return checkbox

    def descriptionChanged(self):
        for i, (descriptionWidget, telemetryItem) in enumerate(
                zip(self.rowWidgets['DESCRIPTION'], self.database.telemetryTypes)):
            description = descriptionWidget.text()
            self.database.telemetryTypes[i] = dataclasses.replace(telemetryItem, description=description)

    def addNewArgument(self):
        self.newArgumentWindow = NewTelemetryArgumentWindow(self.database, self.telemetryName)
        self.newArgumentWindow.buttons.accepted.connect(self.acceptNewArgument)
        self.newArgumentWindow.buttons.rejected.connect(self.newArgumentWindow.close)
        self.newArgumentWindow.show()

    def acceptNewArgument(self):
        name = self.newArgumentWindow.nameEdit.text()
        names = [telemetryResponseType.id.name for telemetryResponseType in self.database.telemetryTypes]
        if name in names:
            warning_dialog = QMessageBox()
            warning_dialog.setWindowTitle("Warning")
            warning_dialog.setWindowIcon(QIcon('sources/icons/PyGS.jpg'))
            warning_dialog.setText('This Telemetry name is already taken.')
            warning_dialog.setIcon(QMessageBox.Warning)
            warning_dialog.setStandardButtons(QMessageBox.Ok)
            warning_dialog.exec_()
            return
        else:
            self.database.addTelemetry(name=name)
            # TODO ERROR when adding telemetry : not recognizing 'name'
            self.addArgumentRow(name, description='')

    def removeSelected(self):
        states = [checkbox.isChecked() for checkbox in self.rowWidgets['SELECTION']]
        telemetriesIndices = [i for i in range(len(states)) if states[i]]
        if len(telemetriesIndices) != 0:
            # -------- Removing selected units
            telemetriesIndices.reverse()
            for i in telemetriesIndices:
                self.database.telemetryTypes.pop(i)
            # -------- Refreshing Table
            self.cleanTable()
            self.fillTable()

    def returnButtonPressed(self):
        self.goBackToTelemetry.emit()
    
    def openAvailableTypes(self, i):
        configType = self.rowWidgets['TYPE'][i].text()
        self.configTypeSelector = TypeSelector(configType, database=self.database, sharedDataTypes=True)
        self.configTypeSelector.buttons.accepted.connect(lambda: self.acceptTypeChange(i))
        self.configTypeSelector.buttons.rejected.connect(self.configTypeSelector.close)
        self.configTypeSelector.show()


class NewTelemetryArgumentWindow(QDialog):
    def __init__(self, database, telemetryName: str):
        super().__init__()
        self.database = database
        self.setWindowTitle('Add New Argument to ' + telemetryName)
        # self.setWindowIcon(QIcon('sources/icons/PyGS.jpg'))
        self.resize(400, 100)
        self.dlgLayout = QVBoxLayout()
        self.formWidget = QWidget(self)
        self.formLayout = QFormLayout()
        self.nameEdit = QLineEdit()
        self.defaultValueEdit = QLineEdit()
        self.formLayout.addRow('Name:', self.nameEdit)
        self.formWidget.setLayout(self.formLayout)
        self.dlgLayout.addWidget(self.formWidget)
        self.buttons = QDialogButtonBox()
        self.buttons.setStandardButtons(QDialogButtonBox.Cancel | QDialogButtonBox.Ok)
        self.dlgLayout.addWidget(self.buttons)
        self.setLayout(self.dlgLayout)


class NewTelemetryWindow(QDialog):
    def __init__(self, database):
        super().__init__()
        self.database = database
        self.setWindowTitle('Add New Telemetry')
        # self.setWindowIcon(QIcon('sources/icons/PyGS.jpg'))
        self.resize(400, 100)
        self.dlgLayout = QVBoxLayout()
        self.formWidget = QWidget(self)
        self.formLayout = QFormLayout()
        self.nameEdit = QLineEdit()
        self.defaultValueEdit = QLineEdit()
        self.formLayout.addRow('Name:', self.nameEdit)
        self.formWidget.setLayout(self.formLayout)
        self.dlgLayout.addWidget(self.formWidget)
        self.buttons = QDialogButtonBox()
        self.buttons.setStandardButtons(QDialogButtonBox.Cancel | QDialogButtonBox.Ok)
        self.dlgLayout.addWidget(self.buttons)
        self.setLayout(self.dlgLayout)
