######################## IMPORTS ########################
import shutil
from datetime import datetime
from functools import partial
import qdarktheme

# ------------------- PyQt Modules -------------------- #
from PyQt5.QtCore import QDateTime, QThread

# --------------------- Sources ----------------------- #
from sources.SerialGS import SerialMonitor, saveParserData
from sources.common.utilities.FileHandling import loadSearchItemsFromJson
from sources.common.widgets.Widgets import *

from sources.databases.general import DatabaseTabWidget, DatabaseEditor, NewDatabaseWindow
from sources.databases.units import UnitsEditorWidget
from sources.databases.constants import ConstantEditorWidget
from sources.databases.configurations import ConfigsEditorWidget
from sources.databases.sharedtypes import SharedTypesEditorWidget, EnumEditorWidget, StructureEditorWidget
from sources.databases.telemetries import TelemetryEditorWidget
from sources.databases.telecommands import TelecommandEditorWidget

from sources.displays.general import DisplayTabWidget, DisplayDockWidget
from sources.weather.general import WeatherWindow


######################## CLASSES ########################
class PyStratoGui(QMainWindow):
    def __init__(self, path):
        super().__init__()
        self.currentDir, self.loadingData = path, None
        self.mainIcon = QIcon('sources/icons/PyStrato')
        self.hide()
        # FOLDER PATHS
        self.formatPath = os.path.join(self.currentDir, "parsers")
        self.dataPath = os.path.join(self.currentDir, "data")
        self.savesPath = os.path.join(self.dataPath, 'saves')
        self.backupPath = os.path.join(self.dataPath, "_backups")
        self.presetPath = os.path.join(self.dataPath, '_presets')
        self.autosavePath = os.path.join(self.presetPath, 'autosaves')
        self.examplesPath = os.path.join(self.presetPath, 'examples')

        # Main Window Settings
        self.setGeometry(200, 200, 1000, 500)
        self.setWindowTitle('PyStrato')
        self.setWindowIcon(self.mainIcon)
        self.settings = loadSettings("settings")
        # Theme Setting
        if self.settings['DARK_THEME']:
            qdarktheme.setup_theme('dark', additional_qss="QToolTip {color: black;}")
        else:
            qdarktheme.setup_theme('light')
        self.icons = {}
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
        self._createIcons()
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

    def _createIcons(self):
        theme = 'dark-theme' if self.settings['DARK_THEME'] else 'light-theme'
        iconPath = os.path.join(self.currentDir, f'sources/icons/{theme}')
        self.icons['NEW_WINDOW'] = QIcon(os.path.join(iconPath, 'icons8-new-window-96.png'))
        self.icons['OPEN_IN_BROWSER'] = QIcon(os.path.join(iconPath, 'icons8-open-in-browser-96.png'))
        self.icons['SAVE'] = QIcon(os.path.join(iconPath, 'icons8-save-96.png'))
        self.icons['SAVE_ALL'] = QIcon(os.path.join(iconPath, 'icons8-save-all-96.png'))
        self.icons['CLOSE_WINDOW'] = QIcon(os.path.join(iconPath, 'icons8-close-window-96.png'))
        self.icons['DOWNLOAD'] = QIcon(os.path.join(iconPath, 'icons8-download-96.png'))
        self.icons['ADD_NEW'] = QIcon(os.path.join(iconPath, 'icons8-add-new-96.png'))
        self.icons['NEGATIVE'] = QIcon(os.path.join(iconPath, 'icons8-negative-96.png'))
        self.icons['EDIT'] = QIcon(os.path.join(iconPath, 'icons8-edit-96.png'))
        self.icons['ADD_SUBNODE'] = QIcon(os.path.join(iconPath, 'icons8-add-subnode-96.png'))
        self.icons['DELETE_SUBNODE'] = QIcon(os.path.join(iconPath, 'icons8-delete-subnode-96.png'))
        self.icons['ADD_FOLDER'] = QIcon(os.path.join(iconPath, 'icons8-add-folder-96.png'))
        self.icons['DELETE_FOLDER'] = QIcon(os.path.join(iconPath, 'icons8-delete-folder-96.png'))
        self.icons['FULL_SCREEN'] = QIcon(os.path.join(iconPath, 'icons8-full-screen-96.png'))
        self.icons['FOUR_SQUARES'] = QIcon(os.path.join(iconPath, 'icons8-four-squares-96.png'))
        self.icons['COMBO_CHART'] = QIcon(os.path.join(iconPath, 'icons8-combo-chart-96.png'))
        self.icons['PLAY'] = QIcon(os.path.join(iconPath, 'icons8-play-96.png'))
        self.icons['STOP'] = QIcon(os.path.join(iconPath, 'icons8-stop-96.png'))
        self.icons['MONITOR'] = QIcon(os.path.join(iconPath, 'icons8-monitor-96.png'))
        self.icons['RESET'] = QIcon(os.path.join(iconPath, 'icons8-reset-96.png'))
        self.icons['MY_LOCATION'] = QIcon(os.path.join(iconPath, 'icons8-my-location-96.png'))
        self.icons['GITHUB'] = QIcon(os.path.join(iconPath, 'icons8-github-96.png'))
        self.icons['HELP'] = QIcon(os.path.join(iconPath, 'icons8-help-96.png'))

    def _generateTabs(self):
        self.generalTabWidget = QTabWidget(self)
        self.generalTabBar = QTabBar(self.generalTabWidget)
        self.generalTabBar.setStyleSheet("QTabBar::tab { min-height: 125px; max-height: 125px; }")
        self.generalTabWidget.setTabBar(self.generalTabBar)
        self.generalTabWidget.setTabPosition(self.generalTabWidget.West)

        # Packet Tab Widget -----------------------------------------
        self.packetTabWidget = DatabaseTabWidget(self.currentDir)
        self.displayTabWidget = DisplayTabWidget(self.currentDir)
        self.weatherTabWidget = WeatherWindow(self.loadingData, self.currentDir) if self.settings['ENABLE_WEATHER'] else QWidget()
        self.graphWidgetsList = []
        # Show created tabs
        self.packetTabWidget.show()
        self.displayTabWidget.show()
        self.weatherTabWidget.setVisible(self.settings['ENABLE_WEATHER'])
        # Adding Tabs to Main Widget -------------------------------
        self.generalTabWidget.addTab(self.displayTabWidget, 'DISPLAY')
        self.generalTabWidget.addTab(self.packetTabWidget, 'PACKETS')
        if self.settings['ENABLE_WEATHER']:
            self.generalTabWidget.addTab(self.weatherTabWidget, 'WEATHER')

        self.generalTabWidget.currentChanged.connect(self.manageToolBars)
        self.packetTabWidget.tabChanged.connect(self.manageDatabaseToolBars)
        self.packetTabWidget.databaseChanged.connect(self.manageDatabaseEditorChange)
        self.setCentralWidget(self.generalTabWidget)

    def _createToolBars(self):
        ########### DATABASES ###########
        self.databasesToolBar = QToolBar('Database', self)
        self.databasesToolBar.addAction(self.newParserAction)
        self.databasesToolBar.addAction(self.openParserAction)
        self.databasesToolBar.addAction(self.saveParserAction)
        self.databasesToolBar.addSeparator()

        ########### DISPLAYS ###########
        self.displaysToolBar = QToolBar('Display', self)
        self.displaysToolBar.addAction(self.newDisplayTabAct)
        self.displaysToolBar.addAction(self.closeDisplayTabAct)
        self.displaysToolBar.addSeparator()
        # INDICATORS
        indicatorToolButton = QToolButton()
        indicatorToolButton.setDefaultAction(self.newSimpleIndicatorAct)
        indicatorSubMenu = QMenu()
        indicatorSubMenu.addAction(self.newSimpleIndicatorAct)
        indicatorSubMenu.addAction(self.newGridIndicatorAct)
        indicatorToolButton.setMenu(indicatorSubMenu)
        self.displaysToolBar.addWidget(indicatorToolButton)
        # GRAPHS
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
        self.weatherToolBar = QToolBar('Weather', self)
        # SPACER
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.weatherToolBar.addWidget(spacer)
        if self.settings['ENABLE_WEATHER']:
            # GEOLOCATION & DATA UPDATING
            self.weatherToolBar.addAction(self.updatingWeatherAct)
            self.weatherToolBar.addAction(self.getGeolocationAct)
            # SEARCH BAR
            searchOptions = self.weatherTabWidget.citiesDataFrame['format']
            self.locationSearchBar = SearchBar(searchOptions)
            self.locationSearchBar.setFixedWidth(300)
            self.locationSearchBar.setFixedHeight(30)
            self.locationSearchBar.searchDone.connect(self.onLocationSearchedClicked)
            self.weatherToolBar.addWidget(self.locationSearchBar)

        ########### DATABASE PANELS ###########
        # UNIT BAR
        self.unitsToolBar = QToolBar('Units')
        self.unitsToolBar.addAction(self.addUnitAct)
        self.unitsToolBar.addAction(self.removeUnitAct)
        # CONSTANT BAR
        self.constantsToolBar = QToolBar('Constants')
        self.constantsToolBar.addAction(self.addConstantAct)
        self.constantsToolBar.addAction(self.removeConstantAct)
        # CONFIGS BAR
        self.configsToolBar = QToolBar('Configurations')
        self.configsToolBar.addAction(self.addConfigurationAct)
        self.configsToolBar.addAction(self.removeConfigurationAct)
        # SHARED DATA TYPE BAR
        self.sharedDataTypesToolBar = QToolBar('SharedDataTypes')
        self.sharedDataTypesToolBar.addAction(self.addDataTypeAct)
        self.sharedDataTypesToolBar.addAction(self.removeDataTypeAct)
        self.sharedDataTypesToolBar.addAction(self.changeDataTypeAct)
        self.sharedDataTypesToolBar.addSeparator()
        self.sharedDataTypesToolBar.addAction(self.addEnumValueAct)
        self.sharedDataTypesToolBar.addAction(self.removeEnumValueAct)
        # TELEMETRY BAR
        self.telemetriesToolBar = QToolBar('Telemetries')
        self.telemetriesToolBar.addAction(self.addTelemetryAct)
        self.telemetriesToolBar.addAction(self.removeTelemetryAct)
        self.telemetriesToolBar.addAction(self.addTelemetryArgumentAct)
        self.telemetriesToolBar.addAction(self.removeTelemetryArgumentAct)
        # TELECOMMAND BAR
        self.telecommandsToolBar = QToolBar('Telecommands')
        self.telecommandsToolBar.addAction(self.addTelecommandAct)
        self.telecommandsToolBar.addAction(self.removeTelecommandAct)
        self.telecommandsToolBar.addAction(self.addTelecommandArgumentAct)
        self.telecommandsToolBar.addAction(self.removeTelecommandArgumentAct)

        ########### APPEARANCE ###########
        self.addToolBar(self.databasesToolBar)
        self.addToolBar(self.displaysToolBar)
        self.addToolBar(self.weatherToolBar)
        # EDITOR PANELS TOOLBARS
        self.addToolBar(self.unitsToolBar)
        self.addToolBar(self.constantsToolBar)
        self.addToolBar(self.configsToolBar)
        self.addToolBar(self.sharedDataTypesToolBar)
        self.addToolBar(self.telemetriesToolBar)
        self.addToolBar(self.telecommandsToolBar)
        self.generalTabWidget.currentChanged.connect(self.manageToolBars)
        self.manageToolBars(0)

    def manageToolBars(self, index):
        # Show the ToolBar based on the appearing tab
        if index == 0:  # DISPLAYS
            self.databasesToolBar.hide()
            self.displaysToolBar.show()
            self.weatherToolBar.hide()
            self.manageDatabaseToolBars()

        elif index == 1:  # PACKAGES
            self.databasesToolBar.show()
            self.displaysToolBar.hide()
            self.weatherToolBar.hide()
            self.manageDatabaseToolBars()

        elif index == 2:  # WEATHER
            self.databasesToolBar.hide()
            self.displaysToolBar.hide()
            self.weatherToolBar.show()
            self.manageDatabaseToolBars()

    def manageDatabaseToolBars(self):
        editor: DatabaseEditor = self.packetTabWidget.currentWidget()
        if self.generalTabWidget.currentIndex() == 1 and editor is not None:
            editorPanelIndex = editor.currentIndex()
            if editorPanelIndex == 0:
                self.unitsToolBar.show()
                self.constantsToolBar.hide()
                self.configsToolBar.hide()
                self.sharedDataTypesToolBar.hide()
                self.telemetriesToolBar.hide()
                self.telecommandsToolBar.hide()
            elif editorPanelIndex == 1:
                self.unitsToolBar.hide()
                self.constantsToolBar.show()
                self.configsToolBar.hide()
                self.sharedDataTypesToolBar.hide()
                self.telemetriesToolBar.hide()
                self.telecommandsToolBar.hide()
            elif editorPanelIndex == 2:
                self.unitsToolBar.hide()
                self.constantsToolBar.hide()
                self.configsToolBar.show()
                self.sharedDataTypesToolBar.hide()
                self.telemetriesToolBar.hide()
                self.telecommandsToolBar.hide()
            elif editorPanelIndex == 3:
                self.unitsToolBar.hide()
                self.constantsToolBar.hide()
                self.configsToolBar.hide()
                self.sharedDataTypesToolBar.show()
                self.telemetriesToolBar.hide()
                self.telecommandsToolBar.hide()
            elif editorPanelIndex == 4:
                self.unitsToolBar.hide()
                self.constantsToolBar.hide()
                self.configsToolBar.hide()
                self.sharedDataTypesToolBar.hide()
                self.telemetriesToolBar.show()
                self.telecommandsToolBar.hide()
            elif editorPanelIndex == 5:
                self.unitsToolBar.hide()
                self.constantsToolBar.hide()
                self.configsToolBar.hide()
                self.sharedDataTypesToolBar.hide()
                self.telemetriesToolBar.hide()
                self.telecommandsToolBar.show()
            self.manageDatabaseEditorChange()
        else:
            self.unitsToolBar.hide()
            self.constantsToolBar.hide()
            self.configsToolBar.hide()
            self.sharedDataTypesToolBar.hide()
            self.telemetriesToolBar.hide()
            self.telecommandsToolBar.hide()

    def _createActions(self):
        ########### FORMATS ###########
        # New Format
        self.newParserAction = QAction('&New Parser', self)
        self.newParserAction.setStatusTip('Create New Parser')
        self.newParserAction.setIcon(self.icons['NEW_WINDOW'])
        self.newParserAction.setShortcut('Ctrl+N')
        self.newParserAction.triggered.connect(self.newParserTab)
        # Open Format
        self.openParserAction = QAction('&Open', self)
        self.openParserAction.setStatusTip('Open Parser')
        self.openParserAction.setIcon(self.icons['OPEN_IN_BROWSER'])
        self.openParserAction.setShortcut('Ctrl+O')
        self.openParserAction.triggered.connect(self.openParserTab)
        # Save Format
        self.saveParserAction = QAction('&Save', self)
        self.saveParserAction.setStatusTip('Save Parser')
        self.saveParserAction.setIcon(self.icons['SAVE'])
        self.saveParserAction.setShortcut('Ctrl+S')
        self.saveParserAction.triggered.connect(self.saveParserTab)
        # Save As Format
        self.saveAsParserAction = QAction('&Save As', self)
        self.saveAsParserAction.setStatusTip('Save Parser As...')
        self.saveAsParserAction.triggered.connect(self.saveAsParserTab)
        # Save All Formats
        self.saveAllParserAction = QAction('&Save All', self)
        self.saveAllParserAction.setStatusTip('Save All Parsers')
        self.saveAllParserAction.setIcon(self.icons['SAVE_ALL'])
        self.saveAllParserAction.triggered.connect(self.saveAllParserTab)
        # Close Format
        self.closeParserAction = QAction('&Close', self)
        self.closeParserAction.setStatusTip('Close Current Parser')
        self.closeParserAction.setIcon(self.icons['CLOSE_WINDOW'])
        self.closeParserAction.triggered.connect(self.closeParserTab)
        # Import Format
        self.importParserAction = QAction('&Import Parser', self)
        self.importParserAction.setStatusTip('Import Parser')
        self.importParserAction.setIcon(self.icons['DOWNLOAD'])
        self.importParserAction.triggered.connect(self.importFormat)
        # Tracked Formats
        self.trackedParserAction = QAction('&Tracked Parsers', self)
        self.trackedParserAction.setStatusTip('Open Tracked Parsers Selection Window')
        self.trackedParserAction.triggered.connect(self.openTrackedParsers)
        # Exit
        self.exitAct = QAction(QIcon('exit.png'), '&Exit', self)
        self.exitAct.setShortcut('Ctrl+Q')
        self.exitAct.setStatusTip('Exit application')
        self.exitAct.triggered.connect(self.close)

        ########### WINDOW ###########
        # EDITOR PANEL -----------------------------------------------
        # Add Unit
        self.addUnitAct = QAction('&Add Unit', self)
        self.addUnitAct.setIcon(self.icons['ADD_NEW'])
        self.addUnitAct.setStatusTip('Add Database Unit')
        self.addUnitAct.triggered.connect(self.addDatabaseUnit)
        # Remove Unit
        self.removeUnitAct = QAction('&Remove Unit', self)
        self.removeUnitAct.setIcon(self.icons['NEGATIVE'])
        self.removeUnitAct.setStatusTip('Remove Database Unit')
        self.removeUnitAct.triggered.connect(self.removeDatabaseUnit)
        # Add Constant
        self.addConstantAct = QAction('&Add Constant', self)
        self.addConstantAct.setIcon(self.icons['ADD_NEW'])
        self.addConstantAct.setStatusTip('Add Database Constant')
        self.addConstantAct.triggered.connect(self.addDatabaseConstant)
        # Remove Constant
        self.removeConstantAct = QAction('&Remove Constant', self)
        self.removeConstantAct.setIcon(self.icons['NEGATIVE'])
        self.removeConstantAct.setStatusTip('Remove Database Constant')
        self.removeConstantAct.triggered.connect(self.removeDatabaseConstant)
        # Add Configuration
        self.addConfigurationAct = QAction('&Add Configuration', self)
        self.addConfigurationAct.setIcon(self.icons['ADD_NEW'])
        self.addConfigurationAct.setStatusTip('Add Database Configuration')
        self.addConfigurationAct.triggered.connect(self.addDatabaseConfig)
        # Remove Configuration
        self.removeConfigurationAct = QAction('&Remove Configuration', self)
        self.removeConfigurationAct.setIcon(self.icons['NEGATIVE'])
        self.removeConfigurationAct.setStatusTip('Remove Database Configuration')
        self.removeConfigurationAct.triggered.connect(self.removeDatabaseConfig)
        # Add SharedDataType
        self.addDataTypeAct = QAction('&Add Shared DataType', self)
        self.addDataTypeAct.setIcon(self.icons['ADD_NEW'])
        self.addDataTypeAct.setStatusTip('Add Shared DataType')
        self.addDataTypeAct.triggered.connect(self.addSharedTypeElement)
        # Edit SharedDataType
        self.changeDataTypeAct = QAction('&Change Shared DataType', self)
        self.changeDataTypeAct.setIcon(self.icons['EDIT'])
        self.changeDataTypeAct.setStatusTip('Change Shared DataType Category')
        self.changeDataTypeAct.triggered.connect(self.changeSharedTypeElementCategory)
        # Remove SharedDataType
        self.removeDataTypeAct = QAction('&Remove Shared DataType', self)
        self.removeDataTypeAct.setIcon(self.icons['NEGATIVE'])
        self.removeDataTypeAct.setStatusTip('Remove Shared DataType')
        self.removeDataTypeAct.triggered.connect(self.removeSharedTypeElement)
        # Add Telemetry Argument
        self.addEnumValueAct = QAction('&Add Enum Value', self)
        self.addEnumValueAct.setIcon(self.icons['ADD_SUBNODE'])
        self.addEnumValueAct.setStatusTip('Add Enumeration value')
        self.addEnumValueAct.triggered.connect(self.addSharedEnumValue)
        # Remove Telemetry Argument
        self.removeEnumValueAct = QAction('&Remove Enum Value', self)
        self.removeEnumValueAct.setIcon(self.icons['DELETE_SUBNODE'])
        self.removeEnumValueAct.setStatusTip('Remove Enumeration value')
        self.removeEnumValueAct.triggered.connect(self.removeSharedEnumValue)
        # Add Telemetry
        self.addTelemetryAct = QAction('&Add Telemetry', self)
        self.addTelemetryAct.setIcon(self.icons['ADD_NEW'])
        self.addTelemetryAct.setStatusTip('Add Database Telemetry')
        self.addTelemetryAct.triggered.connect(self.addDatabaseTelemetry)
        # Remove Telemetry
        self.removeTelemetryAct = QAction('&Remove Telemetry', self)
        self.removeTelemetryAct.setIcon(self.icons['NEGATIVE'])
        self.removeTelemetryAct.setStatusTip('Remove Database Telemetry')
        self.removeTelemetryAct.triggered.connect(self.removeDatabaseTelemetry)
        # Add Telemetry Argument
        self.addTelemetryArgumentAct = QAction('&Add Telemetry Argument', self)
        self.addTelemetryArgumentAct.setIcon(self.icons['ADD_SUBNODE'])
        self.addTelemetryArgumentAct.setStatusTip('Add Database Telemetry Argument')
        self.addTelemetryArgumentAct.triggered.connect(self.addDatabaseTelemetryArgument)
        # Remove Telemetry Argument
        self.removeTelemetryArgumentAct = QAction('&Remove Telemetry Argument', self)
        self.removeTelemetryArgumentAct.setIcon(self.icons['DELETE_SUBNODE'])
        self.removeTelemetryArgumentAct.setStatusTip('Remove Database Telemetry Argument')
        self.removeTelemetryArgumentAct.triggered.connect(self.removeDatabaseTelemetryArgument)
        # Add Telecommand
        self.addTelecommandAct = QAction('&Add Telecommand', self)
        self.addTelecommandAct.setIcon(self.icons['ADD_NEW'])
        self.addTelecommandAct.setStatusTip('Add Database Telecommand')
        self.addTelecommandAct.triggered.connect(self.addDatabaseTelecommand)
        # Remove Telecommand
        self.removeTelecommandAct = QAction('&Remove Telecommand', self)
        self.removeTelecommandAct.setIcon(self.icons['NEGATIVE'])
        self.removeTelecommandAct.setStatusTip('Remove Database Telecommand')
        self.removeTelecommandAct.triggered.connect(self.removeDatabaseTelecommand)
        # Add Telecommand Argument
        self.addTelecommandArgumentAct = QAction('&Add Telemetry Argument', self)
        self.addTelecommandArgumentAct.setIcon(self.icons['ADD_SUBNODE'])
        self.addTelecommandArgumentAct.setStatusTip('Add Database Telemetry Argument')
        self.addTelecommandArgumentAct.triggered.connect(self.addDatabaseTelecommandArgument)
        # Remove Telecommand Argument
        self.removeTelecommandArgumentAct = QAction('&Remove Telecommand Argument', self)
        self.removeTelecommandArgumentAct.setIcon(self.icons['DELETE_SUBNODE'])
        self.removeTelecommandArgumentAct.setStatusTip('Remove Database Telecommand Argument')
        self.removeTelecommandArgumentAct.triggered.connect(self.removeDatabaseTelecommandArgument)
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
        self.layoutAutoSaveAct = QAction('&AutoSave', self, checkable=True, checked=self.settings["LAYOUT_AUTOSAVE"])
        self.layoutAutoSaveAct.setStatusTip('Toggle Layout Autosave')
        self.layoutAutoSaveAct.triggered.connect(self.setLayoutAutoSave)
        # THEME --------------------------------------------------------
        themeText = 'Light Theme' if self.settings['DARK_THEME'] else 'Dark Theme'
        self.darkModeAct = QAction(f'&{themeText}', self)
        self.darkModeAct.setStatusTip(f' Applying {themeText}')
        self.darkModeAct.triggered.connect(self.toggleDarkMode)

        ########### DISPLAYS ###########
        # Add New Display Tab
        self.newDisplayTabAct = QAction('&New Display Tab', self)
        self.newDisplayTabAct.setIcon(self.icons['ADD_FOLDER'])
        self.newDisplayTabAct.setStatusTip('Create New Display Tab')
        self.newDisplayTabAct.setShortcut('Ctrl+Shift+N')
        self.newDisplayTabAct.triggered.connect(lambda: self.displayTabWidget.addNewTab())
        # Close Display Tab
        self.closeDisplayTabAct = QAction('&Close Display Tab', self)
        self.closeDisplayTabAct.setIcon(self.icons['DELETE_FOLDER'])
        self.closeDisplayTabAct.setStatusTip('Close Display Tab')
        self.closeDisplayTabAct.setShortcut('Ctrl+Shift+X')
        self.closeDisplayTabAct.triggered.connect(self.displayTabWidget.closeCurrentTab)
        # Add Simple Indicator
        self.newSimpleIndicatorAct = QAction('&Simple Indicator', self)
        self.newSimpleIndicatorAct.setIcon(self.icons['FULL_SCREEN'])
        self.newSimpleIndicatorAct.setStatusTip('Add New Simple Indicator')
        self.newSimpleIndicatorAct.triggered.connect(self.displayTabWidget.addSimpleIndicator)
        # Add Grid Indicator
        self.newGridIndicatorAct = QAction('&Grid Indicator', self)
        self.newGridIndicatorAct.setIcon(self.icons['FOUR_SQUARES'])
        self.newGridIndicatorAct.setStatusTip('Add New Grid Simple Indicator')
        self.newGridIndicatorAct.triggered.connect(self.displayTabWidget.addGridIndicator)
        # Add MultiCurve Graph
        self.newMultiCurveAct = QAction('&MultiCurve Graph', self)
        self.newMultiCurveAct.setIcon(self.icons['COMBO_CHART'])
        self.newMultiCurveAct.setStatusTip('Add New MultiCurve Graph')
        self.newMultiCurveAct.triggered.connect(self.displayTabWidget.addMultiCurveGraph)

        ########### TOOLS ###########
        # Run Serial
        self.runSerialAct = QAction('&Run', self)
        self.runSerialAct.setShortcut('Ctrl+R')
        self.runSerialAct.setIcon(self.icons['PLAY'])
        self.runSerialAct.setStatusTip('Run Serial Monitoring')
        self.runSerialAct.triggered.connect(self.startSerial)
        # Stop Serial
        self.stopSerialAct = QAction('&Stop', self)
        self.stopSerialAct.setIcon(self.icons['STOP'])
        self.stopSerialAct.setStatusTip('Stop Serial Monitoring')
        self.stopSerialAct.triggered.connect(self.stopSerial)
        # Opening Serial Monitor
        self.openMonitorAct = QAction('&Open Serial Monitor', self)
        self.openMonitorAct.setShortcut('Ctrl+M')
        self.openMonitorAct.setIcon(self.icons['MONITOR'])
        self.openMonitorAct.setStatusTip('Open Serial Monitor')
        self.openMonitorAct.triggered.connect(self.openSerialMonitor)

        ########### WEATHER ###########
        # Updating Weather Tabs
        self.updatingWeatherAct = QAction('&Update Weather Data', self)
        self.updatingWeatherAct.setIcon(self.icons['RESET'])
        self.updatingWeatherAct.setStatusTip('Updating All Weather Tabs')
        self.updatingWeatherAct.triggered.connect(self.updateWeatherTabs)
        # Using Geolocation
        self.getGeolocationAct = QAction('&Get GeoLocation Weather', self)
        self.getGeolocationAct.setIcon(self.icons['MY_LOCATION'])
        self.getGeolocationAct.setStatusTip('Get Weather From Geolocation')
        self.getGeolocationAct.triggered.connect(self.getWeatherForGeolocation)

        ########### HELP ###########
        # Set Saving Parser Content
        self.savingParserContentAct = QAction('&Save Parser Content', self, checkable=True, checked=self.settings["SAVING_SERIAL_CONTENT"])
        self.savingParserContentAct.setStatusTip('Toggle Parser Content Saving')
        self.savingParserContentAct.triggered.connect(self.setParserContentSaving)
        # Toggle Emulator Mode
        self.emulatorAct = QAction('&Emulator Mode', self, checkable=True, checked=self.settings["EMULATOR_MODE"])
        self.emulatorAct.setStatusTip("Toggle Emulator mode")
        self.emulatorAct.triggered.connect(self.setEmulatorMode)
        # Visit GitHub Page
        self.githubAct = QAction('&Visit GitHub', self)
        self.githubAct.setIcon(self.icons['GITHUB'])
        self.githubAct.setStatusTip('Visit GitHub Page')
        self.githubAct.triggered.connect(self.openGithub)
        # Open About Page
        self.aboutAct = QAction('&About', self)
        self.aboutAct.setIcon(self.icons['HELP'])
        self.aboutAct.setStatusTip('About This Software')
        self.aboutAct.triggered.connect(self.openAbout)

    def _createMenuBar(self):
        self.menubar = self.menuBar()

        ###  FILE MENU  ###
        self.fileMenu = self.menubar.addMenu('&File')
        self.fileMenu.addAction(self.newParserAction)
        self.fileMenu.addAction(self.openParserAction)
        self.recentMenu = QMenu('&Recent', self)
        self.recentMenu.aboutToShow.connect(self.populateRecentMenu)

        self.fileMenu.addMenu(self.recentMenu)
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.saveParserAction)
        self.fileMenu.addAction(self.saveAsParserAction)
        self.fileMenu.addAction(self.saveAllParserAction)
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.closeParserAction)
        self.fileMenu.addSeparator()
        self.manageFormatsMenu = QMenu('&Manage Formats', self)
        self.manageFormatsMenu.addAction(self.importParserAction)
        self.manageFormatsMenu.addAction(self.trackedParserAction)
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
        # Layout Menu
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
        # Display Tab Menu
        self.displayMenu = QMenu('&Display Tabs')
        self.displayMenu.addAction(self.newDisplayTabAct)
        self.displayMenu.addAction(self.closeDisplayTabAct)
        self.windowMenu.addMenu(self.displayMenu)
        # Editor Panel Menu
        self.editorTabMenu = QMenu('&Editor Tabs')
        self.unitEditorMenu = QMenu('&Units')
        self.unitEditorMenu.addAction(self.addUnitAct)
        self.unitEditorMenu.addAction(self.removeUnitAct)
        self.constantEditorMenu = QMenu('Constants')
        self.constantEditorMenu.addAction(self.addConstantAct)
        self.constantEditorMenu.addAction(self.removeConstantAct)
        self.configEditorMenu = QMenu('Configurations')
        self.configEditorMenu.addAction(self.addConfigurationAct)
        self.configEditorMenu.addAction(self.removeConfigurationAct)
        self.sharedTypesEditorMenu = QMenu('Shared Data Types')
        self.sharedTypesEditorMenu.addAction(self.addDataTypeAct)
        self.sharedTypesEditorMenu.addAction(self.removeDataTypeAct)
        self.sharedTypesEditorMenu.addAction(self.changeDataTypeAct)
        self.sharedTypesEditorMenu.addSeparator()
        self.sharedTypesEditorMenu.addAction(self.addEnumValueAct)
        self.sharedTypesEditorMenu.addAction(self.removeEnumValueAct)
        self.telemetriesEditorMenu = QMenu('&Telemetries')
        self.telemetriesEditorMenu.addAction(self.addTelemetryAct)
        self.telemetriesEditorMenu.addAction(self.removeTelemetryAct)
        self.telemetriesEditorMenu.addAction(self.addTelemetryArgumentAct)
        self.telemetriesEditorMenu.addAction(self.removeTelemetryArgumentAct)
        self.telecommandsEditorMenu = QMenu('&Telecommands')
        self.telecommandsEditorMenu.addAction(self.addTelecommandAct)
        self.telecommandsEditorMenu.addAction(self.removeTelecommandAct)
        self.telecommandsEditorMenu.addAction(self.addTelecommandArgumentAct)
        self.telecommandsEditorMenu.addAction(self.removeTelecommandArgumentAct)
        self.editorTabMenu.addMenu(self.unitEditorMenu)
        self.editorTabMenu.addMenu(self.constantEditorMenu)
        self.editorTabMenu.addMenu(self.configEditorMenu)
        self.editorTabMenu.addMenu(self.sharedTypesEditorMenu)
        self.editorTabMenu.addMenu(self.telemetriesEditorMenu)
        self.editorTabMenu.addMenu(self.telecommandsEditorMenu)
        self.windowMenu.addMenu(self.editorTabMenu)
        # Theme
        self.windowMenu.addSeparator()
        self.windowMenu.addAction(self.darkModeAct)

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
        self.helpMenu.addAction(self.savingParserContentAct)
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

    def newParserTab(self):
        fullPaths = [os.path.join(self.formatPath, entry) for entry in os.listdir(self.formatPath)]
        databases = [os.path.basename(directory) for directory in fullPaths if os.path.isdir(directory)]
        dialog = NewDatabaseWindow(databases=databases)
        result = dialog.exec_()
        if result == QDialog.Accepted:
            name = self.newFormatWindow.nameLineEdit.text()
            self.packetTabWidget.newParser(name)

    def openParserTab(self):
        if os.path.exists(self.formatPath):
            path = QFileDialog.getExistingDirectory(self, "Select Directory", self.formatPath)
        else:
            path = QFileDialog.getExistingDirectory(self, "Select Directory")
        if os.path.abspath(path) not in [os.path.abspath(self.formatPath), os.path.abspath(self.currentDir)]:
            self.packetTabWidget.openParser(path)
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

    def openRecentParser(self, filename):
        filenames = [os.path.basename(path) for path in self.settings['OPENED_RECENTLY']]
        path = self.settings['OPENED_RECENTLY'][filenames.index(filename)]
        if os.path.exists(path):
            self.packetTabWidget.openParser(path)
            self.addToRecent(path)
        self.populateFileMenu()

    def saveParserTab(self):
        self.packetTabWidget.saveParser()
        self.graphsTabWidget.fillComboBox()
        self.populateFileMenu()

    def saveAsParserTab(self):
        path = QFileDialog.getSaveFileName(self, 'Save File')
        self.packetTabWidget.saveParser(path[0])
        self.graphsTabWidget.fillComboBox()
        self.populateFileMenu()

    def saveAllParserTab(self):
        self.packetTabWidget.saveAllParsers()
        self.populateFileMenu()

    def closeParserTab(self):
        self.packetTabWidget.closeParser()
        self.populateFileMenu()

    def openTrackedParsers(self):
        dialog = TrackedBalloonsWindow(self.currentDir)
        result = dialog.exec_()
        if result == QDialog.Accepted:
            trackedFormats = dialog.getListedValues()
            self.settings['FORMAT_FILES'] = trackedFormats
            saveSettings(self.settings, 'settings')

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
                shutil.copy(filePath, self.presetPath)
                choice = QMessageBox.question(None, "Load Layout", "Do you want to load this layout?", QMessageBox.Yes | QMessageBox.No)
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
        if self.settings['SAVING_SERIAL_CONTENT']:
            parserName, telemetryName, parserData = content['parser'], content['type'], content['data']
            saveParserData(parserName, telemetryName, parserData, self.dataPath)

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

    def setParserContentSaving(self, action):
        self.settings["SAVING_SERIAL_CONTENT"] = action
        saveSettings(self.settings, "settings")

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

        index = self.packetTabWidget.currentIndex()
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
        self.packetTabWidget.unsavedChanges = anyDatabaseChanges
        # SAVE AND CLOSE ACTIONS
        if not self.packetTabWidget.databases:
            self.saveParserAction.setDisabled(True)
            self.saveAllParserAction.setDisabled(True)
            self.saveAsParserAction.setDisabled(True)
            self.closeParserAction.setDisabled(True)

        else:
            self.saveParserAction.setDisabled(not currentDatabaseChanges)
            self.saveAsParserAction.setDisabled(not currentDatabaseChanges)
            self.saveAllParserAction.setDisabled(not anyDatabaseChanges)
            self.closeParserAction.setDisabled(False)

    def populateRecentMenu(self):
        self.recentMenu.clear()
        actions = []
        filenames = [os.path.basename(path) for path in self.settings['OPENED_RECENTLY']]
        for filename in filenames:
            action = QAction(filename, self)
            action.triggered.connect(partial(self.openRecentParser, filename))
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

    def manageDatabaseEditorChange(self):
        editor: DatabaseEditor = self.packetTabWidget.currentWidget()
        if self.generalTabWidget.currentIndex() == 1 and editor is not None:
            isEditorTelemetryArgumentOpen = editor.telemetriesTab.telemetryArgumentsTable.isVisible()
            isEditorTelecommandArgumentOpen = editor.telecommandsTab.telecommandArgumentsTable.isVisible()
            editorPanelIndex = editor.currentIndex()
            selectedUnits = editor.unitsTab.unitsTable.selectedItems()
            self.removeUnitAct.setDisabled(not len(selectedUnits) > 0 or editorPanelIndex != 0)
            selectedConstants = editor.constantsTab.constantsTable.selectedItems()
            self.removeConstantAct.setDisabled(not len(selectedConstants) > 0 or editorPanelIndex != 1)
            selectedConfigs = editor.configsTab.configsTable.selectedItems()
            self.removeConfigurationAct.setDisabled(not len(selectedConfigs) > 0 or editorPanelIndex != 2)
            # TELEMETRY ACTIONS
            if not isEditorTelemetryArgumentOpen:
                selectedTelemetries = editor.telemetriesTab.telemetryTable.selectedItems()
                self.removeTelemetryAct.setDisabled(not len(selectedTelemetries) > 0 or editorPanelIndex != 4)
                self.addTelemetryArgumentAct.setDisabled(True)
                self.removeTelemetryArgumentAct.setDisabled(True)
            else:
                selectedArguments = editor.telemetriesTab.telemetryArgumentsTable.selectedItems()
                self.removeTelemetryArgumentAct.setDisabled(not len(selectedArguments) > 0 or editorPanelIndex != 4)
                self.addTelemetryArgumentAct.setDisabled(False)
                self.addTelemetryAct.setDisabled(False)
                self.removeTelemetryAct.setDisabled(True)
            # TELECOMMAND ACTIONS
            if not isEditorTelecommandArgumentOpen:
                selectedTelecommands = editor.telecommandsTab.telecommandTable.selectedItems()
                self.removeTelecommandAct.setDisabled(not len(selectedTelecommands) > 0 or editorPanelIndex != 5)
                self.addTelecommandArgumentAct.setDisabled(True)
                self.removeTelecommandArgumentAct.setDisabled(True)
            else:
                selectedArguments = editor.telecommandsTab.telecommandArgumentsTable.selectedItems()
                self.removeTelecommandArgumentAct.setDisabled(not len(selectedArguments) > 0 or editorPanelIndex != 5)
                self.addTelecommandArgumentAct.setDisabled(False)
                self.addTelecommandAct.setDisabled(False)
                self.removeTelecommandAct.setDisabled(True)
            # SHARED DATATYPES
            sharedDataTypeEditor = editor.dataTypesTab
            if len(sharedDataTypeEditor.editorCategories) == 0:
                selectedDataTypes = sharedDataTypeEditor.table.selectedItems()
                self.removeDataTypeAct.setDisabled(not len(selectedDataTypes) > 0 or editorPanelIndex != 3)
                self.changeDataTypeAct.setDisabled(not len(selectedDataTypes) > 0 or editorPanelIndex != 3)
                self.addDataTypeAct.setDisabled(False)
                self.addEnumValueAct.setDisabled(True)
                self.removeEnumValueAct.setDisabled(True)
            else:
                if isinstance(sharedDataTypeEditor.editorCategories[-1], EnumEditorWidget):
                    selectedValues = sharedDataTypeEditor.editorCategories[-1].valuesTableWidget.selectedItems()
                    self.removeDataTypeAct.setDisabled(True)
                    self.changeDataTypeAct.setDisabled(True)
                    self.addDataTypeAct.setDisabled(True)
                    self.addEnumValueAct.setDisabled(False)
                    self.removeEnumValueAct.setDisabled(not len(selectedValues) > 0 or editorPanelIndex != 3)
                if isinstance(sharedDataTypeEditor.editorCategories[-1], StructureEditorWidget):
                    selectedElements = sharedDataTypeEditor.editorCategories[-1].elementTable.selectedItems()
                    self.removeDataTypeAct.setDisabled(not len(selectedElements) > 0 or editorPanelIndex != 3)
                    self.changeDataTypeAct.setDisabled(not len(selectedElements) > 0 or editorPanelIndex != 3)
                    self.addDataTypeAct.setDisabled(False)
                    self.addEnumValueAct.setDisabled(True)
                    self.removeEnumValueAct.setDisabled(True)
        self.populateFileMenu()

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

    def addDatabaseUnit(self):
        databaseTabEditor: DatabaseEditor = self.packetTabWidget.currentWidget()
        currentEditor: UnitsEditorWidget  = databaseTabEditor.currentWidget()
        if isinstance(currentEditor, UnitsEditorWidget):
            currentEditor.addUnit()
        else:
            databaseTabEditor.setCurrentIndex(0)
            currentEditor: UnitsEditorWidget = databaseTabEditor.currentWidget()
            currentEditor.addUnit()

    def removeDatabaseUnit(self):
        databaseTabEditor: DatabaseEditor = self.packetTabWidget.currentWidget()
        currentEditor: UnitsEditorWidget = databaseTabEditor.currentWidget()
        if isinstance(currentEditor, UnitsEditorWidget):
            currentEditor.deleteUnit()
        else:
            databaseTabEditor.setCurrentIndex(0)
            currentEditor: UnitsEditorWidget = databaseTabEditor.currentWidget()
            currentEditor.deleteUnit()

    def addDatabaseConstant(self):
        databaseTabEditor: DatabaseEditor = self.packetTabWidget.currentWidget()
        currentEditor: ConstantEditorWidget = databaseTabEditor.currentWidget()
        if isinstance(currentEditor, ConstantEditorWidget):
            currentEditor.addConstant()
        else:
            databaseTabEditor.setCurrentIndex(2)
            currentEditor: ConstantEditorWidget = databaseTabEditor.currentWidget()
            currentEditor.addConstant()

    def removeDatabaseConstant(self):
        databaseTabEditor: DatabaseEditor = self.packetTabWidget.currentWidget()
        currentEditor: ConstantEditorWidget = databaseTabEditor.currentWidget()
        if isinstance(currentEditor, ConstantEditorWidget):
            currentEditor.deleteConstant()
        else:
            databaseTabEditor.setCurrentIndex(0)
            currentEditor: ConstantEditorWidget = databaseTabEditor.currentWidget()
            currentEditor.deleteConstant()

    def addDatabaseConfig(self):
        databaseTabEditor: DatabaseEditor = self.packetTabWidget.currentWidget()
        currentEditor: ConfigsEditorWidget = databaseTabEditor.currentWidget()
        if isinstance(currentEditor, ConfigsEditorWidget):
            currentEditor.addConfig()
        else:
            databaseTabEditor.setCurrentIndex(2)
            currentEditor: ConfigsEditorWidget = databaseTabEditor.currentWidget()
            currentEditor.addConfig()

    def removeDatabaseConfig(self):
        databaseTabEditor: DatabaseEditor = self.packetTabWidget.currentWidget()
        currentEditor: ConfigsEditorWidget = databaseTabEditor.currentWidget()
        if isinstance(currentEditor, ConfigsEditorWidget):
            currentEditor.deleteConfig()

    def addSharedTypeElement(self):
        databaseTabEditor: DatabaseEditor = self.packetTabWidget.currentWidget()
        currentEditor: SharedTypesEditorWidget = databaseTabEditor.currentWidget()
        if isinstance(currentEditor, SharedTypesEditorWidget):
            currentEditor.addDataType()
        else:
            databaseTabEditor.setCurrentIndex(3)
            currentEditor: SharedTypesEditorWidget = databaseTabEditor.currentWidget()
            currentEditor.addDataType()

    def changeSharedTypeElementCategory(self):
        databaseTabEditor: DatabaseEditor = self.packetTabWidget.currentWidget()
        currentEditor: SharedTypesEditorWidget = databaseTabEditor.currentWidget()
        if isinstance(currentEditor, SharedTypesEditorWidget):
            currentEditor.changeDataTypeCategory()
        else:
            databaseTabEditor.setCurrentIndex(3)
            currentEditor: SharedTypesEditorWidget = databaseTabEditor.currentWidget()
            currentEditor.changeDataTypeCategory()

    def removeSharedTypeElement(self):
        databaseTabEditor: DatabaseEditor = self.packetTabWidget.currentWidget()
        currentEditor: SharedTypesEditorWidget = databaseTabEditor.currentWidget()
        if isinstance(currentEditor, SharedTypesEditorWidget):
            currentEditor.removeDataType()

    def addSharedEnumValue(self):
        databaseTabEditor: DatabaseEditor = self.packetTabWidget.currentWidget()
        currentEditor: SharedTypesEditorWidget = databaseTabEditor.currentWidget()
        if isinstance(currentEditor, SharedTypesEditorWidget):
            if isinstance(currentEditor.editorCategories[-1], EnumEditorWidget):
                currentEditor.editorCategories[-1].addEnumValue()
        else:
            databaseTabEditor.setCurrentIndex(3)
            currentEditor: SharedTypesEditorWidget = databaseTabEditor.currentWidget()
            if isinstance(currentEditor.editorCategories[-1], EnumEditorWidget):
                currentEditor.editorCategories[-1].addEnumValue()

    def removeSharedEnumValue(self):
        databaseTabEditor: DatabaseEditor = self.packetTabWidget.currentWidget()
        currentEditor: SharedTypesEditorWidget = databaseTabEditor.currentWidget()
        if isinstance(currentEditor, SharedTypesEditorWidget):
            if isinstance(currentEditor.editorCategories[-1], EnumEditorWidget):
                currentEditor.editorCategories[-1].deleteEnumValue()

    def addDatabaseTelemetry(self):
        databaseTabEditor: DatabaseEditor = self.packetTabWidget.currentWidget()
        currentEditor: TelemetryEditorWidget = databaseTabEditor.currentWidget()
        if isinstance(currentEditor, TelemetryEditorWidget):
            currentEditor.addTelemetryType()
        else:
            databaseTabEditor.setCurrentIndex(4)
            currentEditor: TelemetryEditorWidget = databaseTabEditor.currentWidget()
            currentEditor.addTelemetryType()

    def removeDatabaseTelemetry(self):
        databaseTabEditor: DatabaseEditor = self.packetTabWidget.currentWidget()
        currentEditor: TelemetryEditorWidget = databaseTabEditor.currentWidget()
        if isinstance(currentEditor, TelemetryEditorWidget):
            currentEditor.deleteTelemetryType()

    def addDatabaseTelemetryArgument(self):
        databaseTabEditor: DatabaseEditor = self.packetTabWidget.currentWidget()
        currentEditor: TelemetryEditorWidget = databaseTabEditor.currentWidget()
        if isinstance(currentEditor, TelemetryEditorWidget):
            currentEditor.addArgumentType()
        else:
            databaseTabEditor.setCurrentIndex(4)
            currentEditor: TelemetryEditorWidget = databaseTabEditor.currentWidget()
            currentEditor.addArgumentType()

    def removeDatabaseTelemetryArgument(self):
        databaseTabEditor: DatabaseEditor = self.packetTabWidget.currentWidget()
        currentEditor: TelemetryEditorWidget = databaseTabEditor.currentWidget()
        if isinstance(currentEditor, TelemetryEditorWidget):
            currentEditor.deleteArgumentType()

    def addDatabaseTelecommand(self):
        databaseTabEditor: DatabaseEditor = self.packetTabWidget.currentWidget()
        currentEditor: TelecommandEditorWidget = databaseTabEditor.currentWidget()
        if isinstance(currentEditor, TelecommandEditorWidget):
            currentEditor.addTelecommandType()
        else:
            databaseTabEditor.setCurrentIndex(5)
            currentEditor: TelecommandEditorWidget = databaseTabEditor.currentWidget()
            currentEditor.addTelecommandType()

    def removeDatabaseTelecommand(self):
        databaseTabEditor: DatabaseEditor = self.packetTabWidget.currentWidget()
        currentEditor: TelecommandEditorWidget = databaseTabEditor.currentWidget()
        if isinstance(currentEditor, TelecommandEditorWidget):
            currentEditor.deleteTelecommandType()

    def addDatabaseTelecommandArgument(self):
        databaseTabEditor: DatabaseEditor = self.packetTabWidget.currentWidget()
        currentEditor: TelecommandEditorWidget = databaseTabEditor.currentWidget()
        if isinstance(currentEditor, TelecommandEditorWidget):
            currentEditor.addArgumentType()
        else:
            databaseTabEditor.setCurrentIndex(5)
            currentEditor: TelecommandEditorWidget = databaseTabEditor.currentWidget()
            currentEditor.addArgumentType()

    def removeDatabaseTelecommandArgument(self):
        databaseTabEditor: DatabaseEditor = self.packetTabWidget.currentWidget()
        currentEditor: TelecommandEditorWidget = databaseTabEditor.currentWidget()
        if isinstance(currentEditor, TelemetryEditorWidget):
            currentEditor.deleteArgumentType()

    def toggleDarkMode(self):
        self.settings['DARK_THEME'] = not self.settings['DARK_THEME']
        saveSettings(self.settings, 'settings')
        themeText = 'Light Theme' if self.settings['DARK_THEME'] else 'Dark Theme'
        self.darkModeAct.setText(f'&{themeText}')
        self.darkModeAct.setStatusTip(f' Applying {themeText}')
        self._setTheme()

    def _setTheme(self):
        if self.settings['DARK_THEME']:
            qdarktheme.setup_theme('dark', additional_qss="QToolTip {color: black;}")
        else:
            qdarktheme.setup_theme('light')
        self.locationSearchBar.changeTheme()
        # UPDATING ICONS
        self._createIcons()
        self.newParserAction.setIcon(self.icons['NEW_WINDOW'])
        self.openParserAction.setIcon(self.icons['OPEN_IN_BROWSER'])
        self.saveParserAction.setIcon(self.icons['SAVE'])
        self.saveAllParserAction.setIcon(self.icons['SAVE_ALL'])
        self.closeParserAction.setIcon(self.icons['CLOSE_WINDOW'])
        self.importParserAction.setIcon(self.icons['DOWNLOAD'])
        self.addUnitAct.setIcon(self.icons['ADD_NEW'])
        self.removeUnitAct.setIcon(self.icons['NEGATIVE'])
        self.addConstantAct.setIcon(self.icons['ADD_NEW'])
        self.removeConstantAct.setIcon(self.icons['NEGATIVE'])
        self.addConfigurationAct.setIcon(self.icons['ADD_NEW'])
        self.removeConfigurationAct.setIcon(self.icons['NEGATIVE'])
        self.addDataTypeAct.setIcon(self.icons['ADD_NEW'])
        self.changeDataTypeAct.setIcon(self.icons['EDIT'])
        self.removeDataTypeAct.setIcon(self.icons['NEGATIVE'])
        self.addEnumValueAct.setIcon(self.icons['ADD_SUBNODE'])
        self.removeEnumValueAct.setIcon(self.icons['DELETE_SUBNODE'])
        self.addTelemetryAct.setIcon(self.icons['ADD_NEW'])
        self.removeTelemetryAct.setIcon(self.icons['NEGATIVE'])
        self.addTelemetryArgumentAct.setIcon(self.icons['ADD_SUBNODE'])
        self.removeTelemetryArgumentAct.setIcon(self.icons['DELETE_SUBNODE'])
        self.addTelecommandAct.setIcon(self.icons['ADD_NEW'])
        self.removeTelecommandAct.setIcon(self.icons['NEGATIVE'])
        self.addTelecommandArgumentAct.setIcon(self.icons['ADD_SUBNODE'])
        self.removeTelecommandArgumentAct.setIcon(self.icons['DELETE_SUBNODE'])
        self.newDisplayTabAct.setIcon(self.icons['ADD_FOLDER'])
        self.closeDisplayTabAct.setIcon(self.icons['DELETE_FOLDER'])
        self.newSimpleIndicatorAct.setIcon(self.icons['FULL_SCREEN'])
        self.newGridIndicatorAct.setIcon(self.icons['FOUR_SQUARES'])
        self.newMultiCurveAct.setIcon(self.icons['COMBO_CHART'])
        self.runSerialAct.setIcon(self.icons['PLAY'])
        self.stopSerialAct.setIcon(self.icons['STOP'])
        self.openMonitorAct.setIcon(self.icons['MONITOR'])
        self.updatingWeatherAct.setIcon(self.icons['RESET'])
        self.getGeolocationAct.setIcon(self.icons['MY_LOCATION'])
        self.githubAct.setIcon(self.icons['GITHUB'])
        self.aboutAct.setIcon(self.icons['HELP'])
        # UPDATING PLOT WIDGETS
        displayTabs = [self.displayTabWidget.tabWidget.widget(index) for index in range(self.displayTabWidget.tabWidget.count())]
        for displayTab in displayTabs:
            for dockWidget in displayTab.findChildren(QDockWidget):
                if dockWidget.isVisible() and isinstance(dockWidget, DisplayDockWidget):
                    dockWidget.hoverButton.setIcon(self.icons['EDIT'])
                    dockWidget.display.changeTheme()
        # UPDATING WEATHER WIDGETS
        if self.weatherTabWidget.forecastTabDisplay:
            locationTabs = [self.weatherTabWidget.forecastTabDisplay.widget(index) for index in range(self.weatherTabWidget.forecastTabDisplay.count())]
            for locationTab in locationTabs:
                locationTab.scrollableDayWidget.changeTheme()
                locationTab.observationDisplay.changeTheme()

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
        if self.packetTabWidget.unsavedChanges:
            unsavedMessage = "There are unsaved changes in the editor. What do you want to do?"
            buttons = QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel
            reply = QMessageBox.question(self, 'Unsaved Changes', unsavedMessage, buttons, QMessageBox.Save)
            if reply == QMessageBox.Save:
                self.saveAllParserTab()
                self.stopSerial()
                time.sleep(0.5)
                self.serialMonitorTimer.stop()
                self.settings['MAXIMIZED'] = 1 if self.isMaximized() else 0
                saveSettings(self.settings, 'settings')
                for window in QApplication.topLevelWidgets():
                    window.close()
                event.accept()
            elif reply == QMessageBox.Discard:
                self.stopSerial()
                time.sleep(0.5)
                self.serialMonitorTimer.stop()
                self.settings['MAXIMIZED'] = 1 if self.isMaximized() else 0
                saveSettings(self.settings, 'settings')
                for window in QApplication.topLevelWidgets():
                    window.close()
                event.accept()
            else:
                event.ignore()
                return
        else:
            buttons = QMessageBox.Yes | QMessageBox.No
            reply = QMessageBox.question(self, 'Exit', "Are you sure to quit?", buttons, QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.stopSerial()
                time.sleep(0.5)
                self.serialMonitorTimer.stop()
                self.settings['MAXIMIZED'] = 1 if self.isMaximized() else 0
                saveSettings(self.settings, 'settings')
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
        time.sleep(0.5)
        self.finished.emit(resultDict)
