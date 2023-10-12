######################## IMPORTS ########################
from ecom.datatypes import TypeInfo

# ------------------- PyQt Modules -------------------- #
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from sources.common.widgets.Widgets import ValueWidget
# --------------------- Sources ----------------------- #
from sources.databases.balloondata import BalloonPackageDatabase


######################## CLASSES ########################
class ConstantsWidget(QMainWindow):
    def __init__(self, database: BalloonPackageDatabase):
        super(QMainWindow, self).__init__()
        self.newConfigWindow = None
        self.configTypeSelector = None
        self.database = database
        self.basicTypes = [baseType.value for baseType in TypeInfo.BaseType]
        self.rowWidgets = {'SELECTION': [], 'NAME': [], 'VALUE': [],
                           'TYPE': [], 'DESCRIPTION': []}
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
        self.buttonAddConstant = QPushButton(self.buttonWidget)
        self.buttonAddConstant.setIcon(QIcon('sources/icons/light-theme/icons8-add-96.png'))
        self.buttonAddConstant.setText('ADD CONSTANT')
        self.buttonDeleteConstant = QPushButton('', self.buttonWidget)
        self.buttonDeleteConstant.setIcon(QIcon(QPixmap('sources/icons/light-theme/icons8-remove-96.png')))
        self.buttonLayout = QHBoxLayout(self.buttonWidget)
        self.buttonLayout.addWidget(self.buttonAddConstant)
        self.buttonLayout.addWidget(self.buttonDeleteConstant)
        self.buttonAddConstant.clicked.connect(self.addNewConstant)
        self.buttonDeleteConstant.clicked.connect(self.removeSelected)

        self.centralLayout.addWidget(self.buttonWidget)
        self.centralLayout.addWidget(self.scrollArea)
        self.setCentralWidget(self.centralWidget)
        self.fillTable()
        self.show()

    def addConstantRow(self, name='', value='', constantType=TypeInfo.BaseType.INT8.value, description=''):
        newRowCount = len(self.rowWidgets['SELECTION']) + 1
        self.rowWidgets['SELECTION'].append(self.generateCheckBox())
        self.rowWidgets['NAME'].append(self.generateLabel(name))
        self.rowWidgets['VALUE'].append(self.generateValueEdit(constantType, str(value)))
        self.rowWidgets['TYPE'].append(self.generateTypePushButton(constantType, newRowCount - 1))
        self.rowWidgets['DESCRIPTION'].append(self.generateLineEdit(description))
        self.tableWidgetLayout.addWidget(self.rowWidgets['SELECTION'][-1], newRowCount, 0, 1, 1)
        self.tableWidgetLayout.addWidget(self.rowWidgets['NAME'][-1], newRowCount, 1, 1, 1)
        self.tableWidgetLayout.addWidget(self.rowWidgets['VALUE'][-1], newRowCount, 2, 1, 1)
        self.tableWidgetLayout.addWidget(self.rowWidgets['TYPE'][-1], newRowCount, 3, 1, 1)
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

    def generateLineEdit(self, textContent):
        lineEdit = QLineEdit(self.tableWidget)
        lineEdit.setText(textContent)
        lineEdit.textChanged.connect(self.descriptionChanged)
        return lineEdit

    def generateValueEdit(self, constantType=TypeInfo.BaseType.INT8.value, value=''):
        if constantType not in self.basicTypes:  # Must be in Units... Hopefully...
            unitList = [unitName for unitName, unitVariants in self.database.units.items()]
            if constantType not in unitList:  # Unknown Unit
                return QWidget(self.tableWidget)
            else:
                constantType = self.database.units[constantType][0].baseTypeName
        valueWidget = ValueWidget(constantType, value)
        return valueWidget

    def generateTypePushButton(self, textContent, i):
        typeButton = QPushButton(self.tableWidget)
        unitList = [unitName for unitName, unitVariants in self.database.units.items()]
        acceptedTypes = self.basicTypes + unitList + self.database.getSharedDataTypes()
        if textContent not in acceptedTypes:  # Degenerate Type
            typeButton.setStyleSheet('QPushButton {color: red;}')
        typeButton.setText(textContent)
        typeButton.clicked.connect(lambda: self.openAvailableTypes(i))
        return typeButton

    def cleanTable(self):
        for i in reversed(range(1, self.tableWidgetLayout.count())):
            self.tableWidgetLayout.itemAt(i).widget().setParent(None)
        self.rowWidgets = {'SELECTION': [], 'NAME': [], 'VALUE': [],
                           'TYPE': [], 'DESCRIPTION': []}

    def fillTable(self):
        ### ADD HEADER ###
        self.tableWidgetLayout.addWidget(self.generateLabel(''), 0, 0, 1, 1)
        self.tableWidgetLayout.addWidget(self.generateLabel('NAME'), 0, 1, 1, 1)
        self.tableWidgetLayout.addWidget(self.generateLabel('TYPE'), 0, 2, 1, 1)
        self.tableWidgetLayout.addWidget(self.generateLabel('DEFAULT'), 0, 3, 1, 1)
        self.tableWidgetLayout.addWidget(self.generateLabel('DESCRIPTION'), 0, 4, 1, 1)
        ### ADD ROWS ###
        for constantName, constant in self.database.constants.items():
            self.addConstantRow(name=constantName, constantType=constant.type.baseTypeName,
                                value=constant.value, description=constant.description)

    def addNewConstant(self):
        pass

    def removeSelected(self):
        pass

    def descriptionChanged(self):
        pass



