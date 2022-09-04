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
from PyQt5.QtCore import Qt, pyqtSlot, QTimer, QModelIndex
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
    def __init__(self):
        super(QCustomTabWidget, self).__init__()
        self.setTabsClosable(True)
        self.tabCloseRequested.connect(self.closeTab)
        # for i in range(1, 10):  # add tabs here
        # self.addTab(QWidget(), 'Tab %d' % i)

    def closeTab(self, currentIndex):
        currentQWidget = self.widget(currentIndex)
        currentQWidget.deleteLater()
        self.removeTab(currentIndex)


class NewGraphWindow(QWidget):
    def __init__(self, parent=None, *args):
        super().__init__(parent, *args)
        self.setWindowTitle('Open New Plot Window')
        self.setWindowIcon(QIcon('sources/icons/PyGS.jpg'))
        self.resize(400, 100)
        self.dlgLayout = QVBoxLayout()
        self.formLayout = QFormLayout()
        self.nameEdit = QLineEdit()
        self.formLayout.addRow('Name:', self.nameEdit)
        self.dlgLayout.addLayout(self.formLayout)
        self.buttons = QDialogButtonBox()
        self.buttons.setStandardButtons(QDialogButtonBox.Cancel | QDialogButtonBox.Ok)
        self.dlgLayout.addWidget(self.buttons)
        self.setLayout(self.dlgLayout)


class NewFormatWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Create New Format')
        self.setWindowIcon(QIcon('sources/icons/PyGS.jpg'))
        self.dataChanged = False
        self.saveChanged = False
        self.resize(400, 100)
        self.dlgLayout = QVBoxLayout()
        self.formLayout = QFormLayout()
        self.nameEdit = QLineEdit()
        self.nameEdit.textChanged.connect(self.editLineEdits)
        self.dataEdit = QLineEdit()
        self.formatEdit = QLineEdit()
        self.formLayout.addRow('Name:', self.nameEdit)
        self.formLayout.addRow('Data File:', self.dataEdit)
        self.formLayout.addRow('Save File:', self.formatEdit)
        self.dlgLayout.addLayout(self.formLayout)
        self.buttons = QDialogButtonBox()
        self.buttons.setStandardButtons(QDialogButtonBox.Cancel | QDialogButtonBox.Ok)
        self.dlgLayout.addWidget(self.buttons)
        self.setLayout(self.dlgLayout)

    def editLineEdits(self):
        name = self.nameEdit.text()
        if len(name) == 0:
            name = 'Example'
        self.dataEdit.setText(name.capitalize() + 'Data' + '.csv')
        self.formatEdit.setText(name.capitalize() + 'Format' + '.config')


class HeaderChangeWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Change Header')
        self.setWindowIcon(QIcon('sources/icons/PyGS.jpg'))
        self.resize(400, 100)
        self.dlgLayout = QVBoxLayout()
        self.formLayout = QFormLayout()
        self.headerEdit = QLineEdit()
        self.formLayout.addRow('Header:', self.headerEdit)
        self.dlgLayout.addLayout(self.formLayout)
        self.buttons = QDialogButtonBox()
        self.buttons.setStandardButtons(QDialogButtonBox.Cancel | QDialogButtonBox.Ok)
        self.dlgLayout.addWidget(self.buttons)
        self.setLayout(self.dlgLayout)


class TrackedBalloonsWindow(QWidget):
    def __init__(self, path, parent=None):
        super().__init__(parent)
        self.current_dir = path
        self.format_path = os.path.join(self.current_dir, "formats")
        self.setWindowTitle('Tracked Balloons')
        self.setWindowIcon(QIcon('sources/icons/PyGS.jpg'))
        self.settings = load_settings("settings")

        # Selected Balloon List
        self.selectedList = BalloonsListWidget(self.current_dir)
        self.selectedLabel = QLabel('Tracked Formats')

        # Trackable Balloons List
        self.availableList = BalloonsListWidget(self.current_dir)
        self.availableLabel = QLabel('Available Formats')

        layout = QGridLayout()
        layout.addWidget(self.selectedLabel, 0, 0)
        layout.addWidget(self.selectedList, 1, 0)
        layout.addWidget(self.availableLabel, 0, 1)
        layout.addWidget(self.availableList, 1, 1)
        self.setLayout(layout)

        self.populateFormats()

    def populateFormats(self):
        path = self.format_path
        trackedFormats = self.settings['FORMAT_FILES']
        availableFormats = [file for file in os.listdir(path) if os.path.isfile(os.path.join(path, file))]
        # Verify Present Formats and Change Settings
        for i in trackedFormats:
            if i not in availableFormats:
                trackedFormats.remove(i)
        self.settings['FORMAT_FILES'] = trackedFormats
        save_settings(self.settings, 'settings')
        for i in trackedFormats:
            if i in availableFormats:
                availableFormats.remove(i)
        # Fill both lists
        for i in trackedFormats:
            self.selectedList.addItem(i)
        for i in availableFormats:
            self.availableList.addItem(i)

    def formatName(self, file):
        pass


class BalloonsListWidget(QListWidget):
    def __init__(self, path):
        super(QListWidget, self).__init__()
        self.current_dir = path
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setDragDropOverwriteMode(False)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setDefaultDropAction(Qt.MoveAction)

    def dropEvent(self, event):
        source = event.source()
        items = source.selectedItems()
        for i in items:
            source.takeItem(source.indexFromItem(i).row())
            self.addItem(i)
