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

    def addDockTab(self, name):
        self.openedTabs.append(GraphDockArea(self.current_dir))
        self.graphCentralWindow.addTab(self.openedTabs[-1], name)


class GraphDockArea(QMainWindow):
    def __init__(self, path):
        super(QMainWindow, self).__init__()
        self.current_dir = path
        self.area = DockArea()
        self.setCentralWidget(self.area)
        self.dockPlots = []

        self.addDock('farm')
        self.addDock('cow')

    def addDock(self, name, size=(500, 200), closable=True):
        dock = CustomDock(name, size, closable)
        self.dockPlots.append(dock)
        self.area.addDock(self.dockPlots[-1], 'right')


class CustomDock(Dock):
    def __init__(self, name, size, closable):
        Dock.__init__(self, name, size=size, closable=closable)
        self.setAcceptDrops(True)
        self.trackedValues = []

    def dragEnterEvent(self, event):
        print(event.mimeData().text())
        if event.mimeData().hasFormat('application/x-qabstractitemmodeldatalist'):
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        if isinstance(event.source(), GraphListWidget):
            model = QStandardItemModel()
            model.dropMimeData(event.mimeData(), Qt.CopyAction, 0, 0, QModelIndex())
            item = model.item(0, 0)
            self.setText(item.text())
            print(type(event.source()))
            parent = event.source()


class GraphListWidget(QListWidget):
    def __init__(self, path):
        super(QListWidget, self).__init__()
        self.selectedFormat = None


class GraphSelectionWidget(QWidget):
    def __init__(self, path):
        super(QWidget, self).__init__()
        self.current_dir = path
        # Open Files ComboBox
        self.trackedComboBox = QComboBox()
        # Data Values ListBox
        self.valuesListWidget = GraphListWidget(self.current_dir)
        self.valuesListWidget.setDragDropMode(QAbstractItemView.InternalMove)

        layout = QFormLayout()
        layout.addRow(self.trackedComboBox)
        layout.addRow(self.valuesListWidget)
        layout.setVerticalSpacing(0)
        self.setLayout(layout)

    def loadSelectedFormat(self, name):
        pass

    def comboBoxChanged(self):
        # Removing Old Values
        self.valuesListWidget.clear()
        # Loading New Values
        name = self.packetMenu.openComboBox.currentText()
        self.loadSelected(name)
        values = list(self.formats[name]['DATA'].keys())

