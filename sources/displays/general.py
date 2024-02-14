######################## IMPORTS ########################
import os
from typing import Optional

# ------------------- PyQt Modules -------------------- #
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

# --------------------- Sources ----------------------- #
from sources.common.utilities.FileHandling import loadSettings, nameGiving
from sources.common.widgets.Widgets import ContentStorage
from sources.common.widgets.basic import BasicDisplay
from sources.displays.graphs import MultiCurveGraph
from sources.displays.vtk import VtkDisplay
from sources.displays.indicators import SingleIndicator, GridIndicator


######################## CLASSES ########################
class DisplayTabWidget(QMainWindow):
    def __init__(self, path):
        super(QMainWindow, self).__init__()
        self.hide()
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

    def addVtkDisplay(self):
        if self.tabWidget.count() == 0:
            self.addNewTab()
        currentTabWidget = self.tabWidget.currentWidget()
        widgetNames = [dock.windowTitle() for dock in currentTabWidget.findChildren(QDockWidget) if dock.isVisible()]
        newDisplayName = nameGiving(widgetNames, baseName='Display', firstName=False)
        newDockWidget = DisplayDockWidget(newDisplayName, widget=VtkDisplay(path=self.currentDir))
        currentTabWidget.addDockWidget(self.areaCycler.next(), newDockWidget)

    def getLayoutDescription(self):
        tabs = [self.tabWidget.widget(index) for index in range(self.tabWidget.count())]
        tabNames = [self.tabWidget.tabText(index) for index in range(self.tabWidget.count())]
        description = {}
        for tab, tabName in zip(tabs, tabNames):
            tabDescription = {}
            for dockWidget in tab.findChildren(QDockWidget):
                if dockWidget.isVisible() and isinstance(dockWidget, DisplayDockWidget):
                    displayName = dockWidget.windowTitle()
                    dockPlacement = int(tab.dockWidgetArea(dockWidget))
                    dockGeometry = dockWidget.geometry().getRect()
                    displayDescription = dockWidget.widget().getDescription()
                    dockDescription = {
                        'AREA_PLACEMENT': dockPlacement,
                        'GEOMETRY': dockGeometry,
                        'DISPLAY': displayDescription,
                        'PROPERTIES': dockWidget.dockingProperties
                    }
                    tabDescription[displayName] = dockDescription

            description[tabName] = tabDescription

        return description

    def applyLayoutDescription(self, description: dict):
        self.tabWidget.clear()
        dockAreas = {1: Qt.LeftDockWidgetArea, 2: Qt.RightDockWidgetArea, 4: Qt.TopDockWidgetArea, 8: Qt.BottomDockWidgetArea}
        displayOptions = {'SINGLE_INDICATOR': SingleIndicator, 'GRID_INDICATOR': GridIndicator,
                          'MULTI_CURVE_GRAPH': MultiCurveGraph, 'VTK_DISPLAY': VtkDisplay,
                          'BASIC_DISPLAY': BasicDisplay}
        for i, (tabName, tabContents) in enumerate(description.items()):
            self.addNewTab(name=tabName)
            tabWidget = self.tabWidget.widget(i)
            geometries = []
            for displayName, value in tabContents.items():
                displayWidget = displayOptions[value['DISPLAY']['DISPLAY_TYPE']](self.currentDir)
                dockWidget = DisplayDockWidget(name=displayName, widget=displayWidget)
                geometries.append(value['GEOMETRY'])
                dockPlacement = value['AREA_PLACEMENT']
                tabWidget.addDockWidget(dockAreas.get(dockPlacement, Qt.NoDockWidgetArea), dockWidget)
                dockWidget.display.applyDescription(value['DISPLAY'])

            dockWidgets = [dock for dock in self.findChildren(QDockWidget)]
            for dockWidget, geometry in zip(dockWidgets, geometries):
                dockWidget.setGeometry(QRect(*geometry))
                dockWidget.repaint()


class DisplayDockWidget(QDockWidget):
    def __init__(self, name: str, widget: Optional[BasicDisplay] = None):
        super().__init__()
        self.dockingProperties = {'MOVING': True, 'FLOATING': True, 'CLOSABLE': True, 'TITLEBAR': True}
        if widget is None:
            widget = BasicDisplay()
        self.display = widget
        self.setWidget(self.display)
        self.setAllowedAreas(Qt.TopDockWidgetArea | Qt.LeftDockWidgetArea | Qt.BottomDockWidgetArea | Qt.RightDockWidgetArea)
        self.parametersEditWindow = None
        self.setWindowTitle(name)
        self.hoverButton = HoverButton(self.display)
        self.hoverButton.setVisible(False)
        self.hoverButton.clicked.connect(self.openSettings)
        layout = QVBoxLayout(self.display)
        layout.addWidget(self.hoverButton)
        self.resize(500, 500)

    def enterEvent(self, event):
        self.hoverButton.animation.setStartValue(self.hoverButton.pos())
        self.hoverButton.animation.setEndValue(QPoint(self.width() - self.hoverButton.width(), 0))
        self.hoverButton.animation.start()
        self.hoverButton.setVisible(True)
        self.hoverButton.raise_()

    def leaveEvent(self, event):
        self.hoverButton.animation.setStartValue(self.hoverButton.pos())
        self.hoverButton.animation.setEndValue(QPoint(self.width() - self.hoverButton.width(), -self.hoverButton.height()))
        self.hoverButton.animation.start()
        self.hoverButton.setVisible(False)
        self.hoverButton.lower()

    def openSettings(self):
        self.display.generateSettingsWidget()
        dialog = ParameterDialog(parent=self, editWidget=self.display.settingsWidget)
        dialog.editWidget.show()

        def applySettingsChanges(widget=None):
            # DISPLAY DOCK WIDGET PARAMETERS
            name = dialog.nameEdit.text()
            floating = dialog.floatingCheckbox.isChecked()
            moving = dialog.movingCheckBox.isChecked()
            showTitleBar = dialog.showTitleCheckBox.isChecked()
            closable = dialog.closableCheckbox.isChecked()
            self.dockingProperties = {'MOVING': moving, 'FLOATING': floating, 'CLOSABLE': closable, 'TITLEBAR': showTitleBar}
            features = QDockWidget.NoDockWidgetFeatures
            if moving:
                features |= QDockWidget.DockWidgetMovable
            if closable:
                features |= QDockWidget.DockWidgetClosable
            if floating:
                features |= QDockWidget.DockWidgetFloatable
            self.setFeatures(features)
            self.setWindowTitle(name)
            self.setTitleBarWidget(None if showTitleBar else QWidget())
            self.display.applyChanges(widget if widget is not None else dialog.editWidget)

        dialog.applied.connect(applySettingsChanges)
        result = dialog.exec_()
        if result == QDialog.Accepted:
            # TODO : Add Code to allow canceling feature for changes already applied to the display and dockwidget
            applySettingsChanges(dialog.editWidget)

    def closeEvent(self, event):
        super().closeEvent(event)
        del self


class ParameterDialog(QDialog):
    applied = pyqtSignal()

    def __init__(self, parent: DisplayDockWidget = None, editWidget: Optional[BasicDisplay] = None):
        super().__init__(parent)
        self.setModal(True)
        self.setWindowTitle('Display Settings')
        if editWidget is None:
            editWidget = QWidget(self)

        # EDIT DISPLAYS
        self.editWidget = editWidget
        nameLabel = QLabel('Display Name', self)
        self.nameEdit = QLineEdit()
        self.nameEdit.setText(parent.windowTitle())
        titleBarShowing = parent.titleBarWidget() is None
        floatable = parent.features() & QDockWidget.DockWidgetFloatable
        movable = parent.features() & QDockWidget.DockWidgetMovable
        closable = parent.features() & QDockWidget.DockWidgetClosable
        self.floatingCheckbox = QCheckBox('Allow Floating')
        self.closableCheckbox = QCheckBox('Allow Closing')
        self.movingCheckBox = QCheckBox('Allow Moving')
        self.showTitleCheckBox = QCheckBox('Show TitleBar')
        self.floatingCheckbox.setChecked(floatable)
        self.closableCheckbox.setChecked(closable)
        self.movingCheckBox.setChecked(movable)
        self.showTitleCheckBox.setChecked(titleBarShowing)

        # BOTTOM DIALOG BUTTONS
        self.acceptButton = QPushButton("Accept")
        self.applyButton = QPushButton("Apply")
        self.cancelButton = QPushButton("Cancel")
        self.acceptButton.clicked.connect(self.accept)
        self.applyButton.clicked.connect(self.applied.emit)
        self.cancelButton.clicked.connect(self.reject)

        # MAIN LAYOUT
        propertiesLayout = QGridLayout()
        propertiesLayout.addWidget(nameLabel, 0, 0, 1, 1)
        propertiesLayout.addWidget(self.nameEdit, 0, 1, 1, 1)
        propertiesLayout.addWidget(self.showTitleCheckBox, 1, 0)
        propertiesLayout.addWidget(self.closableCheckbox, 1, 1)
        propertiesLayout.addWidget(self.movingCheckBox, 2, 0)
        propertiesLayout.addWidget(self.floatingCheckbox, 2, 1)
        buttonLayout = QHBoxLayout()
        buttonLayout.addWidget(self.acceptButton)
        buttonLayout.addWidget(self.applyButton)
        buttonLayout.addWidget(self.cancelButton)
        self.layout = QVBoxLayout()
        self.layout.addLayout(propertiesLayout)
        self.layout.addWidget(self.editWidget)
        self.layout.addLayout(buttonLayout)
        self.setLayout(self.layout)


class HoverButton(QPushButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Set the icon and icon size
        self.settings = loadSettings('settings')
        buttonTheme = 'dark-theme' if self.settings['DARK_THEME'] else 'light-theme'
        self.setIcon(QIcon(f'sources/icons/{buttonTheme}/icons8-edit-96.png'))
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
