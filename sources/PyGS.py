######################## IMPORTS ########################
import os
import shutil
import sys
import time as t
import subprocess
from functools import partial

# ------------------- PyQt Modules -------------------- #
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, pyqtSlot, QTimer
from PyQt5.QtGui import *

# --------------------- Sources ----------------------- #
from sources.common.widgets import *
from sources.common.parameters import load_settings, save_settings


######################## CLASSES ########################
class PyGS(QMainWindow):
    def __init__(self, path):
        super().__init__()
        self.current_dir = path
        self.data_path = os.path.join(self.current_dir, "data")
        self.backup_path = os.path.join(self.data_path, "backups")
        self.setGeometry(500, 500, 1000, 600)
        self.setWindowTitle('Balloon Ground Station')
        self.setWindowIcon(QIcon('sources/icons/PyGS.jpg'))
        self.statusBar().showMessage('Ready')
        self.center()
        self.settings = load_settings("settings")

        ##################  VARIABLES  ##################
        if not os.path.exists('OUTPUT'):
            file = open("output", "w").close()
        self.serial = None
        self.pid = None
        self.available_ports = None
        self.formatTabList = []
        self.graphsTabList = []
        self.serialWindow = None
        self.serialMonitorTimer = QTimer()
        self.serialMonitorTimer.timeout.connect(self.checkSubProcess)
        self.output_lines = 0
        self.serialMonitorTimer.start(100)
        self.newFormatWindow = NewFormatWindow()
        self.newGraphWindow = NewGraphWindow()

        # Initialize Interface
        self._generateUI()

        # MenuBars and Actions
        self._createActions()
        self._createToolBars()
        self._createMenuBar()

        self.show()

    def _generateUI(self):
        self.dockPlotWindow = QCustomDockWidget("Plot Window", self)
        self.plotTabWidget = QCustomTabWidget(self.dockPlotWindow)
        self.dockPlotWindow.setWidget(self.plotTabWidget)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.dockPlotWindow)

        self.dockFormatWindow = QCustomDockWidget("Format Editing", self)
        self.formatTabWidget = QCustomTabWidget(self.dockPlotWindow)
        self.dockFormatWindow.setWidget(self.formatTabWidget)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.dockFormatWindow)

    def _createToolBars(self):
        self.windowToolBar = QToolBar("Windows", self)
        self.addToolBar(Qt.RightToolBarArea, self.windowToolBar)
        self.windowToolBar.addAction(self.showFormatAct)
        self.windowToolBar.addAction(self.showPlotAct)
        self.windowToolBar.addAction(self.openMonitorAct)

    def _createActions(self):
        # New Format
        self.newFormatAction = QAction('&New Format', self)
        self.newFormatAction.setStatusTip('Create New Packet Format')
        self.newFormatAction.setShortcut('Ctrl+N')
        self.newFormatAction.triggered.connect(self.newFormatTab)
        # Open Format
        self.openFormatAction = QAction('&Open', self)
        self.openFormatAction.setStatusTip('Open Packet Format')
        self.openFormatAction.setShortcut('Ctrl+O')
        self.openFormatAction.triggered.connect(self.openFormatTab)
        # Save Format
        self.saveFormatAction = QAction('&Save', self)
        self.saveFormatAction.setStatusTip('Save Packet Format')
        self.saveFormatAction.setShortcut('Ctrl+S')
        self.saveFormatAction.triggered.connect(self.saveFormatTab)
        # Save As Format
        self.saveAsFormatAction = QAction('&Save As', self)
        self.saveAsFormatAction.setStatusTip('Save Packet Format As...')
        self.saveAsFormatAction.triggered.connect(self.saveAsFormatTab)
        # Save All Formats
        self.saveAllFormatAction = QAction('&Save All', self)
        self.saveAllFormatAction.setStatusTip('Save All Packet Formats')
        self.saveAllFormatAction.triggered.connect(self.saveAllFormatTab)
        # Exit
        self.exitAct = QAction(QIcon('exit.png'), '&Exit', self)
        self.exitAct.setShortcut('Ctrl+Q')
        self.exitAct.setStatusTip('Exit application')
        self.exitAct.triggered.connect(self.close)
        # Change Header
        self.changeHeaderAct = QAction('&Change Header', self)
        self.changeHeaderAct.setStatusTip('Change Packets Header')
        self.changeHeaderAct.triggered.connect(self.changeHeader)
        # Add Plot Tab
        self.newPlotAction = QAction('&Add Plot tab', self)
        self.newPlotAction.setStatusTip('Add New Graph Tab')
        self.newPlotAction.triggered.connect(self.newPlotTab)
        # Toggle Autoscale
        self.autoscaleAct = QAction('&Autoscale', self, checkable=True, checked=self.settings["AUTOSCALE"])
        self.autoscaleAct.setStatusTip("Toggle Graphs' Autoscale")
        self.autoscaleAct.triggered.connect(self.setAutoscale)
        # Run Serial
        self.runSerialAct = QAction('&Run', self)
        self.runSerialAct.setStatusTip('Run Serial Monitoring')
        self.runSerialAct.triggered.connect(self.startSerial)
        # Stop Serial
        self.stopSerialAct = QAction('&Stop', self)
        self.stopSerialAct.setStatusTip('Stop Serial Monitoring')
        self.stopSerialAct.triggered.connect(self.stopSerial)
        # Opening Serial Monitor
        self.openMonitorAct = QAction('&Open Serial Monitor', self)
        self.openMonitorAct.setIcon(QIcon('sources/icons/Monitor.png'))
        self.openMonitorAct.setStatusTip('Open Serial Monitor')
        self.openMonitorAct.triggered.connect(self.openSerialMonitor)
        # Toggle RSSI Acquirement
        self.rssiAct = QAction('&RSSI', self, checkable=True, checked=self.settings["RSSI"])
        self.rssiAct.setStatusTip('Toggle RSSI Retrieval')
        self.rssiAct.triggered.connect(self.setRssi)
        # Visit GitHub Page
        self.githubAct = QAction('&Visit GitHub', self)
        self.githubAct.setStatusTip('Visit GitHub Page')
        self.githubAct.triggered.connect(self.openGithub)
        # Show Plot Window
        self.showPlotAct = QAction(QIcon('sources/icons/Plot.png'), "&Open Plot", self)
        self.showPlotAct.setStatusTip('Show Graph Window')
        self.showPlotAct.triggered.connect(self.dockPlotWindow.show)
        # Show Format Editing Window
        self.showFormatAct = QAction(QIcon('sources/icons/File.png'), "&Open Format", self)
        self.showFormatAct.setStatusTip('Show Format Editing Window')
        self.showFormatAct.triggered.connect(self.dockFormatWindow.show)

    def _createMenuBar(self):
        self.menubar = self.menuBar()

        ###  FILE MENU  ###
        self.fileMenu = self.menubar.addMenu('&File')
        self.fileMenu.addAction(self.newFormatAction)
        self.fileMenu.addAction(self.openFormatAction)
        self.recentMenu = QMenu('&Recent', self)
        self.recentMenu.aboutToShow.connect(self.populateRecentMenu)
        self.fileMenu.addMenu(self.recentMenu)
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.saveFormatAction)
        self.fileMenu.addAction(self.saveAsFormatAction)
        self.fileMenu.addAction(self.saveAllFormatAction)
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.exitAct)

        ###  EDIT MENU  ###
        self.editMenu = self.menubar.addMenu('&Edit')
        self.editMenu.addAction(self.changeHeaderAct)

        ###  WINDOW MENU  ###
        self.windowMenu = self.menubar.addMenu('&Window')
        self.windowMenu.addAction(self.newPlotAction)
        self.showMenu = QMenu('&Show View', self)
        # Toggle Window Views
        self.showMenu.addAction(self.dockPlotWindow.toggleViewAction())
        self.showMenu.addAction(self.dockFormatWindow.toggleViewAction())
        self.windowMenu.addMenu(self.showMenu)
        self.windowMenu.addSeparator()
        self.windowMenu.addAction(self.autoscaleAct)

        ###  TOOLS MENU  ###
        self.toolsMenu = self.menubar.addMenu('&Tools')
        self.toolsMenu.addAction(self.runSerialAct)
        self.toolsMenu.addAction(self.stopSerialAct)
        self.toolsMenu.addAction(self.openMonitorAct)
        self.toolsMenu.addSeparator()
        self.portMenu = QMenu('&Port', self)
        self.toolsMenu.addMenu(self.portMenu)
        # Baud Group
        baud_rates = self.settings["AVAILABLE_BAUDS"]
        id_baud = baud_rates.index(str(self.settings["SELECTED_BAUD"]))
        self.baudMenu = QMenu('&Baud    ' + baud_rates[id_baud], self)
        baud_group = QActionGroup(self.baudMenu)
        for baud in baud_rates:
            action = QAction(baud, self.baudMenu, checkable=True, checked=baud == baud_rates[id_baud])
            self.baudMenu.addAction(action)
            baud_group.addAction(action)
        baud_group.setExclusive(True)
        baud_group.triggered.connect(self.selectBaud)
        self.toolsMenu.addMenu(self.baudMenu)
        self.toolsMenu.addSeparator()
        self.toolsMenu.addAction(self.rssiAct)
        self.toolsMenu.aboutToShow.connect(self.populateToolsMenu)

        ###  HELP MENU  ###
        self.helpMenu = self.menubar.addMenu('&Help')
        self.helpMenu.addAction(self.githubAct)

    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def newFormatTab(self):
        self.newFormatWindow = NewFormatWindow()
        acceptButton = QPushButton('Accept', self.newFormatWindow)
        acceptButton.clicked.connect(self.acceptNewFormatTab)
        self.newFormatWindow.layout.addWidget(acceptButton)
        self.newFormatWindow.show()

    def acceptNewFormatTab(self):
        name = self.newFormatWindow.nameEntry.text()
        configFile = self.newFormatWindow.formatFileLabel.text()
        widget = FormatEditWidget(self, self.current_dir, formatFile=configFile)
        self.formatTabList.append(widget)
        self.formatTabWidget.addTab(widget, name)
        self.newFormatWindow.close()

    def newPlotTab(self):
        self.newGraphWindow = NewGraphWindow()
        acceptButton = QPushButton('Create', self.newGraphWindow)
        acceptButton.clicked.connect(self.createNewPlotTab)
        self.newGraphWindow.layout.addWidget(acceptButton)
        self.newGraphWindow.show()

    def createNewPlotTab(self):
        widget = GraphWidget(self)
        name = self.newGraphWindow.nameEntry.text()
        self.formatTabWidget.addTab(widget, name)
        self.newGraphWindow.close()

    def openFormatTab(self):
        pass

    def openRecentFile(self, filename):
        pass

    def saveFormatTab(self):
        pass

    def saveAsFormatTab(self):
        # Create Lines
        path = QFileDialog.getSaveFileName(self, 'Save File')
        with open(path, 'w') as file:
            pass
            # Add Format Tab Saving Method

    def saveAllFormatTab(self):
        pass

    def changeHeader(self):
        pass

    def startSerial(self):
        message = "Port : " + self.settings["SELECTED_PORT"] + "  Baud : "
        message += self.settings["SELECTED_BAUD"] + "\nDo you wish to continue ?"
        msg = MessageBox()
        msg.setWindowIcon(QIcon('sources/icons/PyGS.jpg'))
        msg.setWindowTitle("Running Warning")
        msg.setText(message)
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)
        msg.setStyleSheet("QLabel{min-width: 200px;}")
        msg.exec_()
        button = msg.clickedButton()
        sb = msg.standardButton(button)
        if sb == QMessageBox.Yes:
            serialPath = os.path.join(self.current_dir, "sources/SerialGS.py")
            if os.path.exists(serialPath):
                self.serial = subprocess.Popen([sys.executable, serialPath])
                self.pid = self.serial.pid
                self.serial_window.textedit.setDisabled(False)
            else:
                cancelling = MessageBox()
                cancelling.setWindowIcon(QIcon('sources/icons/PyGS.jpg'))
                cancelling.setWindowTitle("Error")
                cancelling.setText("Serial.py not found.")
                cancelling.setStandardButtons(QMessageBox.Ok)
                cancelling.setStyleSheet("QLabel{min-width: 200px;}")
                cancelling.exec_()

    def stopSerial(self):
        if self.serial is not None:
            self.serial.kill()
            self.serial.terminate()
            t.sleep(0.5)
            self.serialWindow.textedit.setDisabled(True)
            self.serial = None

    def openSerialMonitor(self):
        if self.serialWindow is None:
            self.serialWindow = SerialWindow()
            self.serialWindow.textedit.setDisabled(True)
            self.serialWindow.textedit.setReadOnly(True)
        if self.serialWindow.isVisible():
            pass
            #### ADD METHOD TO GRAB ATTENTION
        else:
            self.serialWindow.show()

    def setAutoscale(self, action):
        self.settings["AUTOSCALE"] = action
        save_settings(self.settings, "settings")

    def populateRecentMenu(self):
        self.recentMenu.clear()
        actions = []
        filenames = [f"File-{n}" for n in range(5)]
        for filename in filenames:
            action = QAction(filename, self)
            action.triggered.connect(partial(self.openRecentFile, filename))
            actions.append(action)
        self.recentMenu.addActions(actions)

    def populateToolsMenu(self):
        self.portMenu.setTitle('&Port')
        self.portMenu.setDisabled(False)
        import serial.tools.list_ports
        self.available_ports = [comport.device for comport in serial.tools.list_ports.comports()]
        if len(self.available_ports) == 0:
            self.stopSerialAct.setDisabled(True)
            self.portMenu.setDisabled(True)
            self.settings["SELECTED_PORT"] = ""
            save_settings(self.settings, "settings")
        else:
            self.portMenu.clear()
            port_group = QActionGroup(self.portMenu)
            selection = self.settings["SELECTED_PORT"]
            if selection in self.available_ports:
                for port in self.available_ports:
                    action = QAction(port, self.portMenu, checkable=True, checked=port == selection)
                    self.portMenu.addAction(action)
                    port_group.addAction(action)
                self.portMenu.setTitle('&Port    ' + selection)
            else:
                for port in self.available_ports:
                    action = QAction(port, self.portMenu, checkable=True, checked=port == self.available_ports[0])
                    self.portMenu.addAction(action)
                    port_group.addAction(action)
                self.portMenu.setTitle('&Port    ' + self.available_ports[0])
                self.settings["SELECTED_PORT"] = self.available_ports[0]
                save_settings(self.settings, "settings")
            port_group.setExclusive(True)
            port_group.triggered.connect(self.selectPort)
        if self.serial is None:
            self.stopSerialAct.setDisabled(True)
            self.runSerialAct.setDisabled(False)
        else:
            self.stopSerialAct.setDisabled(False)
            self.runSerialAct.setDisabled(True)

    def selectBaud(self, action):
        self.baudMenu.setTitle('&Baud    ' + action.text())
        self.settings["SELECTED_BAUD"] = action.text()
        save_settings(self.settings, "settings")
        # Restart Serial Connection if on
        if self.serial is not None:
            self.stopSerial()
            self.startSerial()

    def selectPort(self, action):
        self.portMenu.setTitle('&Port    ' + action.text())
        self.settings["SELECTED_PORT"] = action.text()
        save_settings(self.settings, "settings")
        # Stop Serial Connection if on
        if self.serial is not None:
            self.stopSerial()

    def setRssi(self, action):
        self.settings["RSSI"] = action
        save_settings(self.settings, "settings")
        # Restart Serial Connection if on
        if self.serial is not None:
            self.stopSerial()
            self.startSerial()

    def checkSubProcess(self):
        self.settings = load_settings("settings")
        if self.serial is not None and self.serial.poll() is not None:
            self.stopSerial()
            self.serialWindow.textedit.setDisabled(True)
        elif self.serial is not None and self.serial.poll() is None:
            with open(self.settings["output_file"], "r") as file:
                lines = file.readlines()
            if len(lines) != self.output_lines:
                self.serialWindow.textedit.append(lines[-1])
                self.output_lines = len(lines)
            if bool(self.settings["AUTOSCROLL"]):
                self.serialWindow.textedit.moveCursor(QTextCursor.End)
        else:
            pass

    @staticmethod
    def openGithub():
        import webbrowser
        webbrowser.open("https://github.com/EnguerranVidal/PyGS")

    def closeEvent(self, event):
        reply = QMessageBox.question(self, 'Message', "Are you sure to quit?", QMessageBox.Yes |
                                     QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            # Stopping Serial Connection
            self.stopSerial()
            # Removing Serial Output File
            os.remove("output")
            for window in QApplication.topLevelWidgets():
                window.close()
            # Stopping Timers
            t.sleep(0.5)
            self.serialMonitorTimer.stop()
            event.accept()
        else:
            event.ignore()
