######################## IMPORTS ########################
import time

# ------------------- PyQt Modules -------------------- #
from PyQt5.QtCore import QDateTime, QThread

# --------------------- Sources ----------------------- #
from sources.common.Widgets import *
from sources.common.DataCapture import DataWorker
from sources.common.PacketWidgets import PacketTabWidget
from sources.common.GraphWidgets import GraphTabWidget
from sources.common.parameters import load_settings, save_settings, check_format


######################## CLASSES ########################
class PyGS(QMainWindow):
    def __init__(self, path):
        super().__init__()
        self.current_dir = path
        self.format_path = os.path.join(self.current_dir, "formats")
        self.data_path = os.path.join(self.current_dir, "data")
        self.backup_path = os.path.join(self.data_path, "backups")
        # Main Window Settings
        self.setGeometry(500, 500, 1000, 600)
        self.setWindowTitle('Weather Balloon Ground Station')
        self.setWindowIcon(QIcon('sources/icons/PyGS.jpg'))
        self.settings = load_settings("settings")
        self.center()
        # Date&Time in StatusBar
        self.datetime = QDateTime.currentDateTime()
        self.dateLabel = QLabel(self.datetime.toString('dd.MM.yyyy  hh:mm:ss'))
        self.dateLabel.setStyleSheet('border: 0;')
        self.statusBar().addPermanentWidget(self.dateLabel)
        # FPS in StatusBar
        self.lastUpdate = time.perf_counter()
        self.avgFps = 0.0
        self.fpsLabel = QLabel('Fps : ---')
        self.fpsLabel.setStyleSheet('border: 0;')
        self.statusBar().addPermanentWidget(self.fpsLabel)
        # Status Bar Message and Timer
        self.statusBar().showMessage('Ready')
        self.statusDateTimer = QTimer()
        self.statusDateTimer.timeout.connect(self.updateStatus)
        self.statusDateTimer.start(0)

        ##################  VARIABLES  ##################
        if not os.path.exists('OUTPUT'):
            file = open("output", "w").close()
        self.serial = None
        self.pid = None
        self.available_ports = None
        self.packetTabList = []
        self.graphsTabList = []
        self.serialWindow = SerialWindow()

        self.serialMonitorTimer = QTimer()
        self.serialMonitorTimer.timeout.connect(self.checkSubProcess)
        self.outputLines = 0
        self.serialMonitorTimer.start(100)
        self.newFormatWindow = None
        self.newGraphWindow = None
        self.newPlotWindow = None
        self.changeHeaderWindow = None
        self.trackedFormatsWindow = None

        self.dataCaptureWorker = None
        self.dataCaptureThread = None

        # Initialize Interface
        self._checkEnvironment()
        self._generateUI()
        self._createActions()
        self._createMenuBar()

        self.show()

    def _generateUI(self):
        self.generalTabWidget = QTabWidget(self)
        self.generalTabWidget.setTabBar(QTabBar(self.generalTabWidget))
        self.generalTabWidget.setTabPosition(self.generalTabWidget.West)

        # Packet Tab Widget -----------------------------------------
        self.packetTabWidget = PacketTabWidget(self.current_dir)
        self.graphsTabWidget = GraphTabWidget(self.current_dir)
        self.graphWidgetsList = []

        # Adding Tabs to Main Widget -------------------------------
        self.generalTabWidget.addTab(self.graphsTabWidget, 'Graphs')
        self.generalTabWidget.addTab(self.packetTabWidget, 'Packets')
        self.setCentralWidget(self.generalTabWidget)

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
        # Import Format
        self.importFormatAction = QAction('&Import Format', self)
        self.importFormatAction.setStatusTip('Import Format')
        self.importFormatAction.triggered.connect(self.importFormat)
        # Tracked Formats
        self.trackedFormatAction = QAction('&Tracked Formats', self)
        self.trackedFormatAction.setStatusTip('Open Tracked Formats Selection Window')
        self.trackedFormatAction.triggered.connect(self.openTrackedFormats)
        # Exit
        self.exitAct = QAction(QIcon('exit.png'), '&Exit', self)
        self.exitAct.setShortcut('Ctrl+Q')
        self.exitAct.setStatusTip('Exit application')
        self.exitAct.triggered.connect(self.close)
        # Change Header
        self.changeHeaderAct = QAction('&Change Header', self)
        self.changeHeaderAct.setStatusTip('Change Packets Header')
        self.changeHeaderAct.triggered.connect(self.openChangeHeader)
        # Add Plot Tab
        self.newGraphAction = QAction('&Add Graph Tab', self)
        self.newGraphAction.setStatusTip('Add New Graph Tab')
        self.newGraphAction.triggered.connect(self.newGraphTab)
        # Add Graph Tab
        self.newPlotAction = QAction('&Add Plot', self)
        self.newPlotAction.setStatusTip('Add New Plot')
        self.newPlotAction.triggered.connect(self.newPlot)
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
        self.manageFormatsMenu = QMenu('&Manage Formats', self)
        self.manageFormatsMenu.addAction(self.importFormatAction)
        self.manageFormatsMenu.addAction(self.trackedFormatAction)
        self.fileMenu.addMenu(self.manageFormatsMenu)
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.exitAct)

        ###  EDIT MENU  ###
        self.editMenu = self.menubar.addMenu('&Edit')
        self.editMenu.addAction(self.changeHeaderAct)

        ###  WINDOW MENU  ###
        self.windowMenu = self.menubar.addMenu('&Window')
        self.manageGraphsMenu = QMenu('&Manage Graphs', self)
        self.manageGraphsMenu.addAction(self.newGraphAction)
        self.manageGraphsMenu.addAction(self.newPlotAction)
        self.windowMenu.addMenu(self.manageGraphsMenu)
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

    def _checkEnvironment(self):
        if not os.path.exists(self.format_path):
            os.mkdir(self.format_path)
        if not os.path.exists(self.data_path):
            os.mkdir(self.data_path)
        if not os.path.exists(self.backup_path):
            os.mkdir(self.backup_path)

    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def newFormatTab(self):
        self.newFormatWindow = NewFormatWindow()
        self.newFormatWindow.buttons.accepted.connect(self.acceptNewFormatTab)
        self.newFormatWindow.buttons.rejected.connect(self.newFormatWindow.close)
        self.newFormatWindow.show()

    def acceptNewFormatTab(self):
        name = self.newFormatWindow.nameEdit.text()
        configFile = self.newFormatWindow.formatEdit.text()
        saveFile = self.newFormatWindow.dataEdit.text()
        self.packetTabWidget.newFormat(name, configFile, saveFile)
        self.newFormatWindow.close()

    def newGraphTab(self):
        self.newGraphWindow = NewGraphWindow()
        self.newGraphWindow.buttons.accepted.connect(self.createNewGraphTab)
        self.newGraphWindow.buttons.rejected.connect(self.newGraphWindow.close)
        self.newGraphWindow.show()

    def newPlot(self):
        if len(self.graphsTabWidget.openedTabs) > 0:
            self.newPlotWindow = NewPlotWindow()
            self.newPlotWindow.buttons.accepted.connect(self.createNewPlot)
            self.newPlotWindow.buttons.rejected.connect(self.newPlotWindow.close)
            self.newPlotWindow.show()
        else:
            cancelling = MessageBox()
            cancelling.setWindowIcon(QIcon('sources/icons/PyGS.jpg'))
            cancelling.setWindowTitle("Error")
            cancelling.setText("No Graph tabs are \n set to add a plot too.")
            cancelling.setStandardButtons(QMessageBox.Ok)
            cancelling.setStyleSheet("QLabel{min-width: 200px;}")
            cancelling.exec_()

    def createNewPlot(self):
        currentIndex = self.graphsTabWidget.graphCentralWindow.currentIndex()
        name = self.newPlotWindow.nameEdit.text()
        self.graphsTabWidget.openedTabs[currentIndex].addDock(name)
        self.newPlotWindow.close()

    def createNewGraphTab(self):
        name = self.newGraphWindow.nameEdit.text()
        self.graphsTabWidget.addDockTab(name)
        self.newGraphWindow.close()

    def openFormatTab(self):
        if os.path.exists(os.path.join(self.current_dir, 'formats')):
            path = QFileDialog.getOpenFileName(self, 'Open Packet Format', self.format_path)
        else:
            path = QFileDialog.getOpenFileName(self, 'Open Packet Format')
        if path[0] != '' and os.path.exists(path[0]):
            self.packetTabWidget.openFormat(path[0])

    def openRecentFile(self, filename):
        pass

    def saveFormatTab(self):
        self.packetTabWidget.saveFormat()
        self.graphsTabWidget.fillComboBox()

    def saveAsFormatTab(self):
        # Create Lines
        path = QFileDialog.getSaveFileName(self, 'Save File')
        self.packetTabWidget.saveFormat(path[0])
        self.graphsTabWidget.fillComboBox()

    def saveAllFormatTab(self):
        self.packetTabWidget.saveAllFormats()

    def openTrackedFormats(self):
        self.trackedFormatsWindow = TrackedBalloonsWindow(self.current_dir)
        self.trackedFormatsWindow.buttons.accepted.connect(self.editTrackedFormats)
        self.trackedFormatsWindow.buttons.rejected.connect(self.trackedFormatsWindow.close)
        self.trackedFormatsWindow.show()

    def editTrackedFormats(self):
        trackedFormats = self.trackedFormatsWindow.getListedValues()
        self.settings['FORMAT_FILES'] = trackedFormats
        save_settings(self.settings, 'settings')
        self.trackedFormatsWindow.close()
        self.graphsTabWidget.fillComboBox()

    def importFormat(self):
        path = QFileDialog.getOpenFileName(self, 'Import Packet Format')
        # Verifying if chosen file is a format
        if check_format(path[0]):
            # Finally copy the file into our format repository
            shutil.copy2(path[0], self.format_path)
        else:
            cancelling = MessageBox()
            cancelling.setWindowIcon(QIcon('sources/icons/PyGS.jpg'))
            cancelling.setWindowTitle("Error")
            cancelling.setText("This file does not satisfy the required format.")
            cancelling.setStandardButtons(QMessageBox.Ok)
            cancelling.exec_()

    def openChangeHeader(self):
        self.changeHeaderWindow = HeaderChangeWindow()
        acceptButton = QPushButton('Create', self.changeHeaderWindow)
        acceptButton.clicked.connect(self.acceptChangeHeader)
        self.changeHeaderWindow.dlgLayout.addWidget(acceptButton)
        self.changeHeaderWindow.show()

    def acceptChangeHeader(self):
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
                self.serialWindow.textedit.setDisabled(False)
                # Data Retrieving from Thread/Worker
                self.dataCaptureThread = QThread()
                self.dataCaptureWorker = DataWorker(self.current_dir)
                self.dataCaptureWorker.moveToThread(self.dataCaptureThread)
                self.dataCaptureThread.started.connect(self.dataCaptureWorker.run)
                self.dataCaptureWorker.finished.connect(self.dataCaptureThread.quit)
                self.dataCaptureWorker.finished.connect(self.dataCaptureWorker.deleteLater)
                self.dataCaptureThread.finished.connect(self.dataCaptureThread.deleteLater)
                self.dataCaptureWorker.progress.connect(self.reportProgress)
                self.dataCaptureThread.start()

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
            self.serial = None
            self.serialWindow.textedit.setDisabled(True)
            self.dataCaptureWorker.interrupt()

    def reportProgress(self, content):
        #### UPDATING GRAPHS ####
        self.graphsTabWidget.updateGraphs(content)

    def openSerialMonitor(self):
        if self.serialWindow is None:
            self.serialWindow = SerialWindow()
            self.serialWindow.textedit.setDisabled(True)
            self.serialWindow.textedit.setReadOnly(True)
        if self.serialWindow.isVisible():
            self.serialWindow = SerialWindow()
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
            with open(self.settings["OUTPUT_FILE"], "r") as file:
                lines = file.readlines()
            if len(lines) != self.outputLines:
                needScrolling = False
                value = self.serialWindow.textedit.verticalScrollBar().maximum()
                if self.serialWindow.textedit.verticalScrollBar().value() == value:
                    needScrolling = True
                if len(lines) == 0:
                    self.serialWindow.textedit.setText('')
                else:
                    self.serialWindow.textedit.append(lines[-1])
                self.outputLines = len(lines)
                if bool(self.settings["AUTOSCROLL"]) and needScrolling:
                    value = self.serialWindow.textedit.verticalScrollBar().maximum()
                    self.serialWindow.textedit.verticalScrollBar().setValue(value)
        else:
            pass

    def currentGeneralTab(self, *args):
        pass

    def whatTab(self):
        currentIndex = self.tabWidget.currentIndex()
        currentWidget = self.tabWidget.currentWidget()
        print(currentIndex)

    def updateStatus(self):
        self.datetime = QDateTime.currentDateTime()
        self.dateLabel.setText(self.datetime.toString('dd.MM.yyyy  hh:mm:ss'))
        now = time.perf_counter()
        fps = 1.0 / (now - self.lastUpdate)
        self.lastUpdate = now
        self.avgFps = self.avgFps * 0.8 + fps * 0.2
        self.fpsLabel.setText('Fps : %0.2f ' % self.avgFps)

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
            # Closing All Sub Windows
            for window in QApplication.topLevelWidgets():
                window.close()
            # Stopping Timers
            t.sleep(0.5)
            self.serialMonitorTimer.stop()
            # self.dataCaptureThread.terminate()
            event.accept()
        else:
            event.ignore()
