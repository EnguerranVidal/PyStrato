######################## IMPORTS ########################
import os
from typing import Optional

# ------------------- PyQt Modules -------------------- #
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

# --------------------- Sources ----------------------- #
from sources.common.FileHandling import load_settings, newTabNameGiving
from sources.common.Widgets import BasicDisplay, ContentStorage
from sources.displays.graphs import MultiCurveGraph
from sources.displays.indicators import SingleIndicator, GridIndicator


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

        ######## CENTRAL WIDGET ########
        self.tabWidget = QTabWidget(self)
        self.tabWidget.setMovable(True)
        self.setCentralWidget(self.tabWidget)
        self.tabWidget.tabBarDoubleClicked.connect(self.onTabBarDoubleClicked)
        self.tabWidget.currentChanged.connect(self.tabChanged)

        self.show()

    def closeCurrentTab(self):
        currentTabIndex = self.tabWidget.currentIndex()
        self.tabWidget.removeTab(currentTabIndex)

    def addNewTab(self):
        tabNames = [self.tabWidget.tabText(i) for i in range(self.tabWidget.count())]
        newTabName = newTabNameGiving(tabNames, addition='Tab')
        self.tabWidget.addTab(QMainWindow(), newTabName)

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

    def tabChanged(self):
        currentIndex = self.tabWidget.currentIndex()
        if currentIndex != -1:
            tab = self.tabWidget.widget(currentIndex)
            for widget in tab.findChildren(QDockWidget):
                widget.display.updateContent(self.content)

    def updateTabDisplays(self, content):
        self.content.append(content)
        currentIndex = self.tabWidget.currentIndex()
        if currentIndex != -1:
            tab = self.tabWidget.widget(currentIndex)
            for widget in tab.findChildren(QDockWidget):
                widget.display.updateContent(self.content)

    def addSimpleIndicator(self):
        currentTabWidget = self.tabWidget.currentWidget()
        widgetNames = [dock.objectName() for dock in currentTabWidget.findChildren(QDockWidget)]
        newIndicatorName = newTabNameGiving(widgetNames, addition='Indicator')
        newDockWidget = DisplayDockWidget(newIndicatorName, widget=SingleIndicator(path=self.currentDir))
        currentTabWidget.addDockWidget(Qt.LeftDockWidgetArea, newDockWidget)

    def addGridIndicator(self):
        currentTabWidget = self.tabWidget.currentWidget()
        widgetNames = [dock.objectName() for dock in currentTabWidget.findChildren(QDockWidget)]
        newIndicatorName = newTabNameGiving(widgetNames, addition='Grid')
        newDockWidget = DisplayDockWidget(newIndicatorName, widget=GridIndicator(path=self.currentDir))
        currentTabWidget.addDockWidget(Qt.LeftDockWidgetArea, newDockWidget)

    def addMultiCurveGraph(self):
        currentTabWidget = self.tabWidget.currentWidget()
        widgetNames = [dock.objectName() for dock in currentTabWidget.findChildren(QDockWidget)]
        newIndicatorName = newTabNameGiving(widgetNames, addition='Graph')
        newDockWidget = DisplayDockWidget(newIndicatorName, widget=MultiCurveGraph(path=self.currentDir))
        currentTabWidget.addDockWidget(Qt.LeftDockWidgetArea, newDockWidget)


class DisplayDockWidget(QDockWidget):
    def __init__(self, name: str, widget: Optional[BasicDisplay] = None):
        super().__init__()
        if widget is None:
            widget = BasicDisplay()
        self.display = widget
        self.setWidget(self.display)
        self.parametersEditWindow = None
        self.setWindowTitle(name)
        self.button = HoverButton(self.display)
        self.button.setVisible(False)
        self.button.clicked.connect(self.openSettings)
        layout = QVBoxLayout(self.display)
        layout.addWidget(self.button)
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
        self.display.settingsWidget.show()
        self.parametersEditWindow.applied.connect(self.applySettingsChanges)
        self.parametersEditWindow.accepted.connect(self.applySettingsChanges)
        self.parametersEditWindow.show()

    def applySettingsChanges(self):
        # Retrieving
        name = self.parametersEditWindow.nameEdit.text()
        floating = self.parametersEditWindow.floatingCheckbox.isChecked()
        moving = self.parametersEditWindow.movingCheckBox.isChecked()
        showTitleBar = self.parametersEditWindow.showTitleCheckBox.isChecked()
        closable = self.parametersEditWindow.closableCheckbox.isChecked()

        # Upper Layout Basic Properties
        features = QDockWidget.NoDockWidgetFeatures
        if moving:
            features |= QDockWidget.DockWidgetMovable
        if closable:
            features |= QDockWidget.DockWidgetClosable
        if floating:
            features |= QDockWidget.DockWidgetFloatable

        self.setFeatures(features)
        self.setWindowTitle(name)
        if showTitleBar:
            self.setTitleBarWidget(None)
        else:
            self.setTitleBarWidget(QWidget())

        # Edit Contained Display Widget
        self.display.applyChanges(self.parametersEditWindow.editWidget)

    def closeEvent(self, event):
        super().closeEvent(event)
        del self


class ParameterDialog(QDialog):
    accepted = pyqtSignal()
    applied = pyqtSignal()
    canceled = pyqtSignal()
    typeChanged = pyqtSignal()

    def __init__(self, parent: DisplayDockWidget = None, editWidget: Optional[BasicDisplay] = None):
        super().__init__(parent)
        self.setModal(True)
        self.setWindowTitle('Display Settings')
        if editWidget is None:
            editWidget = QWidget(self)
        self.editWidget = editWidget
        propertiesLayout = QGridLayout()

        # Basic Properties --------------------------------------
        # Adding a Name Line Edit
        nameLabel = QLabel('Display Name', self)
        self.nameEdit = QLineEdit()
        self.nameEdit.setText(parent.windowTitle())
        propertiesLayout.addWidget(nameLabel, 0, 0, 1, 1)
        propertiesLayout.addWidget(self.nameEdit, 0, 1, 1, 1)

        # Adding Checkboxes to make the Dock Widget
        # Floating / Closable / Movable / With a TitleBar
        titleBarShowing = parent.titleBarWidget() is None
        floatable = parent.features() & QDockWidget.DockWidgetFloatable
        movable = parent.features() & QDockWidget.DockWidgetMovable
        closable = parent.features() & QDockWidget.DockWidgetClosable
        self.floatingCheckbox = QCheckBox('Allow Floating')
        self.floatingCheckbox.setChecked(floatable)
        self.closableCheckbox = QCheckBox('Allow Closing')
        self.closableCheckbox.setChecked(closable)
        self.movingCheckBox = QCheckBox('Allow Moving')
        self.movingCheckBox.setChecked(movable)
        self.showTitleCheckBox = QCheckBox('Show TitleBar')
        self.showTitleCheckBox.setChecked(titleBarShowing)
        propertiesLayout.addWidget(self.showTitleCheckBox, 1, 0, 1, 1)
        propertiesLayout.addWidget(self.closableCheckbox, 1, 1, 1, 1)
        propertiesLayout.addWidget(self.movingCheckBox, 2, 0, 1, 1)
        propertiesLayout.addWidget(self.floatingCheckbox, 2, 1, 1, 1)

        # Final Buttons Layout --------------------------------------
        buttonLayout = QHBoxLayout()
        # Add three buttons to the button layout
        self.acceptButton = QPushButton("Accept")
        self.applyButton = QPushButton("Apply")
        self.cancelButton = QPushButton("Cancel")
        self.acceptButton.clicked.connect(self.acceptedButtonClicked)
        self.applyButton.clicked.connect(self.appliedButtonClicked)
        self.cancelButton.clicked.connect(self.canceledButtonClicked)
        buttonLayout.addWidget(self.acceptButton)
        buttonLayout.addWidget(self.applyButton)
        buttonLayout.addWidget(self.cancelButton)

        # Add the form layout and button layout to the dialog
        self.layout = QGridLayout()
        self.layout.addWidget(self.nameEdit, 0, 1, 1, 1)
        self.layout.addWidget(nameLabel, 0, 0, 1, 1)
        self.layout.addWidget(self.editWidget, 1, 0, 1, 2)
        self.layout.addLayout(propertiesLayout, 2, 0, 1, 2)
        self.layout.addLayout(buttonLayout, 3, 0, 1, 2)
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
        self.setIcon(QIcon('sources/icons/light-theme/icons8-tools-96.png'))
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
