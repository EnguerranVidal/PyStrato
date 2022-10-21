######################## IMPORTS ########################
import os
import shutil
import sys
import time as t
import subprocess
from functools import partial
import sip
import numpy as np

# ------------------- PyQt Modules -------------------- #
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, pyqtSlot, QTimer, QEvent, QModelIndex
from PyQt5.QtGui import *
import pyqtgraph as pg
from pyqtgraph.dockarea import Dock, DockArea
import pyqtgraph.widgets.RemoteGraphicsView

from qtwidgets import Toggle, AnimatedToggle

# --------------------- Sources ----------------------- #
from sources.common.parameters import load_settings, save_settings, load_format, save_format
from sources.common.Widgets import QCustomTabWidget


######################## CLASSES ########################

class GraphTabWidget(QMainWindow):
    def __init__(self, path):
        super(QMainWindow, self).__init__()
        self.current_dir = path
        self.format_path = os.path.join(self.current_dir, "formats")
        self.formats = {}
        self.settings = {}
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
        self.valuesMenu.valuesListWidget.clear()
        # Loading New Values
        name = self.valuesMenu.trackedComboBox.currentText()
        if name != '':
            self.valuesMenu.valuesListWidget.selectedFormat = name
            values = list(self.formats[name]['DATA'].keys())
            for value in values:
                item = QListWidgetItem(value)
                self.valuesMenu.valuesListWidget.addItem(item)

    def fillComboBox(self):
        self.settings = load_settings('settings')
        files = self.settings['FORMAT_FILES']
        if len(files) == 1 and len(files[0]) == 0:
            files = []
        self.formats = {}
        for file in files:
            path = os.path.join(self.format_path, file)
            name, formatLine = load_format(path)
            # Getting Format Into ComboBox
            self.formats[name] = formatLine
        self.valuesMenu.trackedComboBox.clear()
        names = list(self.formats.keys())
        if len(names) != 0:
            for name in names:
                self.valuesMenu.trackedComboBox.addItem(name)

    def updateTabGraphs(self, content):
        currentIndex = self.graphCentralWindow.currentIndex()
        if currentIndex != -1:
            widget = self.graphCentralWindow.widget(currentIndex)
            widget.updateDockPlots(content)

    def closeRemoteGraphicsView(self, *args):
        for tab in [self.graphCentralWindow.widget(index) for index in range(self.graphCentralWindow.count())]:
            for dock in tab.dockPlots:
                dock.plottingView.close()


class GraphDockArea(QMainWindow):
    def __init__(self, path):
        super(QMainWindow, self).__init__()
        self.current_dir = path
        self.format_path = os.path.join(self.current_dir, "formats")
        self.area = DockArea()
        self.setCentralWidget(self.area)
        self.dockPlots = []

    def addDock(self, name, size=(500, 200), closable=True):
        dock = DockGraph(self.current_dir, name, size, closable)
        self.dockPlots.append(dock)
        self.area.addDock(self.dockPlots[-1], 'right')

    def updateDockPlots(self, content):
        for dock in self.dockPlots:
            dock.updatePlots(content)


class DockGraph(Dock):
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
        # self.plotItem._setProxyOptions(deferGetattr=True)
        self.plottingView.setCentralItem(self.plotItem)
        self.plotItem.addLegend()
        self.colors = ColorCycler()
        self.trackedValues = []
        self.storedContent = None
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
            self.trackedValues.append([item.text(), parent.selectedFormat])
        self.dropArea = None
        self.overlay.setDropArea(self.dropArea)
        if self.storedContent is not None:
            self.updatePlots(self.storedContent)

    def updatePlots(self, content):
        self.storedContent = content
        self.settings = load_settings('settings')
        self.retrieveFormats()
        self.checkTrackedValues()
        # timeSeries = [content[i][1][:, 0] for i in range(len(content))]
        names = list(self.formats.keys())
        for i in range(len(self.trackedValues)):
            dataName, formatName = self.trackedValues[i][0], self.trackedValues[i][1]
            contentLabels = content[names.index(formatName)][0]
            dataSeries = content[names.index(formatName)][1][:, contentLabels.index(dataName)]
            if i == 0:
                linePen = {'color': self.colors.next(0), 'width': 3}
                self.plotItem.plot(dataSeries, clear=True, pen=linePen, _callSync='off',
                                   name=self.trackedValues[i][0].replace('_', ' '))
            else:
                linePen = {'color': self.colors.next(), 'width': 3}
                self.plotItem.plot(dataSeries, clear=False, pen=linePen, _callSync='off',
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
    def __init__(self):
        super(QListWidget, self).__init__()
        self.selectedFormat = None
        self.setDragEnabled(True)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)


class GraphSelectionWidget(QWidget):
    def __init__(self, path):
        super(QWidget, self).__init__()
        self.current_dir = path
        # Open Files ComboBox
        self.trackedComboBox = QComboBox()
        # Data Values ListBox
        self.valuesListWidget = GraphListWidget()
        self.valuesListWidget.setDragDropMode(QAbstractItemView.InternalMove)

        layout = QFormLayout()
        layout.addRow(self.trackedComboBox)
        layout.addRow(self.valuesListWidget)
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
