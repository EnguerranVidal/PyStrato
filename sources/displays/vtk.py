######################## IMPORTS ########################
import os
import pyvista as pv
from pyvistaqt import QtInteractor

# ------------------- PyQt Modules -------------------- #
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

# --------------------- Sources ----------------------- #
from sources.common.utilities.FileHandling import loadSettings
from sources.common.widgets.Widgets import ArgumentSelector
from sources.common.widgets.basic import BasicDisplay


######################## CLASSES ########################
class VtkDisplay(BasicDisplay):
    def __init__(self, path, parent=None):
        super().__init__(path, parent)
        self.content, self.settings = None, loadSettings('settings')

        # VTK DISPLAY WIDGET
        self.meshFilePath = ''
        self.vtkMesh, self.viewedMesh = None, None
        self.vtkDisplay = QtInteractor(self)
        self.vtkDisplay.set_background('black' if self.settings['DARK_THEME'] else 'white')
        self.axes = self.vtkDisplay.add_axes(color='white'if self.settings['DARK_THEME'] else 'black')

        # MAIN LAYOUT
        layout = QVBoxLayout(self)
        layout.addWidget(self.vtkDisplay)
        self.settingsWidget = VtkDisplayEditDialog(self.currentDir, self)

    def getDescription(self):
        displayDescription = {'DISPLAY_TYPE': 'VTK_DISPLAY', 'MESH_PATH': self.meshFilePath}
        return displayDescription

    def applyDescription(self, description):
        self.meshFilePath = description['MESH_PATH']
        if not os.path.exists(self.meshFilePath):
            self.meshFilePath = ''
        else:
            self.vtkMesh = pv.read(self.meshFilePath)
            self.viewedMesh = self.vtkDisplay.add_mesh(self.vtkMesh)
        self.settingsWidget = VtkDisplayEditDialog(self.currentDir, self)

    def applyChanges(self, editWidget):
        editWidget = self.settingsWidget
        self.meshFilePath = editWidget.meshFileEdit.text()
        if os.path.exists(self.meshFilePath):
            self.vtkMesh = pv.read(self.meshFilePath)
            self.vtkDisplay.add_mesh(self.vtkMesh)

    def updateContent(self, content=None):
        self.generalSettings = loadSettings('settings')
        if content is not None:
            self.content = content

    def changeTheme(self):
        self.settings = loadSettings('settings')
        self.vtkDisplay.set_background('black' if self.settings['DARK_THEME'] else 'white')
        self.vtkDisplay.remove_actor(self.axes)
        self.axes = self.vtkDisplay.add_axes(color='white' if self.settings['DARK_THEME'] else 'black')
        self.settingsWidget.changeTheme(darkTheme=self.settings['DARK_THEME'])

    def generateSettingsWidget(self):
        self.settingsWidget = VtkDisplayEditDialog(self.currentDir, self)


class VtkDisplayEditDialog(QWidget):
    def __init__(self, path, parent: VtkDisplay):
        super().__init__(parent)
        self.settings = loadSettings('settings')
        self.currentDir = path
        self.hide()

        # EDITING WIDGETS
        themeFolder = 'dark-theme' if self.settings['DARK_THEME'] else 'light-theme'
        meshPixMap = QPixmap(f'sources/icons/{themeFolder}/icons8-file-explorer-96.png').scaled(25, 25)
        meshFileLabel = QLabel('Mesh file: ')
        self.meshFileEdit = QLineEdit(parent.meshFilePath)
        self.meshSelectionButton = QPushButton()
        self.meshSelectionButton.setIcon(QIcon(meshPixMap))
        self.meshSelectionButton.clicked.connect(self.selectMeshFile)

        mainLayout = QGridLayout(self)
        mainLayout.addWidget(meshFileLabel, 0, 0)
        mainLayout.addWidget(self.meshFileEdit, 0, 1)
        mainLayout.addWidget(self.meshSelectionButton, 0, 2)
        self.setLayout(mainLayout)

    def selectMeshFile(self):
        fileFilter = "VTK Files (*.vtk *.stl *.vtu *.vtp);;All Files (*)"
        filePath, _ = QFileDialog.getOpenFileName(self, "Select a file", "", fileFilter)
        if filePath:
            self.meshFileEdit.setText(filePath)

    def changeTheme(self, darkTheme=False):
        themeFolder = 'dark-theme' if darkTheme else 'light-theme'
        meshPixMap = QPixmap(f'sources/icons/{themeFolder}/icons8-file-explorer-96.png').scaled(25, 25)
        self.meshSelectionButton.setIcon(QIcon(meshPixMap))


class AxisButton(QPushButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Set the icon and icon size
        self.settings = loadSettings('settings')
        buttonTheme = 'dark-theme' if self.settings['DARK_THEME'] else 'light-theme'
        self.setIcon(QIcon(f'sources/icons/{buttonTheme}/icons8-axis-96.png'))
        self.setIconSize(QSize(25, 25))

    def setIconSize(self, size):
        super().setIconSize(size)
        self.setFixedSize(size)

    def sizeHint(self):
        return self.iconSize()