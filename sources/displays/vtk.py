######################## IMPORTS ########################
import os
from functools import reduce
import pyvista as pv
from pyvistaqt import QtInteractor
import operator

# ------------------- PyQt Modules -------------------- #
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

# --------------------- Sources ----------------------- #
from sources.common.utilities.fileSystem import loadSettings
from sources.common.utilities.rotations import quaternionToEuler321
from sources.common.widgets.Widgets import ArgumentSelector
from sources.common.widgets.basic import BasicDisplay
from sources.databases.units import DefaultUnitsCatalogue


######################## CLASSES ########################
class VtkDisplay(BasicDisplay):
    def __init__(self, path, parent=None):
        super().__init__(path, parent)
        self.content, self.settings = None, loadSettings('settings')
        self.catalogue = DefaultUnitsCatalogue()

        # VTK DISPLAY WIDGET
        self.meshFilePath = ''
        self.vtkMesh, self.viewedMesh = None, None
        self.vtkDisplay = QtInteractor(self)
        self.rotation = {'SET_ROTATION': False, 'ROTATION_TYPE': 'EULER', 'ARGUMENTS': [''] * 7, 'UNITS': [None] * 7}
        self.vtkDisplay.set_background('black' if self.settings['DARK_THEME'] else 'white')
        self.axes = self.vtkDisplay.add_axes(color='white'if self.settings['DARK_THEME'] else 'black')

        # MAIN LAYOUT
        layout = QVBoxLayout(self)
        layout.addWidget(self.vtkDisplay)
        self.settingsWidget = VtkDisplayEditDialog(self.currentDir, self)

    def getDescription(self):
        rotation = {key: value for key, value in self.rotation.items() if key != 'UNITS'}
        displayDescription = {'DISPLAY_TYPE': 'VTK_DISPLAY', 'MESH_PATH': self.meshFilePath, 'ROTATION': rotation}
        return displayDescription

    def applyDescription(self, description):
        self.meshFilePath = description['MESH_PATH']
        if not os.path.exists(self.meshFilePath):
            self.meshFilePath = ''
        else:
            self.vtkMesh = pv.read(self.meshFilePath)
            self.viewedMesh = self.vtkDisplay.add_mesh(self.vtkMesh)
        self.settingsWidget = VtkDisplayEditDialog(self.currentDir, self)
        self.rotation = description['ROTATION']
        self.retrieveArgumentUnits()

    def applyChanges(self, editWidget):
        editWidget = self.settingsWidget
        self.meshFilePath = editWidget.meshFileEdit.text()
        if os.path.exists(self.meshFilePath):
            self.vtkMesh = pv.read(self.meshFilePath)
            self.vtkDisplay.add_mesh(self.vtkMesh)
        self.rotation = {'SET_ROTATION': editWidget.rotationCheckbox.isChecked(),
                         'ROTATION_TYPE': 'EULER' if editWidget.rotationTypeComboBox.currentIndex() == 0 else 'QUATERNION',
                         'ARGUMENTS': [editWidget.rollEdit.text(), editWidget.pitchEdit.text(),
                                       editWidget.yawEdit.text(), editWidget.qwEdit.text(),
                                       editWidget.qxEdit.text(), editWidget.qyEdit.text(),
                                       editWidget.qzEdit.text()],
                         'UNITS': editWidget.argumentUnits}
        self.updateContent()

    def updateContent(self, content=None):
        self.generalSettings = loadSettings('settings')
        if content is not None:
            self.content = content
            if self.rotation['ROTATION_TYPE'] == 'EULER' and self.rotation['SET_ROTATION']:
                roll, pitch, yaw = self.rotation['ARGUMENTS'][0], self.rotation['ARGUMENTS'][1], self.rotation['ARGUMENTS'][2]
                rollMapping, pitchMapping, yawMapping = roll.split('/'), pitch.split('/'), yaw.split('/')
                valueRoll = reduce(operator.getitem, rollMapping, content.storage)
                valuePitch = reduce(operator.getitem, pitchMapping, content.storage)
                valueYaw = reduce(operator.getitem, yawMapping, content.storage)
            elif self.rotation['ROTATION_TYPE'] == 'QUATERNION' and self.rotation['SET_ROTATION']:
                qW, qX = self.rotation['ARGUMENTS'][3], self.rotation['ARGUMENTS'][4]
                qY, qZ = self.rotation['ARGUMENTS'][5], self.rotation['ARGUMENTS'][6]
                qwMapping, qxMapping, qyMapping, qzMapping = qW.split('/'), qX.split('/'), qY.split('/'), qZ.split('/')
                valueQw = reduce(operator.getitem, qwMapping, content.storage)
                valueQx = reduce(operator.getitem, qxMapping, content.storage)
                valueQy = reduce(operator.getitem, qyMapping, content.storage)
                valueQz = reduce(operator.getitem, qzMapping, content.storage)
                valueRoll, valuePitch, valueYaw = quaternionToEuler321(valueQw, valueQx, valueQy, valueQz, degrees=True)

    def changeTheme(self):
        self.settings = loadSettings('settings')
        self.vtkDisplay.set_background('black' if self.settings['DARK_THEME'] else 'white')
        self.vtkDisplay.remove_actor(self.axes)
        self.axes = self.vtkDisplay.add_axes(color='white' if self.settings['DARK_THEME'] else 'black')
        self.settingsWidget.changeTheme(darkTheme=self.settings['DARK_THEME'])

    def generateSettingsWidget(self):
        self.settingsWidget = VtkDisplayEditDialog(self.currentDir, self)

    def retrieveArgumentUnits(self, arguments=None):
        argumentUnits = []
        if arguments is None:
            arguments = self.rotation['ARGUMENTS']

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
        for i, argument in enumerate(arguments):

            argument = argument.split('/')
            database, telemetry, argument = argument[0], argument[1], argument[2:]
            selectedTypes, selectedUnits = dialog.databases[database].nestedPythonTypes(telemetry, (int, float))
            unitName = getUnit(selectedUnits, argument)
            argumentUnits[i] = dialog.databases[database].units[unitName][0] if unitName is not None else None
        self.rotation['UNITS'] = argumentUnits


class VtkDisplayEditDialog(QWidget):
    def __init__(self, path, parent: VtkDisplay):
        super().__init__(parent)
        self.settings = loadSettings('settings')
        self.argumentUnits = parent.rotation['UNITS']
        themeFolder = 'dark-theme' if self.settings['DARK_THEME'] else 'light-theme'
        meshPixMap = QPixmap(f'sources/icons/{themeFolder}/icons8-file-explorer-96.png').scaled(25, 25)
        selectionButtonPixmap = QPixmap(f'sources/icons/{themeFolder}/icons8-add-database-96.png').scaled(25, 25)
        self.currentDir = path
        self.hide()

        # MESH FILE EDITION
        meshFileLabel = QLabel('Mesh file: ')
        self.meshFileEdit = QLineEdit(parent.meshFilePath)
        self.meshSelectionButton = QPushButton()
        self.meshSelectionButton.setIcon(QIcon(meshPixMap))
        self.meshSelectionButton.clicked.connect(self.selectMeshFile)

        # EULER ANGLES FRAME
        self.eulerFrame = QFrame()
        self.eulerFrame.setEnabled(parent.rotation['SET_ROTATION'])
        rollLabel, pitchLabel, yawLabel = QLabel('Roll: '), QLabel('Pitch:'), QLabel('Yaw:  ')
        self.rollEdit = QLineEdit(parent.rotation['ARGUMENTS'][0])
        self.pitchEdit = QLineEdit(parent.rotation['ARGUMENTS'][1])
        self.yawEdit = QLineEdit(parent.rotation['ARGUMENTS'][2])
        self.rollButton, self.pitchButton, self.yawButton = QPushButton(), QPushButton(), QPushButton()
        self.rollButton.setIcon(QIcon(selectionButtonPixmap))
        self.pitchButton.setIcon(QIcon(selectionButtonPixmap))
        self.yawButton.setIcon(QIcon(selectionButtonPixmap))
        self.rollButton.clicked.connect(self.openArgumentSelectorRoll)
        self.pitchButton.clicked.connect(self.openArgumentSelectorPitch)
        self.yawButton.clicked.connect(self.openArgumentSelectorYaw)

        eulerFrameLayout = QGridLayout(self.eulerFrame)
        eulerFrameLayout.addWidget(rollLabel, 0, 0)
        eulerFrameLayout.addWidget(pitchLabel, 1, 0)
        eulerFrameLayout.addWidget(yawLabel, 2, 0)
        eulerFrameLayout.addWidget(self.rollEdit, 0, 1)
        eulerFrameLayout.addWidget(self.pitchEdit, 1, 1)
        eulerFrameLayout.addWidget(self.yawEdit, 2, 1)
        eulerFrameLayout.addWidget(self.rollButton, 0, 2)
        eulerFrameLayout.addWidget(self.pitchButton, 1, 2)
        eulerFrameLayout.addWidget(self.yawButton, 2, 2)

        # QUATERNION FRAME
        self.quaternionFrame = QFrame()
        self.eulerFrame.setEnabled(parent.rotation['SET_ROTATION'])
        qwLabel, qxLabel, qyLabel, qzLabel = QLabel('W: '), QLabel('X: '), QLabel('Y: '), QLabel('Z: ')
        self.qwEdit = QLineEdit(parent.rotation['ARGUMENTS'][3])
        self.qxEdit = QLineEdit(parent.rotation['ARGUMENTS'][4])
        self.qyEdit = QLineEdit(parent.rotation['ARGUMENTS'][5])
        self.qzEdit = QLineEdit(parent.rotation['ARGUMENTS'][6])
        self.qwButton, self.qxButton = QPushButton(), QPushButton()
        self.qyButton, self.qzButton = QPushButton(), QPushButton()
        self.qwButton.setIcon(QIcon(selectionButtonPixmap))
        self.qxButton.setIcon(QIcon(selectionButtonPixmap))
        self.qyButton.setIcon(QIcon(selectionButtonPixmap))
        self.qzButton.setIcon(QIcon(selectionButtonPixmap))
        self.qwButton.clicked.connect(self.openArgumentSelectorQw)
        self.qxButton.clicked.connect(self.openArgumentSelectorQx)
        self.qyButton.clicked.connect(self.openArgumentSelectorQy)
        self.qzButton.clicked.connect(self.openArgumentSelectorQz)

        quaternionFrameLayout = QGridLayout(self.quaternionFrame)
        quaternionFrameLayout.addWidget(qwLabel, 0, 0)
        quaternionFrameLayout.addWidget(qxLabel, 1, 0)
        quaternionFrameLayout.addWidget(qyLabel, 2, 0)
        quaternionFrameLayout.addWidget(qzLabel, 3, 0)
        quaternionFrameLayout.addWidget(self.qwEdit, 0, 1)
        quaternionFrameLayout.addWidget(self.qxEdit, 1, 1)
        quaternionFrameLayout.addWidget(self.qyEdit, 2, 1)
        quaternionFrameLayout.addWidget(self.qzEdit, 3, 1)
        quaternionFrameLayout.addWidget(self.qwButton, 0, 2)
        quaternionFrameLayout.addWidget(self.qxButton, 1, 2)
        quaternionFrameLayout.addWidget(self.qyButton, 2, 2)
        quaternionFrameLayout.addWidget(self.qzButton, 3, 2)

        # MESH FILE ROTATION
        self.rotationCheckbox = QCheckBox('Add Rotation')
        self.rotationCheckbox.stateChanged.connect(self.toggleRotation)
        self.rotationCheckbox.setChecked(parent.rotation['SET_ROTATION'])
        self.rotationTypeComboBox = QComboBox()
        self.rotationTypeComboBox.addItems(['Euler Angles', 'Quaternion'])
        self.rotationTypeComboBox.setEnabled(parent.rotation['SET_ROTATION'])
        self.rotationTypeComboBox.currentIndexChanged.connect(self.showRotationFrame)

        # MAIN LAYOUT
        mainLayout = QGridLayout(self)
        mainLayout.addWidget(meshFileLabel, 0, 0)
        mainLayout.addWidget(self.meshFileEdit, 0, 1)
        mainLayout.addWidget(self.meshSelectionButton, 0, 2)
        mainLayout.addWidget(self.rotationCheckbox, 1, 0)
        mainLayout.addWidget(self.rotationTypeComboBox, 1, 1)
        mainLayout.addWidget(self.eulerFrame, 2, 0, 1, 3)
        mainLayout.addWidget(self.quaternionFrame, 2, 0, 1, 3)

        # SETTING RIGHT EDITION FRAME
        self.rotationTypeComboBox.setCurrentText('Euler Angles' if parent.rotation['ROTATION_TYPE'] == 'EULER' else 'Quaternion')
        self.showRotationFrame(0 if parent.rotation['ROTATION_TYPE'] == 'EULER' else 1)

    def openArgumentSelectorRoll(self):
        dialog = ArgumentSelector(self.currentDir, self)
        result = dialog.exec_()
        if result == QMessageBox.Accepted:
            self.argumentUnits[0] = dialog.argumentUnit
            self.rollEdit.setText(dialog.selectedArgument)
            self.rollEdit.adjustSize()

    def openArgumentSelectorPitch(self):
        dialog = ArgumentSelector(self.currentDir, self)
        result = dialog.exec_()
        if result == QMessageBox.Accepted:
            self.argumentUnits[1] = dialog.argumentUnit
            self.pitchEdit.setText(dialog.selectedArgument)
            self.pitchEdit.adjustSize()

    def openArgumentSelectorYaw(self):
        dialog = ArgumentSelector(self.currentDir, self)
        result = dialog.exec_()
        if result == QMessageBox.Accepted:
            self.argumentUnits[2] = dialog.argumentUnit
            self.yawEdit.setText(dialog.selectedArgument)
            self.yawEdit.adjustSize()

    def openArgumentSelectorQw(self):
        dialog = ArgumentSelector(self.currentDir, self)
        result = dialog.exec_()
        if result == QMessageBox.Accepted:
            self.argumentUnits[3] = dialog.argumentUnit
            self.qwEdit.setText(dialog.selectedArgument)
            self.qwEdit.adjustSize()

    def openArgumentSelectorQx(self):
        dialog = ArgumentSelector(self.currentDir, self)
        result = dialog.exec_()
        if result == QMessageBox.Accepted:
            self.argumentUnits[4] = dialog.argumentUnit
            self.qxEdit.setText(dialog.selectedArgument)
            self.qxEdit.adjustSize()

    def openArgumentSelectorQy(self):
        dialog = ArgumentSelector(self.currentDir, self)
        result = dialog.exec_()
        if result == QMessageBox.Accepted:
            self.argumentUnits[5] = dialog.argumentUnit
            self.qyEdit.setText(dialog.selectedArgument)
            self.qyEdit.adjustSize()

    def openArgumentSelectorQz(self):
        dialog = ArgumentSelector(self.currentDir, self)
        result = dialog.exec_()
        if result == QMessageBox.Accepted:
            self.argumentUnits[6] = dialog.argumentUnit
            self.qzEdit.setText(dialog.selectedArgument)
            self.qzEdit.adjustSize()

    def showRotationFrame(self, index):
        if index == 0:  # Euler Angles
            self.eulerFrame.setVisible(True)
            self.quaternionFrame.setVisible(False)
        elif index == 1:  # Quaternion
            self.eulerFrame.setVisible(False)
            self.quaternionFrame.setVisible(True)

    def toggleRotation(self, state):
        self.eulerFrame.setEnabled(state)
        self.quaternionFrame.setEnabled(state)
        self.rotationTypeComboBox.setEnabled(state)

    def selectMeshFile(self):
        fileFilter = "VTK Files (*.vtk *.stl *.vtu *.vtp);;All Files (*)"
        filePath, _ = QFileDialog.getOpenFileName(self, "Select a file", "", fileFilter)
        if filePath:
            self.meshFileEdit.setText(filePath)

    def changeTheme(self, darkTheme=False):
        themeFolder = 'dark-theme' if darkTheme else 'light-theme'
        meshPixMap = QPixmap(f'sources/icons/{themeFolder}/icons8-file-explorer-96.png').scaled(25, 25)
        selectionButtonPixmap = QPixmap(f'sources/icons/{themeFolder}/icons8-add-database-96.png').scaled(25, 25)
        self.rollButton.setIcon(QIcon(selectionButtonPixmap))
        self.pitchButton.setIcon(QIcon(selectionButtonPixmap))
        self.yawButton.setIcon(QIcon(selectionButtonPixmap))
        self.qwButton.setIcon(QIcon(selectionButtonPixmap))
        self.qxButton.setIcon(QIcon(selectionButtonPixmap))
        self.qyButton.setIcon(QIcon(selectionButtonPixmap))
        self.qzButton.setIcon(QIcon(selectionButtonPixmap))
        self.meshSelectionButton.setIcon(QIcon(meshPixMap))


class AxisButton(QPushButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.settings = loadSettings('settings')
        buttonTheme = 'dark-theme' if self.settings['DARK_THEME'] else 'light-theme'
        self.setIcon(QIcon(f'sources/icons/{buttonTheme}/icons8-axis-96.png'))
        self.setIconSize(QSize(25, 25))

    def setIconSize(self, size):
        super().setIconSize(size)
        self.setFixedSize(size)

    def sizeHint(self):
        return self.iconSize()
