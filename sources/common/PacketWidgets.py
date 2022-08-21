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
from sources.common.parameters import load_settings, save_settings, load_format, save_format


######################## CLASSES ########################

class PacketTabWidget(QMainWindow):
    def __init__(self, path):
        super(QMainWindow, self).__init__()
        self.current_dir = path
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
        self.packetMenu.valuesListWidget.model().rowsMoved.connect(self.itemListDragDrop)

        self.formats = {}

    def comboBoxChanged(self):
        # Removing Old Values
        self.packetMenu.valuesListWidget.clear()
        # Loading New Values
        name = self.packetMenu.openComboBox.currentText()
        values = list(self.formats[name]['DATA'].keys())
        for value in values:
            item = QListWidgetItem(value)
            self.packetMenu.valuesListWidget.addItem(item)
        self.packetMenu.nbLabel.setText("Number of Data Values : " + str(self.packetMenu.valuesListWidget.count()))

    def itemListDragDrop(self):
        pass

    def itemListSelected(self):
        item = self.packetMenu.valuesListWidget.currentItem()
        print("You have selected : " + str(item.text()))

    def newFormat(self, name, configPath, savePath):
        configPath = os.path.join()
        # Opening Packet Format File
        with open(configPath, 'w') as file:
            file.write('NAME:' + name + '\n')
            file.write('FILE:' + savePath)
        # Adding New Format Into ComboBox
        self.formats[name] = {'ID': None, 'PIN': None, 'PATH': configPath,
                              'FILE': savePath, 'CLOCK': None, 'VALUES': {}}
        self.packetMenu.openComboBox.addItem(name)

    def openFormat(self, path):
        # Loading Packet Format File
        name, formatLine = load_format(path)
        # Getting Format Into ComboBox
        self.formats[name] = formatLine
        self.packetMenu.openComboBox.addItem(name)

    def saveFormat(self, path=None):
        name = self.packetMenu.openComboBox.currentText()
        formatLine = self.formats[name]
        if path is None:
            path = formatLine['PATH']
        else:
            self.formats[name]['PATH'] = path
        save_format(formatLine, path)

    def saveAllFormats(self):
        n = self.packetMenu.openComboBox.count()
        for name in [self.packetMenu.openComboBox.itemText(i) for i in range(n)]:
            save_format(self.formats[name], self.formats[name]['PATH'])

    def closeFormat(self):
        name = self.packetMenu.openComboBox.currentText()
        path = self.formats[name]['PATH']
        name, formatLine = load_format(path)
        if formatLine != self.formats[name]:
            messageBox = QMessageBox()
            title = "Close Format"
            message = "WARNING !\n\nIf you close without saving, any changes made to the format" \
                      "will be lost.\n\nSave format before closing?"
            reply = messageBox.question(self, title, message, messageBox.Yes | messageBox.No |
                                        messageBox.Cancel, messageBox.Cancel)
            if reply == messageBox.Yes or reply == messageBox.No:
                if reply == messageBox.Yes:
                    save_format(self.formats[name], path)
                index = self.packetMenu.openComboBox.currentIndex()
                self.packetMenu.openComboBox.removeItem(index)
                self.packetMenu.openComboBox.setCurrentIndex(0)
                self.comboBoxChanged()

    def closeAllFormat(self):
        n = self.packetMenu.openComboBox.count()
        names = [self.packetMenu.openComboBox.itemText(i) for i in range(n)]
        changes = []
        for i in range(n):
            name, formatLine = load_format(self.formats[names[i]]['PATH'])
            changes.append(formatLine != self.formats[name])
        if True in changes:
            messageBox = QMessageBox()
            title = "Close Format"
            message = "WARNING !\n\nIf you quit without saving, any changes made to the formats" \
                      "will be lost.\n\nSave format before quitting?"
            reply = messageBox.question(self, title, message, messageBox.Yes | messageBox.No |
                                        messageBox.Cancel, messageBox.Cancel)
            if reply == messageBox.Yes or reply == messageBox.No:
                if reply == messageBox.Yes:
                    for i in range(n):
                        save_format(self.formats[names[i]], self.formats[names[i]]['PATH'])
                self.packetMenu.openComboBox.clear()


class PacketMenu(QWidget):
    def __init__(self):
        super(QWidget, self).__init__()
        # Open Files ComboBox
        self.openComboBox = QComboBox()
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
        self.listedValues = []
        self.valuesListWidget.setDragDropMode(QAbstractItemView.InternalMove)
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
