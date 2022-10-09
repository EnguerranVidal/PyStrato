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
        self.openedTabs = []
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
        self.openedTabs.append(GraphDockArea(self.current_dir))
        self.graphCentralWindow.addTab(self.openedTabs[-1], name)

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

    def updateGraphs(self, content):
        currentIndex = self.graphCentralWindow.currentIndex()
        if currentIndex != -1:
            self.openedTabs[currentIndex].updatePlots(content, self.formats)

    def closeRemoteGraphicsView(self, *args):
        for tab in self.openedTabs:
            for dock in tab.dockPlots:
                dock.plottingView.close()


class GraphDockArea(QMainWindow):
    def __init__(self, path):
        super(QMainWindow, self).__init__()
        self.current_dir = path
        self.area = DockArea()
        self.setCentralWidget(self.area)
        self.dockPlots = []

    def addDock(self, name, size=(500, 200), closable=True):
        dock = DockGraph(name, size, closable)
        self.dockPlots.append(dock)
        self.area.addDock(self.dockPlots[-1], 'right')

    def updatePlots(self, content, formats):
        for dock in self.dockPlots:
            dock.update(content)


class DockGraph(Dock):
    def __init__(self, name, size, closable):
        Dock.__init__(self, name, size=size, closable=closable)
        self.setAcceptDrops(True)
        self.trackedValues = []
        self.plottingView = pg.widgets.RemoteGraphicsView.RemoteGraphicsView()
        self.plottingView.pg.setConfigOptions(antialias=True)
        self.addWidget(self.plottingView)
        self.plotItem = self.plottingView.pg.PlotItem()
        # self.plotItem._setProxyOptions(deferGetattr=True)
        self.plottingView.setCentralItem(self.plotItem)

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
        self.update()

    def update(self):
        data = np.random.normal(size=(10000, 50)).sum(axis=1)
        data1 = data + 5 * np.sin(np.linspace(0, 10, data.shape[0]))
        self.plotItem.plot(data1, clear=True, pen=(255, 0, 0), _callSync='off')


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
