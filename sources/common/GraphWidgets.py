######################## IMPORTS ########################
from dataclasses import dataclass
import os
import shutil
import sys
import time as t
import subprocess
from functools import partial
import numpy as np

# ------------------- PyQt Modules -------------------- #
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, pyqtSlot, QTimer, QEvent, QModelIndex
from PyQt5.QtGui import *
import pyqtgraph as pg
from ecom.database import CommunicationDatabase
from pyqtgraph.dockarea import Dock, DockArea
import pyqtgraph.widgets.RemoteGraphicsView

# --------------------- Sources ----------------------- #
from sources.common.FileHandling import load_settings, load_format, retrieveCSVData
from sources.common.Widgets import QCustomTabWidget
from sources.common.balloondata import BalloonPackageDatabase


######################## CLASSES ########################

class GraphTabWidget(QMainWindow):
    def __init__(self, path):
        super(QMainWindow, self).__init__()
        self.current_dir = path
        self.format_path = os.path.join(self.current_dir, "formats")
        self.formats = {}
        self.settings = {}
        self.content = ContentStorage(self.current_dir)
        self.content.fill()
        # Central Widget -----------------------------------------------
        self.graphCentralWindow = QCustomTabWidget()
        self.setCentralWidget(self.graphCentralWindow)
        # Left Menu Widget ---------------------------------------------
        self.valuesLeftWidget = QDockWidget('Data Values')
        self.valuesMenu = GraphSelectionWidget(self.current_dir)
        self.valuesLeftWidget.setWidget(self.valuesMenu)
        self.valuesLeftWidget.setAllowedAreas(Qt.LeftDockWidgetArea)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.valuesLeftWidget)
        # Connects ---------------------------------------------
        self.valuesMenu.trackedComboBox.currentIndexChanged.connect(self.comboBoxChanged)

        self.fillComboBox()

    def addDockTab(self, name):
        widget = GraphDockArea(self.current_dir)
        self.graphCentralWindow.addTab(widget, name)

    def comboBoxChanged(self):
        # Removing Old Values
        self.valuesMenu.packagesTabWidget.clear()
        # Loading New Values
        name = self.valuesMenu.trackedComboBox.currentText()
        if name != '':
            formatInfo = self.formats[name]
            if isinstance(formatInfo, dict):
                packages = {'Default': list(formatInfo['DATA'].keys())}
            else:
                packages = {
                    package.id.name: [
                        dataPoint.name for dataPoint in package.data
                    ]
                    for package in formatInfo.telemetryTypes
                }
            for packageName, values in packages.items():
                valuesList = GraphListWidget(name, packageName)
                valuesList.setDragDropMode(QAbstractItemView.InternalMove)
                for value in values:
                    item = QListWidgetItem(value)
                    valuesList.addItem(item)
                self.valuesMenu.packagesTabWidget.addTab(valuesList, packageName)

    def fillComboBox(self):
        self.settings = load_settings('settings')
        files = self.settings['FORMAT_FILES']
        if len(files) == 1 and len(files[0]) == 0:
            files = []
        self.formats = {}
        for file in files:
            path = os.path.join(self.format_path, file)
            name, database = os.path.basename(path), BalloonPackageDatabase(path)
            self.formats[name] = database
        self.valuesMenu.trackedComboBox.clear()
        names = list(self.formats.keys())
        if len(names) != 0:
            for name in names:
                self.valuesMenu.trackedComboBox.addItem(name)

    def updateTabGraphs(self, content):
        self.content.append(content)
        currentIndex = self.graphCentralWindow.currentIndex()
        if currentIndex != -1:
            widget = self.graphCentralWindow.widget(currentIndex)
            widget.updateDockPlots(self.content)

    def closeRemoteGraphicsView(self, *args):
        for tab in [self.graphCentralWindow.widget(index) for index in range(self.graphCentralWindow.count())]:
            for dock in tab.dockPlots:
                dock.plottingView.close()


class GraphDockArea(QMainWindow):
    def __init__(self, path):
        super(QMainWindow, self).__init__()
        self.currentDir = path
        self.dataDir = os.path.join(self.currentDir, 'data')
        self.formatDir = os.path.join(self.currentDir, 'formats')
        self.settings = load_settings('settings')
        self.area = DockArea()
        self.setCentralWidget(self.area)
        self.dockPlots = []

    def addDockRemote(self, name, size=(500, 200), closable=True):
        dock = DockGraphRemote(self.currentDir, name, size, closable)
        self.dockPlots.append(dock)
        self.area.addDock(self.dockPlots[-1], 'right')

    def addDockDateTime(self, name, size=(500, 200), closable=True):
        dock = DockGraphDateTime(self.currentDir, name, size, closable, self.storedContent)
        self.dockPlots.append(dock)
        self.area.addDock(self.dockPlots[-1], 'right')

    def updateDockPlots(self, content):
        for dock in self.dockPlots:
            dock.updatePlots(content)


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


class DockGraphRemote(Dock):
    def __init__(self, path, name, size, closable):
        Dock.__init__(self, name, size=size, closable=closable)
        self.current_dir = path
        self.format_path = os.path.join(self.current_dir, "formats")
        self.settings = load_settings('settings')
        self.setAcceptDrops(True)
        self.plottingView = pg.widgets.RemoteGraphicsView.RemoteGraphicsView()
        self.plottingView.pg.setConfigOptions(antialias=True)
        self.addWidget(self.plottingView)
        self.plotItem = self.plottingView.pg.PlotItem()
        self.plottingView.setCentralItem(self.plotItem)
        self.plotItem.addLegend()
        self.colors = ColorCycler()
        self.trackedValues = []
        self.formats = {}

    def dragEnterEvent(self, event):
        if not event.mimeData().hasFormat('application/x-qabstractitemmodeldatalist') \
                or not isinstance(event.source(), GraphListWidget):
            event.ignore()
            return
        model = QStandardItemModel()
        model.dropMimeData(event.mimeData(), Qt.CopyAction, 0, 0, QModelIndex())
        item = model.item(0, 0)
        parent = event.source()
        databaseName = parent.selectedBalloon
        database = CommunicationDatabase(os.path.join(self.current_dir, 'formats', databaseName))
        for telemetryType in database.telemetryTypes:
            if telemetryType.id.name != parent.selectedPackage:
                continue
            for dataTypeInfo in telemetryType.data:
                if dataTypeInfo.name == item.text():
                    if not issubclass(dataTypeInfo.type.type, (int, float)):
                        event.ignore()
                        return
                    break
            else:
                event.ignore()
                return
        event.accept()

    def dropEvent(self, event):
        self.dropArea = None
        self.overlay.setDropArea(self.dropArea)
        model = QStandardItemModel()
        model.dropMimeData(event.mimeData(), Qt.CopyAction, 0, 0, QModelIndex())
        item = model.item(0, 0)
        parent = event.source()
        databaseName = parent.selectedBalloon
        self.trackedValues.append([item.text(), parent.selectedPackage, databaseName])
        self.updatePlots()

    def updatePlots(self, content=None):
        self.settings = load_settings('settings')
        self.checkTrackedValues()
        if content is None:
            # TODO: No data
            return
        for i in range(len(self.trackedValues)):
            dataName, packageName, balloonName = self.trackedValues[i]
            dataSeries = content.storage[balloonName][packageName][dataName]
            if i == 0:
                linePen = {'color': self.colors.next(0), 'width': 3}
                self.plotItem.plot(dataSeries, clear=True, pen=linePen, _callSync='off',
                                   name=self.trackedValues[i][0].replace('_', ' '))
            else:
                linePen = {'color': self.colors.next(), 'width': 3}
                self.plotItem.plot(dataSeries, clear=False, pen=linePen, _callSync='off',
                                   name=self.trackedValues[i][0].replace('_', ' '))

    def checkTrackedValues(self):
        pass
        # indices = []
        # for i in range(len(self.trackedValues)):
        #     item = self.trackedValues[i]
        #     values = list(self.databases[item[1]]['DATA'].keys())
        #     if item[0] not in values:
        #         indices.append(i)
        # for index in sorted(indices, reverse=True):
        #     del self.trackedValues[index]


class DockGraphDateTime(Dock):
    def __init__(self, path, name, size, closable, content=None):
        Dock.__init__(self, name, size=size, closable=closable)
        self.current_dir = path
        self.format_path = os.path.join(self.current_dir, "formats")
        self.settings = load_settings('settings')
        self.setAcceptDrops(True)
        self.plotWidget = pg.PlotWidget(axisItems={'bottom': pg.DateAxisItem()})
        self.addWidget(self.plotWidget)
        self.colors = ColorCycler()
        self.trackedValues = []
        self.storedContent = content
        self.formats = {}

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat('application/x-qabstractitemmodeldatalist'):
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        if isinstance(event.source(), GraphListWidget):
            model = QStandardItemModel()
            model.dropMimeData(event.mimeData(), Qt.CopyAction, 0, 0, QModelIndex())
            item = model.item(0, 0)
            parent = event.source()
            self.trackedValues.append([item.text(), parent.selectedPackage, parent.selectedBalloon])
        self.dropArea = None
        self.overlay.setDropArea(self.dropArea)
        if self.storedContent is not None:
            self.updatePlots(self.storedContent)

    def updatePlots(self, content):
        self.storedContent = content
        self.settings = load_settings('settings')
        self.retrieveFormats()
        self.checkTrackedValues()
        timeValues = [content[i][1][:, 0] for i in range(len(content))]
        names = list(self.formats.keys())
        for i in range(len(self.trackedValues)):
            dataName, formatName = self.trackedValues[i][0], self.trackedValues[i][1]
            contentLabels = content[names.index(formatName)][0]
            dataSeries = content[names.index(formatName)][1][:, contentLabels.index(dataName)]
            timeSeries = timeValues[names.index(formatName)]
            if i == 0:
                linePen = {'color': self.colors.next(0), 'width': 3}
                self.plotWidget.plot(x=timeSeries, y=dataSeries, clear=True, pen=linePen, _callSync='off',
                                     name=self.trackedValues[i][0].replace('_', ' '))
            else:
                linePen = {'color': self.colors.next(), 'width': 3}
                self.plotWidget.plot(x=timeSeries, y=dataSeries, clear=False, pen=linePen, _callSync='off',
                                     name=self.trackedValues[i][0].replace('_', ' '))

    def retrieveFormats(self):
        self.formats = {}
        paths = self.settings['FORMAT_FILES']
        for path in paths:
            name, formatLine = load_format(os.path.join(self.format_path, path))
            self.formats[name] = formatLine

    def checkTrackedValues(self):
        indices = []
        for i in range(len(self.trackedValues)):
            item = self.trackedValues[i]
            values = list(self.formats[item[1]]['DATA'].keys())
            if item[0] not in values:
                indices.append(i)
        for index in sorted(indices, reverse=True):
            del self.trackedValues[index]


class GraphListWidget(QListWidget):
    def __init__(self, balloonName, packageName):
        super(QListWidget, self).__init__()
        self.selectedBalloon = balloonName
        self.selectedPackage = packageName
        self.setDragEnabled(True)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)


class GraphSelectionWidget(QWidget):
    def __init__(self, path):
        super(QWidget, self).__init__()
        self.current_dir = path
        # Open Files ComboBox
        self.trackedComboBox = QComboBox()
        # Data Values ListBox
        self.packagesTabWidget = QTabWidget()

        layout = QFormLayout()
        layout.addRow(self.trackedComboBox)
        layout.addRow(self.packagesTabWidget)
        layout.setVerticalSpacing(0)
        self.setLayout(layout)


class ColorCycler:
    def __init__(self):
        self.cycle = [(31, 119, 180), (255, 127, 14), (44, 160, 44), (214, 39, 40), (148, 103, 189),
                      (140, 86, 75), (227, 119, 194), (127, 127, 127), (188, 189, 34), (23, 190, 207)]
        self.nbColors = len(self.cycle)
        self.step = 0

    def next(self, step=None):
        if step is not None:
            self.step = step
        value = self.cycle[self.step]
        self.step += 1
        if self.step == self.nbColors:
            self.step = 0
        return value

    def get(self, step):
        assert step < self.nbColors
        return self.cycle[step]
