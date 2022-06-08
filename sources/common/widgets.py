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
        self.settings = load_settings("settings")
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
        save_settings(self.parameters, "settings")
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


class FormatEditWidget(QWidget):
    def __init__(self, parent=None, path=None, formatFile=None):
        super(QWidget, self).__init__(parent)
        self.formatFile = os.path.join('formats', formatFile)
        self.current_dir = path
        self.settings = {}
        self.settings = load_settings("settings")
        if os.path.exists(self.formatFile):
            self.saved = True
        else:
            self.saved = False
        ####### WIDGETS #######

        # Balloon Identifier
        self.balloonIdWidget = QWidget(self)
        self.balloonIdWidget.move(10, 10)
        self.balloonIdLayout = QHBoxLayout(self.balloonIdWidget)
        self.balloonIdBox = QCheckBox("Balloon Identifier?", self.balloonIdWidget)
        self.balloonIdBox.stateChanged.connect(self.balloonIdBoxChanged)
        self.balloonIdEdit = QLineEdit(self.balloonIdWidget)
        self.balloonIdLayout.addWidget(self.balloonIdBox)
        self.balloonIdLayout.addWidget(self.balloonIdEdit)
        self.balloonIdWidget.setLayout(self.balloonIdLayout)

        # Packet Identifier
        self.packetIdWidget = QWidget(self)
        self.packetIdWidget.move(10, 40)
        self.packetIdLayout = QHBoxLayout(self.packetIdWidget)
        self.packetIdBox = QCheckBox("Packet Identifier?", self)
        self.packetIdBox.stateChanged.connect(self.packetIdBoxChanged)
        self.packetIdSpinBox = QSpinBox(self)
        self.packetIdSpinBox.setValue(1)
        self.packetIdSpinBox.setMinimum(1)
        self.packetIdSpinBox.valueChanged.connect(self.spinBoxChanged)
        self.packetIdSpinBox.setFocusPolicy(Qt.NoFocus)
        self.packetIdLabel = QLabel(self)
        self.packetIdLabel.setText('ex : NA')
        self.packetIdLayout.addWidget(self.packetIdBox)
        self.packetIdLayout.addWidget(self.packetIdSpinBox)
        self.packetIdLayout.addWidget(self.packetIdLabel)
        self.packetIdWidget.setLayout(self.packetIdLayout)

        # Header
        self.headerWidget = QWidget(self)
        self.headerWidget.move(10, 70)
        self.headerLayout = QHBoxLayout(self.headerWidget)
        self.headerBox = QCheckBox("Header?", self)
        self.headerLabel = QLabel(self)
        self.headerLabel.setText(self.settings['HEADER'])
        self.headerLayout.addWidget(self.headerBox)
        self.headerLayout.addWidget(self.headerLabel)
        self.headerWidget.setLayout(self.headerLayout)

    def saveFormat(self, save_path=None):
        pass

    def loadFormat(self):
        pass

    @staticmethod
    def removeWidget(widget, layout):
        layout.removeWidget(widget)
        sip.delete(widget)
        widget = None
        return widget, layout

    def addValueEntry(self):
        pass

    def balloonIdBoxChanged(self):
        if self.balloonIdBox.isChecked():
            self.balloonIdEdit.setDisabled(False)
        else:
            self.balloonIdEdit.setDisabled(True)

    def packetIdBoxChanged(self):
        if self.packetIdBox.isChecked():
            self.packetIdSpinBox.setDisabled(False)
        else:
            self.packetIdSpinBox.setDisabled(True)

    def spinBoxChanged(self):
        n = self.packetIdSpinBox.value()
        random = np.random.randint(0, int(n * '9'))
        self.packetIdLabel.setText('ex: ' + str(random))


class GraphWidget(QWidget):
    def __init__(self, parent=None):
        super(QWidget, self).__init__(parent)


class NewGraphWindow(QWidget):
    def __init__(self):
        super(QWidget, self).__init__()
        self.setWindowTitle('Create New Format')
        self.setWindowIcon(QIcon('sources/icons/PyGS.jpg'))
        self.resize(400, 100)
        # General Layout
        self.layout = QVBoxLayout(self)
        # Loading settings
        self.settings = {}
        self.settings = load_settings("settings")
        #######  NAME FRAME  #######
        self.nameFrame = QWidget()
        self.nameLayout = QHBoxLayout(self)
        self.nameLabel = QLabel(self)
        self.nameLabel.setText('Format Name:   ')
        self.nameEntry = QLineEdit(self)
        self.nameEntry.resize(1000, 40)
        self.nameLayout.addWidget(self.nameLabel)
        self.nameLayout.addWidget(self.nameEntry)
        self.nameFrame.setLayout(self.nameLayout)
        self.layout.addWidget(self.nameFrame)
        self.setLayout(self.layout)


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
        self.settings = load_settings("settings")
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
        self.dataFileLabel.setText('Example.csv')
        self.dataLayout.addWidget(self.dataLabel)
        self.dataLayout.addWidget(self.dataFileLabel)
        self.dataFrame.setLayout(self.dataLayout)
        #######  FORMAT FILE FRAME  #######
        self.formatFrame = QWidget(self)
        self.formatLayout = QHBoxLayout(self)
        self.formatLabel = QLabel(self)
        self.formatLabel.setText('Format File Name: ')
        self.formatFileLabel = QLabel(self)
        self.formatFileLabel.setText('Example.config')
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
            name = 'Example'
        self.dataFileLabel.setText('Data' + name + '.csv')
        self.formatFileLabel.setText('Format' + name + '.config')


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




