######################## IMPORTS ########################
import os
from typing import Optional

# ------------------- PyQt Modules -------------------- #
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

# --------------------- Sources ----------------------- #
from sources.common.FileHandling import loadSettings, nameGiving
from sources.common.Widgets import BasicDisplay, ContentStorage
from sources.displays.graphs import MultiCurveGraph
from sources.displays.indicators import SingleIndicator, GridIndicator


######################## CLASSES ########################
class DisplayTabWidget(QMainWindow):
    def __init__(self, path):
        super(QMainWindow, self).__init__()
        self.currentDir = path
        self.dockSpaces = [Qt.LeftDockWidgetArea, Qt.RightDockWidgetArea, Qt.TopDockWidgetArea, Qt.BottomDockWidgetArea]
        self.formatPath = os.path.join(self.currentDir, 'formats')
        self.content = ContentStorage(self.currentDir)
        self.content.fill()
        self.settings = loadSettings('settings')
        self.formats = {}

        ######## CENTRAL WIDGET ########
        self.areaCycler = AreaCycler()
        self.tabWidget = QTabWidget(self)
        self.tabWidget.setMovable(True)
        self.setCentralWidget(self.tabWidget)
        self.tabWidget.tabBarDoubleClicked.connect(self.onTabBarDoubleClicked)
        self.tabWidget.currentChanged.connect(self.tabChanged)

        self.show()

    def closeCurrentTab(self):
        currentTabIndex = self.tabWidget.currentIndex()
        self.tabWidget.removeTab(currentTabIndex)

    def closeAllTabs(self):
        while self.tabWidget.count() > 0:
            self.tabWidget.removeTab(0)

    def addNewTab(self, name=None):
        if name is None:
            tabNames = [self.tabWidget.tabText(i) for i in range(self.tabWidget.count())]
            name = nameGiving(tabNames, baseName='Tab', firstName=False)
        self.tabWidget.addTab(QMainWindow(), name)

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
        if self.tabWidget.count() == 0:
            self.addNewTab()
        currentTabWidget = self.tabWidget.currentWidget()
        widgetNames = [dock.windowTitle() for dock in currentTabWidget.findChildren(QDockWidget) if dock.isVisible()]
        newIndicatorName = nameGiving(widgetNames, baseName='Indicator', firstName=False)
        newDockWidget = DisplayDockWidget(newIndicatorName, widget=SingleIndicator(path=self.currentDir))
        currentTabWidget.addDockWidget(self.areaCycler.next(), newDockWidget)

    def addGridIndicator(self):
        if self.tabWidget.count() == 0:
            self.addNewTab()
        currentTabWidget = self.tabWidget.currentWidget()
        widgetNames = [dock.windowTitle() for dock in currentTabWidget.findChildren(QDockWidget) if dock.isVisible()]
        newIndicatorName = nameGiving(widgetNames, baseName='Grid', firstName=False)
        newDockWidget = DisplayDockWidget(newIndicatorName, widget=GridIndicator(path=self.currentDir))
        currentTabWidget.addDockWidget(self.areaCycler.next(), newDockWidget)

    def addMultiCurveGraph(self):
        if self.tabWidget.count() == 0:
            self.addNewTab()
        currentTabWidget = self.tabWidget.currentWidget()
        widgetNames = [dock.windowTitle() for dock in currentTabWidget.findChildren(QDockWidget) if dock.isVisible()]
        newIndicatorName = nameGiving(widgetNames, baseName='Graph', firstName=False)
        newDockWidget = DisplayDockWidget(newIndicatorName, widget=MultiCurveGraph(path=self.currentDir))
        currentTabWidget.addDockWidget(self.areaCycler.next(), newDockWidget)

    def getLayoutDescription(self):
        dockAreas = {1: Qt.LeftDockWidgetArea, 2: Qt.RightDockWidgetArea,
                     4: Qt.TopDockWidgetArea, 8: Qt.BottomDockWidgetArea}
        tabs = [self.tabWidget.widget(index) for index in range(self.tabWidget.count())]
        tabNames = [self.tabWidget.tabText(index) for index in range(self.tabWidget.count())]
        description = {}

        for tab, tabName in zip(tabs, tabNames):
            tabDescription = {}

            for dockWidget in tab.findChildren(QDockWidget):
                if dockWidget.isVisible():
                    displayName = dockWidget.windowTitle()
                    dockPlacement = int(tab.dockWidgetArea(dockWidget))
                    dockGeometry = dockWidget.geometry().getRect()
                    displayDescription = dockWidget.widget().getDescription()

                    dockDescription = {
                        'AREA_PLACEMENT': dockPlacement,
                        'GEOMETRY': dockGeometry,
                        'DISPLAY': displayDescription,
                    }

                    tabDescription[displayName] = dockDescription

            description[tabName] = tabDescription

        return description

    def applyLayoutDescription(self, description: dict):
        dockAreas = {1: Qt.LeftDockWidgetArea, 2: Qt.RightDockWidgetArea,
                     4: Qt.TopDockWidgetArea, 8: Qt.BottomDockWidgetArea}
        self.tabWidget.clear()

        for i, (tabName, tabContents) in enumerate(description.items()):
            self.addNewTab(name=tabName)
            tabWidget = self.tabWidget.widget(i)
            geometries = []
            dock_widgets = {}
            for displayName, value in tabContents.items():
                display = DisplayDockWidget(name=displayName, widget=BasicDisplay(self.currentDir))
                geometries.append(value['GEOMETRY'])
                dockPlacement = value['AREA_PLACEMENT']
                tabWidget.addDockWidget(dockAreas.get(dockPlacement, Qt.NoDockWidgetArea), display)
                dock_widgets[displayName] = display
                print('loading after', displayName, display.geometry().getRect(), dockPlacement)

            dockWidgets = [dock for dock in self.findChildren(QDockWidget)]
            for dockWidget, geometry in zip(dockWidgets, geometries):
                dockWidget.setGeometry(QRect(*geometry))
                name = dockWidget.windowTitle()
                dockWidget.repaint()


class DisplayDockWidget(QDockWidget):
    def __init__(self, name: str, widget: Optional[BasicDisplay] = None):
        super().__init__()
        self.dockingProperties = {'MOVING': True, 'FLOATING': True,
                                  'CLOSABLE': True, 'TITLEBAR': True}
        if widget is None:
            widget = BasicDisplay()
        self.display = widget
        self.setWidget(self.display)
        self.setAllowedAreas(Qt.TopDockWidgetArea | Qt.LeftDockWidgetArea |
                             Qt.BottomDockWidgetArea | Qt.RightDockWidgetArea)
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
        self.dockingProperties = {'MOVING': moving, 'FLOATING': floating,
                                  'CLOSABLE': closable, 'TITLEBAR': showTitleBar}

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


class AreaCycler:
    def __init__(self):
        self.cycle = [Qt.LeftDockWidgetArea, Qt.RightDockWidgetArea, Qt.TopDockWidgetArea, Qt.BottomDockWidgetArea]
        self.step = 0

    def next(self, step=None):
        if step is not None:
            self.step = step
        value = self.cycle[self.step]
        self.step += 1
        if self.step == 4:
            self.step = 0
        return value

    def get(self, step):
        assert step < 4
        return self.cycle[step]
