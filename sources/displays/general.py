######################## IMPORTS ########################
import os
from typing import Optional

# ------------------- PyQt Modules -------------------- #
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

# --------------------- Sources ----------------------- #
from sources.common.FileHandling import load_settings
from sources.common.Widgets import BasicDisplay
from sources.common.balloondata import BalloonPackageDatabase
from sources.displays.graphs import CustomGraph


######################## CLASSES ########################
class DisplayTabWidget(QMainWindow):
    def __init__(self, path):
        super(QMainWindow, self).__init__()
        self.currentDir = path
        self.formatPath = os.path.join(self.currentDir, 'formats')
        self.content = ContentStorage(self.currentDir)
        self.content.fill()
        self.settings = load_settings('settings')
        self.formats = {}

        # Central Widget -----------------------------------------------
        self.tabWidget = QTabWidget(self)
        self.setCentralWidget(self.tabWidget)
        self.tabWidget.tabBarDoubleClicked.connect(self.onTabBarDoubleClicked)

        # Add some tabs to the QTabWidget
        self.tabWidget.addTab(QMainWindow(), "Tab 1")
        self.tabWidget.addTab(QMainWindow(), "Tab 2")

        tabWidget1 = self.tabWidget.widget(0)
        dock_widget_1 = DisplayDockWidget("Dock Widget 1", widget=CustomGraph())
        dock_widget_2 = DisplayDockWidget("Dock Widget 2", widget=CustomGraph())
        dock_widget_3 = DisplayDockWidget('Dock Widget 3', widget=CustomGraph())
        dock_widget_4 = DisplayDockWidget("Dock Widget 4", widget=CustomGraph())
        dock_widget_5 = DisplayDockWidget('bruh', widget=CustomGraph())

        tabWidget1.addDockWidget(Qt.TopDockWidgetArea, dock_widget_1)
        tabWidget1.addDockWidget(Qt.RightDockWidgetArea, dock_widget_2)
        tabWidget1.addDockWidget(Qt.BottomDockWidgetArea, dock_widget_3)
        tabWidget1.addDockWidget(Qt.LeftDockWidgetArea, dock_widget_4)
        tabWidget1.splitDockWidget(dock_widget_3, dock_widget_5, Qt.Horizontal)

        self.show()

    def tabNamesList(self):
        return [self.tabWidget.tabText(i) for i in range(self.tabWidget.count())]

    def closeCurrentTab(self):
        currentTabIndex = self.tabWidget.currentIndex()
        self.tabWidget.removeTab(currentTabIndex)

    def onTabBarDoubleClicked(self, index):
        tabName = self.tabWidget.tabText(index)
        lineEdit = QLineEdit(tabName)
        self.tabWidget.setTabText(index, '')
        tabBar = self.tabWidget.tabBar()
        tabBar.setTabButton(index, tabBar.ButtonPosition.LeftSide, lineEdit)
        lineEdit.setFocus()
        lineEdit.selectAll()
        lineEdit.returnPressed.connect(lambda: self.renameTab(lineEdit, index))

    def renameTab(self, lineEdit, index):
        tabBar = self.tabWidget.tabBar()
        self.tabWidget.setTabText(index, lineEdit.text())
        tabBar.setTabButton(index, tabBar.ButtonPosition.LeftSide, None)


class DisplayDockWidget(QDockWidget):
    def __init__(self, name: str, widget: Optional[BasicDisplay] = None):
        super().__init__()
        if widget is None:
            widget = BasicDisplay()
        self.display = widget
        self.setWidget(self.display)
        self.parametersEditWindow = ParameterDialog(self)
        self.parametersEditWindow.applied.connect(self.applySettingsChanges)
        self.parametersEditWindow.accepted.connect(self.applySettingsChanges)

        self.setWindowTitle(name)
        self.button = HoverButton(self.display)
        self.button.setVisible(False)
        self.button.clicked.connect(self.openSettings)

        # Create the central widget and add the button to it
        layout = QVBoxLayout(self.display)
        layout.addWidget(self.button)

        # Set the size of the widget to be 500x500 pixels
        self.resize(500, 500)

    def enterEvent(self, event):
        # Animate the button from the top of the widget to the top right corner
        self.button.animation.setStartValue(self.button.pos())
        self.button.animation.setEndValue(QPoint(self.width() - self.button.width(), 0))
        self.button.animation.start()
        self.button.setVisible(True)

    def leaveEvent(self, event):
        # Animate the button back to the top of the widget
        self.button.animation.setStartValue(self.button.pos())
        self.button.animation.setEndValue(QPoint(self.width() - self.button.width(), -self.button.height()))
        self.button.animation.start()
        self.button.setVisible(False)

    def openSettings(self):
        self.parametersEditWindow = ParameterDialog(parent=self, editWidget=self.display.settingsWidget)
        self.parametersEditWindow.applied.connect(self.applySettingsChanges)
        self.parametersEditWindow.accepted.connect(self.applySettingsChanges)
        self.parametersEditWindow.show()

    def applySettingsChanges(self):
        name = self.parametersEditWindow.nameEdit.text()
        self.display.applyChanges(self.parametersEditWindow.editWidget)
        self.setWindowTitle(name)

    def closeEvent(self, event):
        super().closeEvent(event)
        del self


class ParameterDialog(QDialog):
    accepted = pyqtSignal()
    applied = pyqtSignal()
    canceled = pyqtSignal()
    typeChanged = pyqtSignal()

    def __init__(self, parent=None, editWidget: Optional[QWidget] = None):
        super().__init__(parent)
        self.setModal(True)
        self.setWindowTitle('Display Settings')
        if editWidget is None:
            editWidget = QWidget(self)
        self.editWidget = editWidget
        form_layout = QFormLayout()

        # Add a line edit to the form layout
        self.nameEdit = QLineEdit()
        self.nameEdit.setText(parent.windowTitle())
        form_layout.addRow("Display Name :", self.nameEdit)

        # Create the button layout
        button_layout = QHBoxLayout()

        # Add three buttons to the button layout
        self.acceptButton = QPushButton("Accept")
        self.applyButton = QPushButton("Apply")
        self.cancelButton = QPushButton("Cancel")
        self.acceptButton.clicked.connect(self.acceptedButtonClicked)
        self.applyButton.clicked.connect(self.appliedButtonClicked)
        self.cancelButton.clicked.connect(self.canceledButtonClicked)
        button_layout.addWidget(self.acceptButton)
        button_layout.addWidget(self.applyButton)
        button_layout.addWidget(self.cancelButton)

        # Add the form layout and button layout to the dialog
        self.layout = QVBoxLayout()
        self.layout.addLayout(form_layout)
        self.layout.addWidget(self.editWidget)
        self.layout.addLayout(button_layout)
        self.setLayout(self.layout)

    def acceptedButtonClicked(self):
        self.accepted.emit()
        self.close()

    def appliedButtonClicked(self):
        self.applied.emit()

    def canceledButtonClicked(self):
        self.canceled.emit()
        self.close()


class HoverButton(QPushButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Set the icon and icon size
        self.setIcon(QIcon('sources/icons/icons8-settings-96.png'))
        self.setIconSize(QSize(25, 25))

        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setStyleSheet('border: none;')
        self.setAutoFillBackground(False)
        self.setFlat(True)

        # Create an animation to move the button
        self.animation = QPropertyAnimation(self, b'pos')
        self.animation.setDuration(250)
        self.animation.setEasingCurve(QEasingCurve.OutQuad)

        # Set the initial position of the button to be off the screen
        self.move(self.parent().width() - self.width(), -self.height())

    def setIconSize(self, size):
        super().setIconSize(size)
        self.setFixedSize(size)

    def sizeHint(self):
        return self.iconSize()


class ContentStorage:
    def __init__(self, path):
        self.settings = load_settings('settings')
        self.currentDir = path
        self.storage = {}

    def fill(self):
        self.settings = load_settings('settings')
        paths = self.settings['FORMAT_FILES']
        for path in paths:
            path = os.path.join(self.currentDir, 'formats', path)
            if os.path.isdir(path):
                name, database = os.path.basename(path), BalloonPackageDatabase(path)
                self.storage[name] = {
                    telemetryType.id.name: {
                        dataPoint.name: []
                        for dataPoint in telemetryType.data
                    }
                    for telemetryType in database.telemetryTypes
                }

    def append(self, content):
        packageStorage = self.storage[content['parser']][content['type']]
        for key, value in content['data'].items():
            packageStorage[key].append(value)
