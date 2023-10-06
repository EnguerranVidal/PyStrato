######################## IMPORTS ########################
from datetime import datetime
from functools import partial

# ------------------- PyQt Modules -------------------- #
from PyQt5.QtCore import QDateTime, QThread, Qt

# --------------------- Sources ----------------------- #
from sources.SerialGS import SerialMonitor
from sources.common.FileHandling import nameGiving, loadSearchItemsFromJson
from sources.common.Widgets import *

from sources.databases.general import PacketTabWidget
from sources.displays.general import DisplayTabWidget
from sources.weather.general import WeatherWindow


######################## CLASSES ########################
class PyStratoGui(QMainWindow):
    def __init__(self, path):
        super().__init__()
        self.loadingData = None
        self.hide()
        self.currentDir = path
        self.mainIcon = QIcon('sources/icons/PyStrato')
        # FOLDER PATHS
        self.formatPath = os.path.join(self.currentDir, "formats")
        self.dataPath = os.path.join(self.currentDir, "data")
        self.savesPath = os.path.join(self.dataPath, 'saves')
        self.backupPath = os.path.join(self.dataPath, "backups")
        self.presetPath = os.path.join(self.dataPath, 'presets')
        self.autosavePath = os.path.join(self.presetPath, 'autosaves')
        self.examplesPath = os.path.join(self.presetPath, 'examples')

        # Main Window Settings
        self.setGeometry(500, 500, 1000, 600)
        self.setWindowTitle('PyStrato')
        self.setWindowIcon(self.mainIcon)
        self.settings = loadSettings("settings")
        self._center()
        # FPS in StatusBar
        self.lastUpdate = time.perf_counter()
        self.avgFps = 0.0
        self.fpsLabel = QLabel('Fps : ---')
        self.fpsLabel.setStyleSheet('border: 0;')
        self.statusBar().addPermanentWidget(self.fpsLabel)
        # Date&Time in StatusBar
        self.datetime = QDateTime.currentDateTime()
        self.dateLabel = QLabel(self.datetime.toString('dd.MM.yyyy  hh:mm:ss'))
        self.dateLabel.setStyleSheet('border: 0;')
        self.statusBar().addPermanentWidget(self.dateLabel)
        # Status Bar Message and Timer
        self.statusBar().showMessage('Ready')
        self.statusDateTimer = QTimer()
        self.statusDateTimer.timeout.connect(self.updateStatus)
        self.statusDateTimer.start(1000)

        ##################  VARIABLES  ##################
        self.serial = None
        self.available_ports = None
        self.packetTabList = []
        self.graphsTabList = []
        self.serialWindow = SerialWindow()
        self.serialWindow.textedit.setDisabled(True)
        self.layoutPresetWindow = None

        self.serialMonitorTimer = QTimer()
        self.serialMonitorTimer.timeout.connect(self.checkSerialMonitor)
        self.serialMonitorTimer.start(100)
        self.newFormatWindow = None
        self.newGraphWindow = None
        self.newPlotWindow = None
        self.changeHeaderWindow = None
        self.trackedFormatsWindow = None
        self.layoutAutosaveTimer = None

    def initializeUI(self, data=None):
        self.loadingData = data
        # Initialize Interface
        self._checkEnvironment()
        self._generateTabs()
        self._createActions()
        self._createMenuBar()
        self._createToolBars()
        self._initializeDisplayLayout()

        # Populate Menus
        self.populateFileMenu()
        self.populateToolsMenu()
        self.populateLayoutMenu()

        if self.settings['LAYOUT_AUTOSAVE']:
            self.startupAutosave()

    def _generateTabs(self):
        self.generalTabWidget = QTabWidget(self)
        self.generalTabBar = QTabBar(self.generalTabWidget)
        self.generalTabBar.setStyleSheet("QTabBar::tab { min-height: 125px; max-height: 125px; }")
        self.generalTabWidget.setTabBar(self.generalTabBar)
        self.generalTabWidget.setTabPosition(self.generalTabWidget.West)

        # Packet Tab Widget -----------------------------------------
        self.packetTabWidget = PacketTabWidget(self.currentDir)
        self.displayTabWidget = DisplayTabWidget(self.currentDir)
        self.weatherTabWidget = WeatherWindow(self.loadingData, self.currentDir)
        self.graphWidgetsList = []
        # Show created tabs
        self.packetTabWidget.show()
        self.displayTabWidget.show()
        self.weatherTabWidget.show()
        # Adding Tabs to Main Widget -------------------------------
        self.generalTabWidget.addTab(self.displayTabWidget, 'DISPLAY')
        self.generalTabWidget.addTab(self.packetTabWidget, 'PACKETS')
        self.generalTabWidget.addTab(self.weatherTabWidget, 'WEATHER')

        self.generalTabWidget.currentChanged.connect(self.manageToolBars)
        self.setCentralWidget(self.generalTabWidget)

    def _createToolBars(self):
        ########### DATABASES ###########
        self.databasesToolBar = QToolBar("Package", self)
        self.databasesToolBar.addAction(self.newFormatAction)
        self.databasesToolBar.addAction(self.openFormatAction)
        self.databasesToolBar.addAction(self.saveFormatAction)
        self.databasesToolBar.addSeparator()

        ########### DISPLAYS ###########
        self.displaysToolBar = QToolBar('Display', self)
        self.displaysToolBar.addAction(self.newDisplayTabAct)
        self.displaysToolBar.addAction(self.closeDisplayTabAct)
        self.displaysToolBar.addSeparator()
        # Indicators
        indicatorToolButton = QToolButton()
        indicatorToolButton.setDefaultAction(self.newSimpleIndicatorAct)
        indicatorSubMenu = QMenu()
        indicatorSubMenu.addAction(self.newSimpleIndicatorAct)
        indicatorSubMenu.addAction(self.newGridIndicatorAct)
        indicatorToolButton.setMenu(indicatorSubMenu)
        self.displaysToolBar.addWidget(indicatorToolButton)
        # Graphs
        graphToolButton = QToolButton()
        graphToolButton.setDefaultAction(self.newMultiCurveAct)
        graphSubMenu = QMenu()
        graphSubMenu.addAction(self.newMultiCurveAct)
        graphToolButton.setMenu(graphSubMenu)
        self.displaysToolBar.addWidget(graphToolButton)
        # RUN / STOP
        self.displaysToolBar.addSeparator()
        self.displaysToolBar.addAction(self.runSerialAct)
        self.displaysToolBar.addAction(self.stopSerialAct)

        ########### WEATHER ###########
        self.weatherToolBar = QToolBar("Weather", self)
        # SPACER
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.weatherToolBar.addWidget(spacer)
        # GEOLOCATION
        self.weatherToolBar.addAction(self.updatingWeatherAct)
        self.weatherToolBar.addAction(self.getGeolocationAct)

        # SEARCH BAR
        searchOptions = self.weatherTabWidget.forecastTabDisplay.citiesDataFrame['format']
        self.locationSearchBar = SearchBar(self.currentDir, searchOptions)
        self.locationSearchBar.setFixedWidth(300)
        self.locationSearchBar.setFixedHeight(30)
        self.locationSearchBar.searchDone.connect(self.onLocationSearchedClicked)
        self.weatherToolBar.addWidget(self.locationSearchBar)

        ########### APPEARANCE ###########
        self.addToolBar(self.databasesToolBar)
        self.addToolBar(self.displaysToolBar)
        self.addToolBar(self.weatherToolBar)
        self.generalTabWidget.currentChanged.connect(self.manageToolBars)
        self.manageToolBars(0)

    def manageToolBars(self, index):
        # Show the ToolBar based on the appearing tab
        if index == 0:  # DISPLAYS
            self.databasesToolBar.hide()
            self.displaysToolBar.show()
            self.weatherToolBar.hide()
        elif index == 1:  # PACKAGES
            self.databasesToolBar.show()
            self.displaysToolBar.hide()
            self.weatherToolBar.hide()
        elif index == 2:  # WEATHER
            self.databasesToolBar.hide()
            self.displaysToolBar.hide()
            self.weatherToolBar.show()

    def _createActions(self):
        ########### FORMATS ###########
        # New Format
        self.newFormatAction = QAction('&New Format', self)
        self.newFormatAction.setStatusTip('Create New Packet Format')
        self.newFormatAction.setIcon(QIcon('sources/icons/light-theme/icons8-new-window-96.png'))
        self.newFormatAction.setShortcut('Ctrl+N')
        self.newFormatAction.triggered.connect(self.newFormatTab)
        # Open Format
        self.openFormatAction = QAction('&Open', self)
        self.openFormatAction.setStatusTip('Open Packet Format')
        self.openFormatAction.setIcon(QIcon('sources/icons/light-theme/icons8-open-in-browser-96.png'))
        self.openFormatAction.setShortcut('Ctrl+O')
        self.openFormatAction.triggered.connect(self.openFormatTab)
        # Save Format
        self.saveFormatAction = QAction('&Save', self)
        self.saveFormatAction.setStatusTip('Save Packet Format')
        self.saveFormatAction.setIcon(QIcon('sources/icons/light-theme/icons8-save-96.png'))
        self.saveFormatAction.setShortcut('Ctrl+S')
        self.saveFormatAction.triggered.connect(self.saveFormatTab)
        # Save As Format
        self.saveAsFormatAction = QAction('&Save As', self)
        self.saveAsFormatAction.setStatusTip('Save Packet Format As...')
        self.saveAsFormatAction.triggered.connect(self.saveAsFormatTab)
        # Save All Formats
        self.saveAllFormatAction = QAction('&Save All', self)
        self.saveAllFormatAction.setStatusTip('Save All Packet Formats')
        self.saveAllFormatAction.setIcon(QIcon('sources/icons/light-theme/icons8-save-all-96.png'))
        self.saveAllFormatAction.triggered.connect(self.saveAllFormatTab)
        # Close Format
        self.closeFormatAction = QAction('&Close', self)
        self.closeFormatAction.setStatusTip('Close Current Format')
        self.closeFormatAction.setIcon(QIcon('sources/icons/light-theme/icons8-close-window-96.png'))
        self.closeFormatAction.triggered.connect(self.closeFormatTab)
        # Import Format
        self.importFormatAction = QAction('&Import Format', self)
        self.importFormatAction.setStatusTip('Import Format')
        self.importFormatAction.setIcon(QIcon('sources/icons/light-theme/icons8-download-96.png'))
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

        ########### WINDOW ###########
        # LAYOUT -----------------------------------------------------
        # Save Layout
        self.saveLayoutAct = QAction('&Save', self)
        self.saveLayoutAct.setStatusTip('Save Display Layout')
        self.saveLayoutAct.triggered.connect(self.saveLayout)
        # Save As Layout
        self.saveAsLayoutAct = QAction('&Save As', self)
        self.saveAsLayoutAct.setStatusTip('Save Display Layout As')
        self.saveAsLayoutAct.triggered.connect(self.saveLayoutAs)
        # Restore Layout
        self.restoreLayoutAct = QAction('&Restore', self)
        self.restoreLayoutAct.setStatusTip('Restore Current Layout')
        self.restoreLayoutAct.triggered.connect(self.restoreLayout)
        # Import Layout
        self.importLayoutAct = QAction('&Import', self)
        self.importLayoutAct.setStatusTip('Import External Layout')
        self.importLayoutAct.triggered.connect(self.importLayout)
        # Export Layout
        self.exportLayoutAct = QAction('&Export As', self)
        self.exportLayoutAct.setStatusTip('Export Layout As JSON')
        self.exportLayoutAct.triggered.connect(self.exportLayoutJSON)
        # Manage Layouts
        self.manageLayoutAct = QAction('&Manage Layouts', self)
        self.manageLayoutAct.setStatusTip('Open Layout Manager')
        self.manageLayoutAct.triggered.connect(self.openLayoutManager)
        # Set Layout Autosave
        self.layoutAutoSaveAct = QAction('&AutoSave', self, checkable=True,
                                         checked=self.settings["LAYOUT_AUTOSAVE"])
        self.layoutAutoSaveAct.setStatusTip('Toggle Layout Autosave')
        self.layoutAutoSaveAct.triggered.connect(self.setLayoutAutoSave)

        ########### DISPLAYS ###########
        # Add New Display Tab
        self.newDisplayTabAct = QAction('&New Display Tab', self)
        self.newDisplayTabAct.setIcon(QIcon('sources/icons/light-theme/icons8-add-folder-96.png'))
        self.newDisplayTabAct.setStatusTip('Create New Display Tab')
        self.newDisplayTabAct.setShortcut('Ctrl+Shift+N')
        self.newDisplayTabAct.triggered.connect(lambda: self.displayTabWidget.addNewTab())
        # Close Display Tab
        self.closeDisplayTabAct = QAction('&Close Display Tab', self)
        self.closeDisplayTabAct.setIcon(QIcon('sources/icons/light-theme/icons8-delete-folder-96.png'))
        self.closeDisplayTabAct.setStatusTip('Close Display Tab')
        self.closeDisplayTabAct.setShortcut('Ctrl+Shift+X')
        self.closeDisplayTabAct.triggered.connect(self.displayTabWidget.closeCurrentTab)
        # Add Simple Indicator
        self.newSimpleIndicatorAct = QAction('&Simple Indicator', self)
        self.newSimpleIndicatorAct.setIcon(QIcon('sources/icons/light-theme/icons8-full-screen-96.png'))
        self.newSimpleIndicatorAct.setStatusTip('Add New Simple Indicator')
        self.newSimpleIndicatorAct.triggered.connect(self.displayTabWidget.addSimpleIndicator)
        # Add Grid Indicator
        self.newGridIndicatorAct = QAction('&Grid Indicator', self)
        self.newGridIndicatorAct.setIcon(QIcon('sources/icons/light-theme/icons8-four-squares-96.png'))
        self.newGridIndicatorAct.setStatusTip('Add New Grid Simple Indicator')
        self.newGridIndicatorAct.triggered.connect(self.displayTabWidget.addGridIndicator)
        # Add MultiCurve Graph
        self.newMultiCurveAct = QAction('&MultiCurve Graph', self)
        self.newMultiCurveAct.setIcon(QIcon('sources/icons/light-theme/icons8-combo-chart-96.png'))
        self.newMultiCurveAct.setStatusTip('Add New MultiCurve Graph')
        self.newMultiCurveAct.triggered.connect(self.displayTabWidget.addMultiCurveGraph)

        ########### TOOLS ###########
        # Run Serial
        self.runSerialAct = QAction('&Run', self)
        self.runSerialAct.setShortcut('Ctrl+R')
        self.runSerialAct.setIcon(QIcon('sources/icons/light-theme/icons8-play-96.png'))
        self.runSerialAct.setStatusTip('Run Serial Monitoring')
        self.runSerialAct.triggered.connect(self.startSerial)
        # Stop Serial
        self.stopSerialAct = QAction('&Stop', self)
        self.stopSerialAct.setIcon(QIcon('sources/icons/light-theme/icons8-stop-96.png'))
        self.stopSerialAct.setStatusTip('Stop Serial Monitoring')
        self.stopSerialAct.triggered.connect(self.stopSerial)
        # Opening Serial Monitor
        self.openMonitorAct = QAction('&Open Serial Monitor', self)
        self.openMonitorAct.setShortcut('Ctrl+M')
        self.openMonitorAct.setIcon(QIcon('sources/icons/light-theme/icons8-monitor-96.png'))
        self.openMonitorAct.setStatusTip('Open Serial Monitor')
        self.openMonitorAct.triggered.connect(self.openSerialMonitor)

        ########### WEATHER ###########
        # Updating Weather Tabs
        self.updatingWeatherAct = QAction('&Update Weather Data', self)
        self.updatingWeatherAct.setIcon(QIcon('sources/icons/light-theme/icons8-reset-96.png'))
        self.updatingWeatherAct.setStatusTip('Updating All Weather Tabs')
        self.updatingWeatherAct.triggered.connect(self.updateWeatherTabs)
        # Using Geolocation
        self.getGeolocationAct = QAction('&Get GeoLocation Weather', self)
        self.getGeolocationAct.setIcon(QIcon('sources/icons/light-theme/icons8-my-location-96.png'))
        self.getGeolocationAct.setStatusTip('Get Weather From Geolocation')
        self.getGeolocationAct.triggered.connect(self.getWeatherForGeolocation)

        ########### HELP ###########
        # Toggle Emulator Mode
        self.emulatorAct = QAction('&Emulator Mode', self, checkable=True, checked=self.settings["EMULATOR_MODE"])
        self.emulatorAct.setStatusTip("Toggle Emulator mode")
        self.emulatorAct.triggered.connect(self.setEmulatorMode)
        # Visit GitHub Page
        self.githubAct = QAction('&Visit GitHub', self)
        self.githubAct.setIcon(QIcon('sources/icons/light-theme/icons8-github-96.png'))
        self.githubAct.setStatusTip('Visit GitHub Page')
        self.githubAct.triggered.connect(self.openGithub)
        # Open About Page
        self.aboutAct = QAction('&About', self)
        self.aboutAct.setIcon(QIcon('sources/icons/light-theme/icons8-help-96.png'))
        self.aboutAct.setStatusTip('About This Software')
        self.aboutAct.triggered.connect(self.openAbout)

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
        self.fileMenu.addAction(self.closeFormatAction)
        self.fileMenu.addSeparator()
        self.manageFormatsMenu = QMenu('&Manage Formats', self)
        self.manageFormatsMenu.addAction(self.importFormatAction)
        self.manageFormatsMenu.addAction(self.trackedFormatAction)
        self.fileMenu.addMenu(self.manageFormatsMenu)
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.exitAct)
        self.fileMenu.aboutToShow.connect(self.populateFileMenu)

        ###  EDIT MENU  ###
        self.editMenu = self.menubar.addMenu('&Edit')

        ###  INSERT MENU  ###
        self.insertMenu = self.menubar.addMenu('&Insert')
        # Display Menu ----------------------
        self.displayMenu = self.insertMenu.addMenu('&Displays')
        # Indicators
        self.indicatorMenu = QMenu('&Indicators')
        self.indicatorMenu.addAction(self.newSimpleIndicatorAct)
        self.indicatorMenu.addAction(self.newGridIndicatorAct)
        # Graphs
        self.graphsMenu = QMenu('&Graphs')
        self.graphsMenu.addAction(self.newMultiCurveAct)
        self.displayMenu.addMenu(self.indicatorMenu)
        self.displayMenu.addMenu(self.graphsMenu)
        self.insertMenu.addMenu(self.displayMenu)

        ###  WINDOW MENU  ###
        self.windowMenu = self.menubar.addMenu('&Window')
        self.layoutMenu = QMenu('&Layout')
        self.layoutMenu.addAction(self.saveLayoutAct)
        self.layoutMenu.addAction(self.saveAsLayoutAct)
        self.layoutMenu.addSeparator()
        self.layoutMenu.addAction(self.restoreLayoutAct)
        self.layoutMenu.addAction(self.importLayoutAct)
        self.layoutMenu.addAction(self.exportLayoutAct)
        self.layoutMenu.addSeparator()
        self.layoutMenu.addAction(self.manageLayoutAct)
        self.layoutMenu.addAction(self.layoutAutoSaveAct)
        self.layoutMenu.aboutToShow.connect(self.populateLayoutMenu)
        self.windowMenu.addMenu(self.layoutMenu)
        self.windowMenu.addSeparator()
        self.displayMenu = QMenu('&Display Tabs')
        self.displayMenu.addAction(self.newDisplayTabAct)
        self.displayMenu.addAction(self.closeDisplayTabAct)
        self.windowMenu.addSeparator()

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
        self.toolsMenu.aboutToShow.connect(self.populateToolsMenu)

        ###  HELP MENU  ###
        self.helpMenu = self.menubar.addMenu('&Help')
        self.helpMenu.addAction(self.emulatorAct)
        self.helpMenu.addSeparator()
        self.helpMenu.addAction(self.githubAct)
        self.helpMenu.addAction(self.aboutAct)

    def _checkEnvironment(self):
        if not os.path.exists(self.formatPath):
            os.mkdir(self.formatPath)
        if not os.path.exists(self.dataPath):
            os.mkdir(self.dataPath)
        if not os.path.exists(self.backupPath):
            os.mkdir(self.backupPath)
        if not os.path.exists(self.presetPath):
            os.mkdir(self.presetPath)
        if not os.path.exists(self.autosavePath):
            os.mkdir(self.autosavePath)
        if not os.path.exists(self.examplesPath):
            os.mkdir(self.examplesPath)

    def _center(self):
        frameGeometry = self.frameGeometry()
        screenCenter = QDesktopWidget().availableGeometry().center()
        frameGeometry.moveCenter(screenCenter)
        self.move(frameGeometry.topLeft())

    def _initializeDisplayLayout(self):
        currentLayout = self.settings['CURRENT_LAYOUT']
        if currentLayout != '':
            path = os.path.join(self.presetPath, f"{currentLayout}.json")
            self.loadLayout(path, warning=False)

    def newFormatTab(self):
        self.newFormatWindow = NewPackageWindow()
        self.newFormatWindow.buttons.accepted.connect(self.acceptNewFormatTab)
        self.newFormatWindow.buttons.rejected.connect(self.newFormatWindow.close)
        self.newFormatWindow.show()

    def acceptNewFormatTab(self):
        name = self.newFormatWindow.nameEdit.text()
        self.packetTabWidget.newFormat(name)
        self.newFormatWindow.close()

    def openFormatTab(self):
        if os.path.exists(self.formatPath):
            path = QFileDialog.getExistingDirectory(self, "Select Directory", self.formatPath)
        else:
            path = QFileDialog.getExistingDirectory(self, "Select Directory")
        if os.path.abspath(path) not in [os.path.abspath(self.formatPath), os.path.abspath(self.currentDir)]:
            self.packetTabWidget.openFormat(path)
            self.addToRecent(path)
        self.populateFileMenu()

    def addToRecent(self, path):
        self.settings['OPENED_RECENTLY'].insert(0, path)
        openedRecently = []
        for i in range(len(self.settings['OPENED_RECENTLY'])):
            if self.settings['OPENED_RECENTLY'][i] not in openedRecently:
                openedRecently.append(self.settings['OPENED_RECENTLY'][i])
        self.settings['OPENED_RECENTLY'] = openedRecently
        if len(self.settings['OPENED_RECENTLY']) == 5:
            self.settings['OPENED_RECENTLY'].pop()
        saveSettings(self.settings, 'settings')

    def openRecentFile(self, filename):
        filenames = [os.path.basename(path) for path in self.settings['OPENED_RECENTLY']]
        path = self.settings['OPENED_RECENTLY'][filenames.index(filename)]
        if os.path.exists(path):
            self.packetTabWidget.openFormat(path)
            self.addToRecent(path)
        self.populateFileMenu()

    def saveFormatTab(self):
        self.packetTabWidget.saveFormat()
        self.graphsTabWidget.fillComboBox()
        self.populateFileMenu()

    def saveAsFormatTab(self):
        # Create Lines
        path = QFileDialog.getSaveFileName(self, 'Save File')
        self.packetTabWidget.saveFormat(path[0])
        self.graphsTabWidget.fillComboBox()
        self.populateFileMenu()

    def saveAllFormatTab(self):
        self.packetTabWidget.saveAllFormats()
        self.populateFileMenu()

    def closeFormatTab(self):
        self.packetTabWidget.closeFormat()
        self.populateFileMenu()

    def openTrackedFormats(self):
        self.trackedFormatsWindow = TrackedBalloonsWindow(self.currentDir)
        self.trackedFormatsWindow.buttons.accepted.connect(self.editTrackedFormats)
        self.trackedFormatsWindow.buttons.rejected.connect(self.trackedFormatsWindow.close)
        self.trackedFormatsWindow.show()

    def editTrackedFormats(self):
        trackedFormats = self.trackedFormatsWindow.getListedValues()
        self.settings['FORMAT_FILES'] = trackedFormats
        saveSettings(self.settings, 'settings')
        self.trackedFormatsWindow.close()
        self.graphsTabWidget.fillComboBox()

    def openLayoutManager(self):
        description = self.displayTabWidget.getLayoutDescription()
        self.layoutPresetWindow = LayoutManagerDialog(self.currentDir, description, currentLayout=self.settings['CURRENT_LAYOUT'])
        self.layoutPresetWindow.loadSignal.connect(self.loadLayout)
        self.layoutPresetWindow.exec_()
        self.layoutPresetWindow = None

    def loadLayout(self, filePath: str, warning=True):
        with open(filePath, "r") as file:
            description = json.load(file)
        self.displayTabWidget.applyLayoutDescription(description)
        self.settings['CURRENT_LAYOUT'] = os.path.splitext(os.path.basename(filePath))[0]
        saveSettings(self.settings, 'settings')

    def saveLayout(self, autosave=False):
        # SAVING LAYOUT PRESET
        displayedLayout = self.displayTabWidget.getLayoutDescription()
        currentLayout = self.settings['CURRENT_LAYOUT']
        # AUTOMATIC AUTOSAVE WITHOUT ANY CURRENT LAYOUT
        if autosave:
            current_datetime = datetime.now()
            timestamp = current_datetime.strftime("%Y-%m-%d_%H-%M-%S")
            filename = os.path.join(self.autosavePath, f"autosave_{timestamp}.json")
            autoItems = os.listdir(self.autosavePath)
            autoSaves = [item for item in autoItems if os.path.isfile(os.path.join(self.autosavePath, item))]
            # REMOVING OLD AUTOSAVES
            overflow = len(autoSaves) - int(self.settings['MAXIMUM_AUTOSAVES'])
            if overflow > 0:
                for i in range(overflow):
                    fileToDelete = os.path.join(self.autosavePath, autoSaves[i])
                    os.remove(fileToDelete)
            with open(filename, "w") as file:
                json.dump(displayedLayout, file)
        # MANUAL SAVE WITH SAVE AS
        elif not autosave and currentLayout == '':
            self.saveLayoutAs()
        # MANUAL SAVE INTO CURRENTLY LOADED SAVE
        else:
            filename = os.path.join(self.presetPath, f"{currentLayout}.json")
            with open(filename, "w") as file:
                json.dump(displayedLayout, file)

    def saveLayoutAs(self):
        layoutDescription = self.displayTabWidget.getLayoutDescription()
        # EXISTING USER SAVES' NAMES
        userItems = os.listdir(self.presetPath)
        userSaves = [os.path.splitext(item)[0] for item in userItems if os.path.isfile(os.path.join(self.presetPath, item))]
        # NEW NAME DIALOG
        inputDialog = StringInputDialog('Save Layout As', 'Enter Layout Name', exclusives=userSaves)
        result = inputDialog.exec_()
        if result == QDialog.Accepted:
            name = inputDialog.getStringInput()
            self.settings['CURRENT_LAYOUT'] = name
            filename = os.path.join(self.presetPath, f"{self.settings['CURRENT_LAYOUT']}.json")
            with open(filename, "w") as file:
                json.dump(layoutDescription, file)
        self.populateLayoutMenu()

    def importLayout(self):
        filePath, _ = QFileDialog.getOpenFileName(None, "Select JSON layout file", "", "JSON Files (*.json)")
        if filePath:
            try:
                with open(filePath, 'r') as file:
                    layoutDescription = json.load(file)
                testDisplay = DisplayTabWidget(self.currentDir)
                testDisplay.applyLayoutDescription(layoutDescription)
                # Move File to User Saves
                shutil.copy(filePath, self.presetPath)
                # Ask for Loading
                choice = QMessageBox.question(None, "Load Layout", "Do you want to load this layout?",
                                              QMessageBox.Yes | QMessageBox.No)
                if choice == QMessageBox.Yes:
                    self.loadLayout(filePath)
                    self.settings['CURRENT_LAYOUT'] = os.path.basename(filePath)

            except Exception:
                errorDialog = QMessageBox()
                errorDialog.setIcon(QMessageBox.Warning)
                errorDialog.setWindowTitle("Error")
                errorDialog.setText("An error occurred while processing the file.")
                errorDialog.setStandardButtons(QMessageBox.Retry | QMessageBox.Cancel)
                errorDialog.setDefaultButton(QMessageBox.Retry)
                errorDialog.exec_()
                if errorDialog.Retry:
                    self.importLayout()

    def exportLayoutJSON(self):
        layout = self.displayTabWidget.getLayoutDescription()
        filePath, _ = QFileDialog.getSaveFileName(None, "Export as JSON file", "", "JSON Files (*.json)")
        if filePath:
            with open(filePath, 'w') as file:
                json.dump(layout, file)

    def restoreLayout(self):
        dialog = QDialog()
        dialog.setWindowTitle("Confirmation")
        layout = QVBoxLayout()
        label = QLabel("All previous changes will be erased. Do you want to proceed?")
        layout.addWidget(label)
        button_box = QDialogButtonBox(QDialogButtonBox.Yes | QDialogButtonBox.No)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        dialog.setLayout(layout)
        dialog.exec_()
        if dialog.Accepted:
            self.displayTabWidget.closeAllTabs()
            path = os.path.join(self.presetPath, f"{self.settings['CURRENT_LAYOUT']}.json")
            self.loadLayout(path)

    def startupAutosave(self):
        self.layoutAutosaveTimer = QTimer()
        self.layoutAutosaveTimer.timeout.connect(lambda: self.saveLayout(autosave=True))
        self.layoutAutosaveTimer.start(int(self.settings['INTERVAL_AUTOSAVE']) * 1000)

    def setLayoutAutoSave(self, action):
        self.settings["LAYOUT_AUTOSAVE"] = action
        saveSettings(self.settings, "settings")
        if self.settings["LAYOUT_AUTOSAVE"]:
            self.layoutAutosaveTimer = QTimer()
            self.layoutAutosaveTimer.timeout.connect(lambda: self.saveLayout(autosave=True))
            self.layoutAutosaveTimer.start(120)
        else:
            self.layoutAutosaveTimer.stop()

    def populateLayoutMenu(self):
        layoutDescription = self.displayTabWidget.getLayoutDescription()
        if self.settings['CURRENT_LAYOUT'] == '':
            self.restoreLayoutAct.setDisabled(True)
            if layoutDescription:
                self.saveLayoutAct.setDisabled(False)
                self.exportLayoutAct.setDisabled(False)
            else:
                self.saveLayoutAct.setDisabled(True)
                self.exportLayoutAct.setDisabled(True)
        else:
            filename = os.path.join(self.presetPath, f"{self.settings['CURRENT_LAYOUT']}.json")
            self.exportLayoutAct.setDisabled(False)
            with open(filename, "r") as file:
                previousState = json.load(file)
            if layoutDescription == previousState:
                self.saveLayoutAct.setDisabled(True)
                self.restoreLayoutAct.setDisabled(True)
            else:
                self.saveLayoutAct.setDisabled(False)
                self.restoreLayoutAct.setDisabled(False)

    def importFormat(self):
        path = QFileDialog.getOpenFileName(self, 'Import Packet Format')
        # TODO : Verifying if chosen file is a format
        pass

    def startSerial(self):
        if not self.settings['EMULATOR_MODE']:
            message = "Port : " + self.settings["SELECTED_PORT"] + "  Baud : "
            message += self.settings["SELECTED_BAUD"] + "\nDo you wish to continue ?"
            msg = MessageBox()
            msg.setWindowIcon(self.mainIcon)
            msg.setWindowTitle("Running Warning")
            msg.setText(message)
            msg.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)
            msg.setStyleSheet("QLabel{min-width: 200px;}")
            msg.exec_()
            button = msg.clickedButton()
            sb = msg.standardButton(button)
        else:
            message = "Starting Emulator Mode"
            message += "\nDo you wish to continue ?"
            msg = MessageBox()
            msg.setWindowIcon(self.mainIcon)
            msg.setWindowTitle("Running Warning")
            msg.setText(message)
            msg.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)
            msg.setStyleSheet("QLabel{min-width: 200px;}")
            msg.exec_()
            button = msg.clickedButton()
            sb = msg.standardButton(button)
        if sb == QMessageBox.Yes:
            serialPath = os.path.join(self.currentDir, "sources/SerialGS.py")
            if os.path.exists(serialPath):
                self.serial = SerialMonitor(self.currentDir)
                self.serialWindow.textedit.setDisabled(False)
                self.serial.output.connect(self.onSerialOutput)
                self.serial.progress.connect(self.newSerialData)
                self.serial.start()
            else:
                cancelling = MessageBox()
                cancelling.setWindowIcon(self.mainIcon)
                cancelling.setWindowTitle("Error")
                cancelling.setText("Serial.py not found.")
                cancelling.setStandardButtons(QMessageBox.Ok)
                cancelling.setStyleSheet("QLabel{min-width: 200px;}")
                cancelling.exec_()
        self.populateToolsMenu()

    def stopSerial(self):
        if self.serial is not None:
            self.serial.interrupt()
            self.serial = None
            time.sleep(0.5)
            self.serialWindow.textedit.setDisabled(True)
        self.populateToolsMenu()

    def newSerialData(self, content):
        self.displayTabWidget.updateTabDisplays(content)

    def onSerialOutput(self, newLine):
        needScrolling = False
        value = self.serialWindow.textedit.verticalScrollBar().maximum()
        if self.serialWindow.textedit.verticalScrollBar().value() == value:
            needScrolling = True
        self.serialWindow.textedit.append(newLine + '\n')
        if bool(self.settings["AUTOSCROLL"]) and needScrolling:
            value = self.serialWindow.textedit.verticalScrollBar().maximum()
            self.serialWindow.textedit.verticalScrollBar().setValue(value)

    def dataCaptureUpdated(self, content):
        self.graphsTabWidget.updateTabGraphs(content)

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
        saveSettings(self.settings, "settings")

    def setEmulatorMode(self, action):
        if action:
            message = "Entering Emulator Mode.\nDo you wish to proceed ?"
            msg = MessageBox()
            msg.setWindowIcon(self.mainIcon)
            msg.setWindowTitle("Emulator Mode Warning")
            msg.setText(message)
            msg.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)
            msg.setStyleSheet("QLabel{min-width: 200px;}")
            msg.exec_()
            button = msg.clickedButton()
            sb = msg.standardButton(button)
            if sb == QMessageBox.Yes:
                self.settings["EMULATOR_MODE"] = action
                saveSettings(self.settings, "settings")
                if self.serial is not None:
                    self.stopSerial()
        else:
            self.settings["EMULATOR_MODE"] = action
            saveSettings(self.settings, "settings")
            if self.serial is not None:
                self.stopSerial()

    def populateFileMenu(self):
        # OPENED RECENTLY MENU
        if len(self.settings['OPENED_RECENTLY']) == 0:
            self.recentMenu.setDisabled(True)
        else:
            self.recentMenu.setDisabled(False)
        index = self.packetTabWidget.databasesTabWidget.currentIndex()
        anyDatabaseChanges = False
        currentDatabaseChanges = False
        for i, database in enumerate(self.packetTabWidget.databases.values()):
            referenceDatabase = BalloonPackageDatabase(database.path)
            if referenceDatabase != database:
                anyDatabaseChanges = True
                if i == index:
                    currentDatabaseChanges = True
                if i >= index:
                    break

        # SAVE AND CLOSE ACTIONS
        if not self.packetTabWidget.databases:
            self.saveFormatAction.setDisabled(True)
            self.saveAllFormatAction.setDisabled(True)
            self.saveAsFormatAction.setDisabled(True)
            self.closeFormatAction.setDisabled(True)

        else:
            # Enabled if any changes done on currently edited database
            self.saveFormatAction.setDisabled(not currentDatabaseChanges)
            self.saveAsFormatAction.setDisabled(not currentDatabaseChanges)
            # Enabled if any changes done to any database
            self.saveAllFormatAction.setDisabled(not anyDatabaseChanges)
            # Others
            self.closeFormatAction.setDisabled(False)

    def populateRecentMenu(self):
        self.recentMenu.clear()
        actions = []
        filenames = [os.path.basename(path) for path in self.settings['OPENED_RECENTLY']]
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
            saveSettings(self.settings, "settings")
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
                saveSettings(self.settings, "settings")
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
        saveSettings(self.settings, "settings")
        # Restart Serial Connection if on
        if self.serial is not None:
            self.stopSerial()
            self.startSerial()

    def selectPort(self, action):
        self.portMenu.setTitle('&Port    ' + action.text())
        self.settings["SELECTED_PORT"] = action.text()
        saveSettings(self.settings, "settings")
        if self.serial is not None:
            self.stopSerial()
            self.startSerial()

    def setRssi(self, action):
        self.settings["RSSI"] = action
        saveSettings(self.settings, "settings")
        if self.serial is not None:
            self.stopSerial()
            self.startSerial()

    def checkSerialMonitor(self):
        self.settings = loadSettings("settings")
        if self.serial is not None and not self.serial.isRunning():
            self.stopSerial()
            self.serialWindow.textedit.setDisabled(True)

    def getWeatherForGeolocation(self):
        self.weatherTabWidget.forecastTabDisplay.getGpsLocation()

    def updateWeatherTabs(self):
        self.weatherTabWidget.forecastTabDisplay.updateTabs()

    def onLocationSearchedClicked(self):
        formattedCityName = self.locationSearchBar.selection
        dataSlice = self.weatherTabWidget.forecastTabDisplay.citiesDataFrame[self.weatherTabWidget.forecastTabDisplay.citiesDataFrame['format'] == formattedCityName]
        self.weatherTabWidget.forecastTabDisplay.addLocationTab(dataSlice.iloc[0])

    def updateStatus(self):
        self.datetime = QDateTime.currentDateTime()
        formattedDate = self.datetime.toString('dd.MM.yyyy  hh:mm:ss')
        self.dateLabel.setText(formattedDate)
        now = time.perf_counter()
        fps = 1000 / (now - self.lastUpdate)
        self.lastUpdate = now
        self.avgFps = self.avgFps * 0.8 + fps * 0.2
        self.fpsLabel.setText('Fps : %0.2f ' % self.avgFps)

    @staticmethod
    def openGithub():
        import webbrowser
        webbrowser.open("https://github.com/EnguerranVidal/PyStrato")

    @staticmethod
    def openAbout():
        dialog = AboutDialog()
        dialog.exec_()

    def closeEvent(self, event):
        reply = QMessageBox.question(self, 'Message', "Are you sure to quit?", QMessageBox.Yes |
                                     QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.stopSerial()
            time.sleep(0.5)
            self.serialMonitorTimer.stop()
            for window in QApplication.topLevelWidgets():
                window.close()
            event.accept()
        else:
            event.ignore()


class LoadingSplashScreen(QSplashScreen):
    workerFinished = pyqtSignal(dict)

    def __init__(self, imagePath, currentDir):
        application = QApplication.instance()
        super().__init__(QPixmap(imagePath))
        self.currentDir = currentDir

        # PROGRESS BAR
        self.progressBar = QProgressBar(self)
        self.goal, self.currentValue, self.maximumValue = 0, 0, 200
        self.progressBar.setStyleSheet("QProgressBar::chunk { background-color: teal; }")
        self.progressBar.setTextVisible(False)
        self.progressBar.setGeometry(10, self.size().height() - 60, self.size().width() - 20, 20)
        self.progressBar.setFixedHeight(10)
        self.progressBar.setValue(0)
        self.progressBar.setMaximum(self.maximumValue)
        self.progressTimer = QTimer(self)
        self.progressTimer.timeout.connect(self.updateProgress)
        self.progressTimer.start(5)

        # ADVANCEMENT LABEL
        self.advancementLabel = QLabel(self)
        self.advancementLabel.setText("Progress:")
        paletteAdvancement = self.advancementLabel.palette()
        paletteAdvancement.setColor(QPalette.WindowText, Qt.white)
        self.advancementLabel.setPalette(paletteAdvancement)
        self.advancementLabel.setAlignment(Qt.AlignCenter)
        self.advancementLabel.setGeometry(10, self.size().height() - 100, self.size().width() - 20, 20)
        application.processEvents()

        # WORKER THREAD
        self.worker = LoadingTasksWorker(self.currentDir)
        self.worker.progress.connect(self.handleWorkerProgress)
        self.worker.finished.connect(self.handleWorkerFinished)
        self.workerThread = QThread()
        self.worker.moveToThread(self.workerThread)
        self.workerThread.started.connect(self.worker.loadingTasks)
        self.workerThread.start()

    def updateProgress(self):
        if self.currentValue < self.goal:
            self.currentValue += 1
            self.progressBar.setValue(self.currentValue)

    def handleWorkerProgress(self, progressTuple):
        self.goal = int(progressTuple[0] / 100 * self.maximumValue)
        self.advancementLabel.setText(progressTuple[1])

    def handleWorkerFinished(self, resultDict):
        self.workerFinished.emit(resultDict)


class LoadingTasksWorker(QObject):
    progress = pyqtSignal(tuple)
    finished = pyqtSignal(dict)

    def __init__(self, currentDirectory):
        super().__init__()
        self.currentDir = currentDirectory

    def loadingTasks(self):
        resultDict = {}
        self.progress.emit((80, 'Loading Cities DataBase'))
        resultDict['CITIES'] = loadSearchItemsFromJson(self.currentDir)
        self.progress.emit((100, 'Loading User Interface'))
        time.sleep(2)
        self.finished.emit(resultDict)