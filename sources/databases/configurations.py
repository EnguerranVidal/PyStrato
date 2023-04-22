######################## IMPORTS ########################
import dataclasses
from ecom.datatypes import TypeInfo

# ------------------- PyQt Modules -------------------- #
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from sources.common.Widgets import ValueWidget, TypeSelector
# --------------------- Sources ----------------------- #
from sources.databases.balloondata import BalloonPackageDatabase, serializeTypedValue


######################## CLASSES ########################
class ConfigurationsWidget(QMainWindow):
    def __init__(self, database: BalloonPackageDatabase):
        super(QMainWindow, self).__init__()
        self.newConfigWindow = None
        self.configTypeSelector = None
        self.database = database
        self.basicTypes = [baseType.value for baseType in TypeInfo.BaseType]
        self.rowWidgets = {'SELECTION': [], 'CONFIG NAME': [], 'CONFIG TYPE': [],
                           'DEFAULT VALUE': [], 'DESCRIPTION': []}
        self.centralWidget = QWidget(self)
        self.centralLayout = QVBoxLayout(self.centralWidget)

        self.scrollArea = QScrollArea(self.centralWidget)
        self.scrollArea.setWidgetResizable(True)
        self.tableWidget = QWidget()
        self.tableWidget.setGeometry(QRect(0, 0, 780, 539))
        self.tableWidgetLayout = QGridLayout(self.tableWidget)
        self.tableWidgetLayout.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.scrollArea.setWidget(self.tableWidget)

        self.buttonWidget = QWidget()
        self.buttonAddConfig = QPushButton(self.buttonWidget)
        self.buttonAddConfig.setIcon(QIcon('sources/icons/light-theme/icons8-add-96.png'))
        self.buttonAddConfig.setText('ADD CONFIG')
        self.buttonDeleteConfig = QPushButton('', self.buttonWidget)
        self.buttonDeleteConfig.setIcon(QIcon(QPixmap('sources/icons/light-theme/icons8-remove-96.png')))
        self.buttonLayout = QHBoxLayout(self.buttonWidget)
        self.buttonLayout.addWidget(self.buttonAddConfig)
        self.buttonLayout.addWidget(self.buttonDeleteConfig)
        self.buttonAddConfig.clicked.connect(self.addNewConfig)
        self.buttonDeleteConfig.clicked.connect(self.removeSelected)

        self.centralLayout.addWidget(self.buttonWidget)
        self.centralLayout.addWidget(self.scrollArea)
        self.setCentralWidget(self.centralWidget)
        self.fillTable()
        self.show()

    def addConfigurationRow(self, name='', configType=TypeInfo.BaseType.INT8.value, defaultValue='', description=''):
        newRowCount = len(self.rowWidgets['SELECTION']) + 1
        self.rowWidgets['SELECTION'].append(self.generateCheckBox())
        self.rowWidgets['CONFIG NAME'].append(self.generateLabel(name))
        self.rowWidgets['CONFIG TYPE'].append(self.generateTypePushButton(configType, newRowCount - 1))
        self.rowWidgets['DEFAULT VALUE'].append(self.generateDefaultEdit(configType, defaultValue))
        self.rowWidgets['DESCRIPTION'].append(self.generateLineEdit(description))
        self.tableWidgetLayout.addWidget(self.rowWidgets['SELECTION'][-1], newRowCount, 0, 1, 1)
        self.tableWidgetLayout.addWidget(self.rowWidgets['CONFIG NAME'][-1], newRowCount, 1, 1, 1)
        self.tableWidgetLayout.addWidget(self.rowWidgets['CONFIG TYPE'][-1], newRowCount, 2, 1, 1)
        self.tableWidgetLayout.addWidget(self.rowWidgets['DEFAULT VALUE'][-1], newRowCount, 3, 1, 1)
        self.tableWidgetLayout.addWidget(self.rowWidgets['DESCRIPTION'][-1], newRowCount, 4, 1, 1)

    @staticmethod
    def generateCheckBox():
        checkbox = QCheckBox()
        return checkbox

    @staticmethod
    def generateLabel(textContent):
        label = QLabel()
        label.setText(textContent)
        return label

    def cleanTable(self):
        for i in reversed(range(1, self.tableWidgetLayout.count())):
            self.tableWidgetLayout.itemAt(i).widget().setParent(None)
        self.rowWidgets = {'SELECTION': [], 'CONFIG NAME': [], 'CONFIG TYPE': [],
                           'DEFAULT VALUE': [], 'DESCRIPTION': []}

    def removeSelected(self):
        # Retrieving selected units for removal
        states = [checkbox.isChecked() for checkbox in self.rowWidgets['SELECTION']]
        configIndices = [i for i in range(len(states)) if states[i]]
        if len(configIndices) != 0:
            # -------- Removing selected units
            configIndices.reverse()
            for i in configIndices:
                self.database.configurations.pop(i)
            # -------- Refreshing Table
            self.cleanTable()
            self.fillTable()

    def generateTypePushButton(self, textContent, i):
        typeButton = QPushButton(self.tableWidget)
        unitList = [unitName for unitName, unitVariants in self.database.units.items()]
        if textContent not in self.basicTypes and textContent not in unitList:  # Degenerate Type
            typeButton.setStyleSheet('QPushButton {color: red;}')
        typeButton.setText(textContent)
        typeButton.clicked.connect(lambda: self.openAvailableTypes(i))
        return typeButton

    def generateDefaultEdit(self, configType=TypeInfo.BaseType.INT8.value, defaultValue=''):
        if configType not in self.basicTypes:  # Must be in Units... Hopefully...
            unitList = [unitName for unitName, unitVariants in self.database.units.items()]
            if configType not in unitList:  # Unknown Unit
                return QWidget(self.tableWidget)
            else:
                configType = self.database.units[configType][0].baseTypeName
        valueWidget = ValueWidget(configType, defaultValue)
        return valueWidget

    def generateLineEdit(self, textContent):
        lineEdit = QLineEdit(self.tableWidget)
        lineEdit.setText(textContent)
        lineEdit.textChanged.connect(self.descriptionChanged)
        return lineEdit

    def openAvailableTypes(self, i):
        configType = self.rowWidgets['CONFIG TYPE'][i].text()
        self.configTypeSelector = TypeSelector(configType, database=self.database)
        self.configTypeSelector.buttons.accepted.connect(lambda: self.acceptTypeChange(i))
        self.configTypeSelector.buttons.rejected.connect(self.configTypeSelector.close)
        self.configTypeSelector.show()

    def acceptTypeChange(self, i):
        # CHANGING TYPE IN DATABASE
        typeName = self.configTypeSelector.selectedLabel.text()
        self.rowWidgets['CONFIG TYPE'][i].setStyleSheet('')
        self.rowWidgets['CONFIG TYPE'][i].setText(typeName)
        typeInfo = self.database.getTypeInfo(self.rowWidgets['CONFIG TYPE'][i].text())
        self.database.configurations[i] = dataclasses.replace(self.database.configurations[i], type=typeInfo)
        # CHANGING DEFAULT VALUE WIDGET
        if typeName not in self.basicTypes:  # Must be in Units... Hopefully...
            unitList = [unitName for unitName, unitVariants in self.database.units.items()]
            if typeName not in unitList:  # Unknown Unit
                return QWidget(self.tableWidget)
            else:
                typeName = self.database.units[typeName][0].baseTypeName
        oldDefaultValue = self.rowWidgets['DEFAULT VALUE'][i].value
        self.rowWidgets['DEFAULT VALUE'][i].changeCType(typeName)
        self.configTypeSelector.close()
        # CHANGING DEFAULT VALUE IN DATABASE
        defaultValue = self.rowWidgets['DEFAULT VALUE'][i].value
        if defaultValue != oldDefaultValue:
            self.database.configurations[i] = dataclasses.replace(self.database.configurations[i], defaultValue=defaultValue)

    def defaultValueChanged(self):
        for i, (defaultValueWidget, configItem) in enumerate(
                zip(self.rowWidgets['DEFAULT VALUE'], self.database.configurations)):
            if issubclass(configItem.type.type, bool):
                defaultValue = self.rowWidgts['DEFAULT VALUE'][i].currentText() == 'true'  # if bool
            else:
                try:
                    defaultValue = configItem.type.type(self.rowWidgts['DEFAULT VALUE'][i].text())  # else
                except (ValueError, TypeInfo) as error:
                    print(f'{error}')
                    return
            self.database.configurations[i] = dataclasses.replace(configItem, defaultValue=defaultValue)

    def addNewConfig(self):
        self.newConfigWindow = NewConfigWindow(self.database)
        self.newConfigWindow.buttons.accepted.connect(self.acceptNewConfig)
        self.newConfigWindow.buttons.rejected.connect(self.newConfigWindow.close)
        self.newConfigWindow.show()

    def acceptNewConfig(self):
        name = self.newConfigWindow.nameEdit.text()
        typeName = self.newConfigWindow.typePushButton.text()
        if typeName not in self.basicTypes:  # Must be in Units... Hopefully...
            unitList = [unitName for unitName, unitVariants in self.database.units.items()]
            if typeName in unitList:
                typeName = self.database.units[typeName][0].baseTypeName
        configTypeInfo = self.database.getTypeInfo(typeName)
        if issubclass(configTypeInfo.type, bool):
            defaultValue = self.newConfigWindow.defaultValueEdit.currentText() == 'true'
        else:
            defaultValue = configTypeInfo.type(self.newConfigWindow.defaultValueEdit.text())
        baseTypeInfo = TypeInfo(type=TypeInfo.lookupBaseType(typeName).type, name=typeName, baseTypeName=typeName)
        self.database.addConfiguration(name, type=baseTypeInfo, defaultValue=defaultValue)
        # TODO ERROR when adding configuration : too many arguments
        self.addConfigurationRow(name, typeName, defaultValue, description='')
        self.newConfigWindow.close()

    def descriptionChanged(self):
        for i, (descriptionWidget, configItem) in enumerate(
                zip(self.rowWidgets['DESCRIPTION'], self.database.configurations)):
            description = descriptionWidget.text()
            self.database.configurations[i] = dataclasses.replace(configItem, description=description)

    def fillTable(self):
        ### ADD HEADER ###
        self.tableWidgetLayout.addWidget(self.generateLabel(''), 0, 0, 1, 1)
        self.tableWidgetLayout.addWidget(self.generateLabel('NAME'), 0, 1, 1, 1)
        self.tableWidgetLayout.addWidget(self.generateLabel('TYPE'), 0, 2, 1, 1)
        self.tableWidgetLayout.addWidget(self.generateLabel('DEFAULT'), 0, 3, 1, 1)
        self.tableWidgetLayout.addWidget(self.generateLabel('DESCRIPTION'), 0, 4, 1, 1)
        ### ADD ROWS ###
        for configuration in self.database.configurations:
            typeName = self.database.getTypeName(configuration.type)
            defaultValue = serializeTypedValue(configuration.defaultValue, configuration.type.type)
            self.addConfigurationRow(name=configuration.name, configType=typeName,
                                     defaultValue=defaultValue, description=configuration.description)


class NewConfigWindow(QDialog):
    def __init__(self, database):
        super().__init__()
        self.basicTypes = [baseType.value for baseType in TypeInfo.BaseType]
        self.database = database
        self.configTypeSelector = None
        self.setWindowTitle('Add New Configuration')
        # self.setWindowIcon(QIcon('sources/icons/PyGS.jpg'))
        self.resize(400, 100)
        self.dlgLayout = QVBoxLayout()
        self.formWidget = QWidget(self)
        self.formLayout = QFormLayout()
        self.nameEdit = QLineEdit()
        self.typePushButton = QPushButton(self.basicTypes[0])
        self.typePushButton.clicked.connect(self.openAvailableTypes)
        self.formLayout.addRow('Name:', self.nameEdit)
        self.formLayout.addRow('Type:', self.typePushButton)
        self.formLayout.addRow('', QWidget())
        self.formWidget.setLayout(self.formLayout)
        self.dlgLayout.addWidget(self.formWidget)
        self.buttons = QDialogButtonBox()
        self.buttons.setStandardButtons(QDialogButtonBox.Cancel | QDialogButtonBox.Ok)
        self.dlgLayout.addWidget(self.buttons)
        self.setLayout(self.dlgLayout)

    def openAvailableTypes(self):
        self.configTypeSelector = TypeSelector(self.typePushButton.text(), database=self.database)
        self.configTypeSelector.buttons.accepted.connect(self.acceptTypeChange)
        self.configTypeSelector.buttons.rejected.connect(self.configTypeSelector.close)
        self.configTypeSelector.show()

    def acceptTypeChange(self):
        typeName = self.configTypeSelector.selectedLabel.text()
        self.typePushButton.setText(typeName)
        typeInfo = self.database.getTypeInfo(self.typePushButton.text())
        # TODO Add Compatibility issue function
        defaultValue = typeInfo.type()
        self.formLayout.removeWidget(self.defaultValueEdit)
        self.defaultValueEdit = self.generateDefaultEdit(typeName, str(defaultValue))
        self.formLayout.addWidget(self.defaultValueEdit)
        self.configTypeSelector.close()

    def generateDefaultEdit(self, configType=TypeInfo.BaseType.INT8.value, defaultValue=''):
        if configType not in self.basicTypes:  # Must be in Units... Hopefully...
            unitList = [unitName for unitName, unitVariants in self.database.units.items()]
            if configType not in unitList:  # Unknown Unit
                return QWidget()
            else:
                configType = self.database.units[configType][0].baseTypeName
        configTypeInfo = self.database.getTypeInfo(configType)
        if issubclass(configTypeInfo.type, bool):
            comboBox = QComboBox()
            comboBox.addItems(['true', 'false'])
            if defaultValue in ['true', 'false']:
                comboBox.setCurrentIndex(['true', 'false'].index(defaultValue))
            else:
                comboBox.setCurrentIndex(0)
            return comboBox
        else:
            # TODO add minimum maximum ranges and types to comply with C types
            lineEdit = QLineEdit()
            lineEdit.setText(str(defaultValue))
            if issubclass(configTypeInfo.type, int):
                # maxRange = configTypeInfo.getMaxNumericalValue(self.database)
                # minRange = configTypeInfo.getMinNumericalValue(self.database)
                # onlyInt = QIntValidator(minRange, maxRange)
                onlyInt = QIntValidator()
                lineEdit.setValidator(onlyInt)
            elif issubclass(configTypeInfo.type, float):
                onlyFloat = QDoubleValidator()
                locale = QLocale(QLocale.English, QLocale.UnitedStates)
                onlyFloat.setLocale(locale)
                onlyFloat.setNotation(QDoubleValidator.StandardNotation)
                lineEdit.setValidator(onlyFloat)
            return lineEdit
