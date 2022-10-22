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
from PyQt5.QtCore import Qt, pyqtSlot, QTimer, QEvent
from PyQt5.QtGui import *
import pyqtgraph as pg
from pyqtgraph.dockarea import Dock, DockArea
import pyqtgraph.widgets.RemoteGraphicsView

from qtwidgets import Toggle, AnimatedToggle

# --------------------- Sources ----------------------- #
from sources.common.parameters import load_settings, save_settings, load_format, save_format


######################## CLASSES ########################

class PacketTabWidget(QMainWindow):
    def __init__(self, path):
        super(QMainWindow, self).__init__()
        self.current_dir = path
        self.format_path = os.path.join(self.current_dir, "formats")
        self.formats = {}
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
        # self.packetMenu.valuesListWidget.model().rowsMoved.connect(self.itemListDragDrop)
        self.packetCentralWidget.bottomWidget.totalSlider.valueChanged.connect(self.totalChanged)
        self.packetCentralWidget.bottomWidget.floatSlider.valueChanged.connect(self.floatChanged)

    def totalChanged(self, value):
        name = self.packetMenu.openComboBox.currentText()
        item = self.packetMenu.valuesListWidget.currentItem()
        if item is not None:
            data = item.text()
            floatValue = self.packetCentralWidget.bottomWidget.floatSlider.value()
            self.formats[name]['DATA'][data]['TOTAL'] = str(value)
            self.packetCentralWidget.bottomWidget.floatSlider.setRange(0, value)
            self.packetCentralWidget.bottomWidget.floatSlider.setValue(floatValue)
            self.packetCentralWidget.bottomWidget.floatSlider.setTickInterval(1)

    def floatChanged(self, value):
        name = self.packetMenu.openComboBox.currentText()
        item = self.packetMenu.valuesListWidget.currentItem()
        if item is not None:
            data = item.text()
            self.formats[name]['DATA'][data]['FLOAT'] = str(value)

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

    def itemListSelected(self):
        name = self.packetMenu.openComboBox.currentText()
        item = self.packetMenu.valuesListWidget.currentItem()
        if item is not None:
            nameValue = item.text()
            floatValue = int(self.formats[name]['DATA'][nameValue]['FLOAT'])
            totalValue = int(self.formats[name]['DATA'][nameValue]['TOTAL'])
            unitValue = self.formats[name]['DATA'][nameValue]['UNIT']
            signValue = bool(int(self.formats[name]['DATA'][nameValue]['SIGN']))
            self.packetCentralWidget.bottomWidget.floatSlider.setValue(floatValue)
            self.packetCentralWidget.bottomWidget.totalSlider.setValue(totalValue)
            self.packetCentralWidget.bottomWidget.unitEdit.setText(unitValue)
            self.packetCentralWidget.bottomWidget.signToggle.setChecked(signValue)
            self.packetCentralWidget.bottomWidget.nameEdit.setText(nameValue)

    def newFormat(self, name, configPath, savePath):
        configPath = os.path.join(self.format_path, configPath)
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
        if len(name) != 0:
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
        print(name)
        if name != '':
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
            message = "WARNING !\n\nIf you quit without saving, any changes made to the balloonFormats" \
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
        # Data Values ListBox
        self.valuesListWidget = QListWidget()
        self.listedValues = []
        self.valuesListWidget.setDragDropMode(QAbstractItemView.InternalMove)
        # Number Label
        self.nbLabel = QLabel("Number of Data Values : 0")

        layout = QFormLayout()
        layout.addRow(self.openComboBox)
        layout.addRow(self.valuesListWidget)
        layout.addRow(self.nbLabel)
        layout.setVerticalSpacing(0)
        self.setLayout(layout)


class PacketCentralWidget(QWidget):
    def __init__(self):
        super(QWidget, self).__init__()
        self.topWidget = TopCentralPacketWidget()
        self.bottomWidget = ValuePacketWidget()
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.topWidget)
        self.layout.addWidget(self.bottomWidget)
        self.setLayout(self.layout)


class TopCentralPacketWidget(QWidget):
    def __init__(self):
        super(QWidget, self).__init__()
        # Balloon Identifier ---------------------------------------------
        self.balloonIdToggle = Toggle()
        self.balloonIdEdit = QLineEdit()
        self.balloonIdLabel = QLabel()
        # Balloon Internal Clock -----------------------------------------

        # Balloon Packet Identifier --------------------------------------
        self.packetIdToggle = Toggle()
        self.packetIdSlider = QSlider()
        self.packetIdLabel = QLabel()


class ValuePacketWidget(QWidget):
    def __init__(self):
        super(QWidget, self).__init__()
        # Sign ---------------------------------------------
        self.signToggle = Toggle()
        # Total Digits -------------------------------------
        self.totalSlider = QSlider(Qt.Vertical)
        self.totalSlider.setSingleStep(1)
        self.totalSlider.setTickInterval(1)
        self.totalSlider.setRange(0, 10)
        self.totalSlider.setTickPosition(QSlider.TicksLeft)
        self.totalLabel = QLabel('Total')
        # Float Digits -------------------------------------
        self.floatSlider = QSlider(Qt.Vertical)
        self.floatSlider.setSingleStep(1)
        self.floatSlider.setTickInterval(1)
        self.floatSlider.setRange(0, 10)
        self.floatSlider.setTickPosition(QSlider.TicksLeft)
        self.floatLabel = QLabel('Float')
        # Value Unit
        self.unitEdit = QLineEdit()
        self.nameEdit = QLineEdit()

        self.formLayout = QFormLayout()
        self.formLayout.addRow('Name:', self.nameEdit)
        self.formLayout.addRow('Unit:', self.unitEdit)
        self.formLayout.addRow('Sign', self.signToggle)
        self.leftContainer = QWidget()
        self.leftContainer.setLayout(self.formLayout)

        self.rightLayout = QGridLayout()
        self.rightLayout.addWidget(self.totalLabel, 0, 0)
        self.rightLayout.addWidget(self.totalSlider, 1, 0)
        self.rightLayout.addWidget(self.floatLabel, 0, 1)
        self.rightLayout.addWidget(self.floatSlider, 1, 1)
        self.rightContainer = QWidget()
        self.rightContainer.setLayout(self.rightLayout)

        self.layout = QHBoxLayout()
        self.layout.addWidget(self.leftContainer)
        self.layout.addWidget(self.rightContainer)

        self.setLayout(self.layout)