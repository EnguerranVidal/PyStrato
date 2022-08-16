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
from PyQt5.QtCore import Qt, pyqtSlot, QTimer
from PyQt5.QtGui import *
import pyqtgraph as pg
from pyqtgraph.dockarea import Dock, DockArea
import pyqtgraph.widgets.RemoteGraphicsView

# --------------------- Sources ----------------------- #
from sources.common.parameters import load_settings, save_settings


######################## CLASSES ########################

class PacketTabWidget(QMainWindow):
    def __init__(self):
        super(QMainWindow, self).__init__()
        # Central Widget -----------------------------------------------
        self.packetCentralWidget = PacketCentralWidget()
        self.setCentralWidget(self.packetCentralWidget)

        # Left Menu Widget ---------------------------------------------
        self.packetLeftWidget = QDockWidget('Selection')
        self.packetMenu = PacketMenu()
        self.packetLeftWidget.setWidget(self.packetMenu)
        self.packetLeftWidget.setAllowedAreas(Qt.LeftDockWidgetArea)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.packetLeftWidget)

        # Setting Connects ---------------------------------------------
        self.packetMenu.openComboBox.currentIndexChanged.connect(self.comboBoxChanged)
        self.packetMenu.valuesListWidget.clicked.connect(self.itemListSelected)

        self.comboBoxChanged()

    def comboBoxChanged(self, *args):
        # Removing Old Values
        # self.packetMenu.valuesListWidget.clear()
        self.packetMenu.nbLabel.setText("Number of Data Values : " + str(self.packetMenu.valuesListWidget.count()))
        print("You have selected : " + self.packetMenu.openComboBox.currentText())

    def itemListSelected(self, *args):
        item = self.packetMenu.valuesListWidget.currentItem()
        print("You have selected : " + str(item.text()))


class PacketMenu(QWidget):
    def __init__(self):
        super(QWidget, self).__init__()
        # self.resize(270, 110)

        # Open Files ComboBox
        self.openComboBox = QComboBox()
        self.openComboBox.addItem('Bruh')
        self.openComboBox.addItem('Bruh2')

        # Search Bar
        self.searchWidget = QWidget()
        self.searchButton = QPushButton('search')
        self.searchLineEdit = QLineEdit()
        self.searchLineEdit.setPlaceholderText("Search in browser")
        searchLayout = QHBoxLayout()
        searchLayout.addWidget(self.searchLineEdit)
        searchLayout.addWidget(self.searchButton)
        self.searchWidget.setLayout(searchLayout)

        # Data Values ListBox
        self.valuesListWidget = QListWidget()
        item = QListWidgetItem('BRUH')
        self.valuesListWidget.addItem(item)
        item = QListWidgetItem('BRUH2')
        self.valuesListWidget.addItem(item)

        # Number Label
        self.nbLabel = QLabel("Number of Data Values : 0")

        layout = QFormLayout()
        layout.addRow(self.openComboBox)
        layout.addRow(self.searchWidget)
        layout.addRow(self.valuesListWidget)
        layout.addRow(self.nbLabel)
        layout.setVerticalSpacing(0)
        self.setLayout(layout)


class PacketCentralWidget(QWidget):
    def __init__(self):
        super(QWidget, self).__init__()
        self.textEdit = QTextEdit()