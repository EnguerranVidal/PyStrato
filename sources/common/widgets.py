######################## IMPORTS ########################
import os
import shutil
import sys
import time as t
import subprocess
from functools import partial
import sip

# ------------------- PyQt Modules -------------------- #
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, pyqtSlot, QTimer
from PyQt5.QtGui import *
import pyqtgraph as pg
from pyqtgraph.dockarea import Dock, DockArea
import pyqtgraph.widgets.RemoteGraphicsView

# --------------------- Sources ----------------------- #
from sources.common.parameters import load, save

######################## CLASSES ########################


class SerialWindow(QWidget):
    def __init__(self):
        super(SerialWindow, self).__init__()
        self.resize(450, 350)
        self.setWindowTitle('Serial Monitor')
        self.setWindowIcon(QIcon('sources/icons/PyGS.jpg'))
        # General Layout
        self.layout = QGridLayout(self)
        self.setLayout(self.layout)
        # Loading settings
        self.settings = {}
        self.settings = load("settings")
        # Text edit box
        self.textedit = QTextEdit(self)
        self.textedit.setText('Run Serial listening to display incoming info ...')
        self.textedit.setStyleSheet('font-size:15px')
        self.textedit.setLineWrapMode(QTextEdit.FixedPixelWidth)
        self.textedit.setLineWrapColumnOrWidth(1000)
        self.layout.addWidget(self.textedit, 1, 1, 1, 2)
        # Autoscroll Che-box
        self.autoscroll_box = QCheckBox("Autoscroll")
        self.autoscroll_box.setChecked(bool(self.settings["AUTOSCROLL"]))
        self.autoscroll_box.stateChanged.connect(self.changeAutoscroll)
        self.layout.addWidget(self.autoscroll_box, 2, 1)
        # Clearing Output Button
        self.clearButton = QPushButton("Clear Output")
        self.clearButton.clicked.connect(self.clearOutput)
        self.layout.addWidget(self.clearButton, 2, 2)

    def changeAutoscroll(self):
        self.parameters["AUTOSCROLL"] = int(not bool(self.settings["AUTOSCROLL"]))
        save(self.parameters, "settings")
        self.autoscroll_box.setChecked(bool(self.settings["AUTOSCROLL"]))

    @staticmethod
    def clearOutput(self):
        file = open("output", "w").close()
        self.textedit.setText("")


class MessageBox(QMessageBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        grid_layout = self.layout()
        qt_msgboxex_icon_label = self.findChild(QLabel, "qt_msgboxex_icon_label")
        qt_msgboxex_icon_label.deleteLater()
        qt_msgbox_label = self.findChild(QLabel, "qt_msgbox_label")
        qt_msgbox_label.setAlignment(Qt.AlignCenter)
        grid_layout.removeWidget(qt_msgbox_label)
        qt_msgbox_buttonbox = self.findChild(QDialogButtonBox, "qt_msgbox_buttonbox")
        grid_layout.removeWidget(qt_msgbox_buttonbox)
        grid_layout.addWidget(qt_msgbox_label, 0, 0)
        grid_layout.addWidget(qt_msgbox_buttonbox, 1, 0, alignment=Qt.AlignCenter)


class QCustomDockWidget(QDockWidget):
    def __init__(self, string, parent=None):
        super(QCustomDockWidget, self).__init__(parent)
        self.setAllowedAreas(Qt.TopDockWidgetArea | Qt.LeftDockWidgetArea |
                             Qt.BottomDockWidgetArea | Qt.RightDockWidgetArea)
        self.setWindowTitle(string)
        # self.setTitleBarWidget(QWidget())


class QCustomTabWidget(QTabWidget):
    def __init__(self, parent=None):
        super(QCustomTabWidget, self).__init__(parent)
        self.setTabsClosable(True)
        self.tabCloseRequested.connect(self.closeTab)
        # for i in range(1, 10):  # add tabs here
        # self.addTab(QWidget(), 'Tab %d' % i)

    def closeTab(self, currentIndex):
        currentQWidget = self.widget(currentIndex)
        currentQWidget.deleteLater()
        self.removeTab(currentIndex)


class FormatEditFrame(QFrame):
    def __init__(self, parent=None):
        super(QFrame, self).__init__(parent)

    @staticmethod
    def removeWidget(widget, layout):
        layout.removeWidget(widget)
        sip.delete(widget)
        widget = None
        return widget, layout

    def addValueEntry(self):
        pass


class NewFormatWindow(QWidget):
    def __init__(self):
        super(QWidget, self).__init__()
        self.setWindowTitle('Create New Format')
        self.setWindowIcon(QIcon('sources/icons/PyGS.jpg'))
        self.resize(400, 100)
        # General Layout
        self.layout = QVBoxLayout(self)
        # Loading settings
        self.settings = {}
        self.settings = load("settings")
        #######  NAME FRAME  #######
        self.nameFrame = QWidget()
        self.nameLayout = QHBoxLayout(self)
        self.nameLabel = QLabel(self)
        self.nameLabel.setText('Format Name:   ')
        self.nameEntry = QLineEdit(self)
        self.nameEntry.textChanged.connect(self.editLabels)
        self.nameEntry.resize(1000, 40)
        self.nameLayout.addWidget(self.nameLabel)
        self.nameLayout.addWidget(self.nameEntry)
        self.nameFrame.setLayout(self.nameLayout)
        #######  DATAFILE FRAME  #######
        self.dataFrame = QWidget(self)
        self.dataLayout = QHBoxLayout(self)
        self.dataLabel = QLabel(self)
        self.dataLabel.setText('Data File Name:   ')
        self.dataFileLabel = QLabel(self)
        self.dataFileLabel.setText('example.csv')
        self.dataLayout.addWidget(self.dataLabel)
        self.dataLayout.addWidget(self.dataFileLabel)
        self.dataFrame.setLayout(self.dataLayout)
        #######  FORMAT FILE FRAME  #######
        self.formatFrame = QWidget(self)
        self.formatLayout = QHBoxLayout(self)
        self.formatLabel = QLabel(self)
        self.formatLabel.setText('Format File Name: ')
        self.formatFileLabel = QLabel(self)
        self.formatFileLabel.setText('example.txt')
        self.formatLayout.addWidget(self.formatLabel)
        self.formatLayout.addWidget(self.formatFileLabel)
        self.formatFrame.setLayout(self.formatLayout)
        # Add everything to general layout
        self.layout.addWidget(self.nameFrame)
        self.layout.addWidget(self.dataFrame)
        self.layout.addWidget(self.formatFrame)
        self.setLayout(self.layout)

    def editLabels(self):
        name = self.nameEntry.text()
        if len(name) == 0:
            name = 'example'
        self.dataFileLabel.setText('data_' + name + '.csv')
        self.formatFileLabel.setText('format_' + name + '.txt')


class ValuesTreeWidget(QTreeWidget):
    def __init__(self, parent=None):
        super(QTreeWidget, self).__init__(parent)
        headerItem = QTreeWidgetItem()
        item = QTreeWidgetItem()
        for i in range(3):
            parent = QTreeWidgetItem(self)
            parent.setText(0, "Parent {}".format(i))
            parent.setFlags(parent.flags() | Qt.ItemIsTristate | Qt.ItemIsUserCheckable)
            for x in range(5):
                child = QTreeWidgetItem(parent)
                child.setFlags(child.flags() | Qt.ItemIsUserCheckable)
                child.setText(0, "Child {}".format(x))
                child.setCheckState(0, Qt.Unchecked)




