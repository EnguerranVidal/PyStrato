######################## IMPORTS ########################
import json
import os
import folium
import geocoder
import requests
import pandas as pd

# ------------------- PyQt Modules -------------------- #
from PyQt5.QtWidgets import *
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWebChannel import QWebChannel
from PyQt5.QtCore import *
from PyQt5.QtGui import *

# --------------------- Sources ----------------------- #
from sources.common.FileHandling import loadSettings, saveSettings, nameGiving
from sources.common.Functions import isInternetAvailable
from sources.common.Widgets import FlatButton, SearchBar
from sources.weather.openweathermap import *


######################## CLASSES ########################
class WeatherWindow(QMainWindow):
    def __init__(self, path: str = os.path.dirname(__file__)):
        super().__init__()
        self.currentDir = path
        self.settings = loadSettings('settings')
        self.apiKey = self.settings['WEATHER_API_KEY']
        self.stackedWidget = QStackedWidget()
        self.setCentralWidget(self.stackedWidget)
        self.forecastTabDisplay = ForecastTabDisplay(self, self.currentDir)
        self.stackedWidget.addWidget(self.forecastTabDisplay)
        if isInternetAvailable():
            if not self.apiKey or not isValidAPIKey(self.apiKey):
                self.apiRegistrationWidget = ApiRegistrationWidget(self)
                self.apiRegistrationWidget.validApiRegistration.connect(self.switchToForecast)
                self.stackedWidget.addWidget(self.apiRegistrationWidget)
                self.stackedWidget.setCurrentWidget(self.apiRegistrationWidget)
            else:
                self.stackedWidget.setCurrentWidget(self.forecastTabDisplay)
        else:
            self.notAvailableDisplay = NoInternetDisplay(self, self.currentDir)
            self.stackedWidget.addWidget(self.notAvailableDisplay)
            self.stackedWidget.setCurrentWidget(self.notAvailableDisplay)
            # Creating time loop that checks for internet access
            self.internetAccessTimer = QTimer()
            self.internetAccessTimer.timeout.connect(self.checkInternetAccess)
            self.internetAccessTimer.start(100)

    def checkInternetAccess(self):
        if isInternetAvailable():
            self.switchToForecast()
            self.internetAccessTimer.stop()

    def changeApiKey(self, apiKey: str):
        self.apiKey = apiKey
        self.settings['WEATHER_API_KEY'] = apiKey
        saveSettings(self.settings, 'settings')
        if isInternetAvailable():
            self.switchToForecast()
        else:
            self.notAvailableDisplay = NoInternetDisplay(self, self.currentDir)
            self.stackedWidget.addWidget(self.notAvailableDisplay)
            self.stackedWidget.setCurrentWidget(self.notAvailableDisplay)
            # Creating time loop that checks for internet access
            self.internetAccessTimer = QTimer()
            self.internetAccessTimer.timeout.connect(self.checkInternetAccess)
            self.internetAccessTimer.start(100)

    def switchToForecast(self):
        self.stackedWidget.setCurrentWidget(self.forecastTabDisplay)


class NoInternetDisplay(QWidget):
    retry = pyqtSignal()

    def __init__(self, parent=None, path: str = os.path.dirname(__file__)):
        super().__init__(parent)
        self.currentDir = path
        self.iconPath = os.path.join(self.currentDir, 'sources/icons')
        layout = QVBoxLayout()

        # Label to display the message
        self.message_label = QLabel("No Internet Access")
        self.message_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.message_label)

        # Loading wheel animation
        self.loading_label = QLabel(self)
        self.loading_label.setAlignment(Qt.AlignCenter)
        self.loading_movie = QMovie(os.path.join(self.iconPath, "loading.gif"))  # Replace "loading.gif" with your loading animation file
        self.loading_label.setMovie(self.loading_movie)
        self.loading_movie.start()
        layout.addWidget(self.loading_label)

        # Button to trigger reloading
        self.retryButton = QPushButton("Retry")
        layout.addWidget(self.retryButton)
        self.setLayout(layout)
        self.retryButton.clicked.connect(self.emitRetrySignal)

    def emitRetrySignal(self):
        self.retry.emit()


class ForecastTabDisplay(QTabWidget):
    def __init__(self, parent=None, path: str = os.path.dirname(__file__)):
        super().__init__(parent)
        self.currentDir = path

        # LOADING LOCATIONS
        self.citiesDataFrame = self.loadSearchItemsFromJson()
        self.settings = loadSettings('settings')
        self.apiKey = self.settings['WEATHER_API_KEY']
        self.locations = []
        self.locationsWidgets = []
        for location in self.settings['LOCATIONS']:
            dataSlice = self.findCitySlice(location[0], location[1], location[2])
            self.locations.append(dataSlice.iloc[0])

    def loadLocations(self):
        self.locations, self.locationsWidgets = [], []
        self.settings = loadSettings('settings')
        for locationIndex, location in enumerate(self.settings['LOCATIONS']):
            dataSlice = self.findCitySlice(location[0], location[1], location[2])
            self.locations.append(dataSlice.iloc[0])
            self.addLocationTab(self.locations[locationIndex])

    def showMapDialog(self):
        dialog = MapDialog(self.citiesDataFrame, parent=self, path=self.currentDir)
        if dialog.exec_() == QDialog.Accepted:
            lastMarker = dialog.markers[-1]
            cityData = lastMarker[0]
            print(type(cityData))
            print(cityData)

    def removeLocation(self, index):
        self.locationsWidgets.pop(index)
        self.removeTab(index)
        self.locations.pop(index)
        self.settings['LOCATIONS'].pop(index)
        saveSettings(self.settings, 'settings')

    def addLocationTab(self, cityData):
        displayWidget, displayLayout = QWidget(), QHBoxLayout()
        name, state, country = cityData['name'], cityData['state'], cityData['country']
        observationData = getObservationWeatherData(name, state, country, self.apiKey)
        forecastData = get5Day3HoursForecastWeatherData(name, state, country, self.apiKey)
        pollutionData = getAirPollutionData(name, state, country, self.apiKey)
        observationDisplay = WeatherObservationDisplay(observationData, pollutionData, metric=True)
        forecastDisplay = WeatherForecastWidget(observationData, forecastData, metric=True)
        displayLayout.addWidget(observationDisplay)
        displayLayout.addWidget(forecastDisplay)
        displayWidget.setLayout(displayLayout)
        self.locationsWidgets.append((observationDisplay, forecastDisplay))
        self.addTab(displayWidget, name)

    def findCitySlice(self, cityName='', state='', country=''):
        mask = ((self.citiesDataFrame['name'] == cityName) &
                (self.citiesDataFrame['state'] == state) &
                (self.citiesDataFrame['country'] == country))
        return self.citiesDataFrame[mask]

    def loadSearchItemsFromJson(self):
        path = os.path.join(self.currentDir, 'sources/weather/city.list.json')
        citiesDataFrame = pd.read_json(path)
        citiesDataFrame['format'] = citiesDataFrame.apply(
            lambda row: f"{row['name']}, {row['state']}, {row['country']}" if row[
            'state'] else f"{row['name']}, {row['country']}",
        axis=1)
        return citiesDataFrame

    def getGpsLocation(self):
        g = geocoder.ip('me')
        if g.status == 'OK':
            cityName = g.city
            stateName = g.state
            countryName = g.country
            dataSlice = self.findCitySlice(cityName, stateName, countryName).iloc[0]


class MapDialog(QDialog):
    def __init__(self, citiesDataFrame, parent: ForecastTabDisplay = None, path: str = os.path.dirname(__file__),
                 cityData: dict = None):
        super().__init__(parent)
        self.citiesDataFrame = citiesDataFrame
        self.currentDir = path
        self.iconPath = os.path.join(self.currentDir, 'sources/icons')
        self.foliumMap = None
        self.markers = []
        self.setWindowTitle("Setting location")
        self.setGeometry(100, 100, 800, 600)
        layout = QVBoxLayout()
        topLayout = QHBoxLayout()

        # SEARCH BAR
        self.searchBar = SearchBar(options=self.citiesDataFrame['format'])
        self.searchBar.setFixedHeight(25)
        self.searchBar.suggestionSelected.connect(self.onSearchResultClicked)
        topLayout.addWidget(self.searchBar, 1)

        # GPS LOCATION BUTTON
        self.gpsButton = FlatButton(os.path.join(self.iconPath, 'light-theme/icons8-my-location-96.png'))
        self.gpsButton.setToolTip('Show Your Location')
        self.gpsButton.clicked.connect(self.useGpsLocation)
        topLayout.addWidget(self.gpsButton)

        self.mapView = QWebEngineView()
        self.doneButton = QPushButton("Done")
        self.doneButton.clicked.connect(self.accept)
        layout.addLayout(topLayout)
        layout.addWidget(self.mapView)
        layout.addWidget(self.doneButton)
        self.setLayout(layout)

        self.showMap()
        if cityData is None:
            self.useGpsLocation()
        else:
            self.addMarker(cityData)

    def findClosestCity(self, latitude, longitude):
        self.citiesDataFrame['distance'] = ((self.citiesDataFrame['coord'].apply(lambda x: x['lat']) - latitude) ** 2 +
                                            (self.citiesDataFrame['coord'].apply(
                                                lambda x: x['lon']) - longitude) ** 2) ** 0.5
        closestCityIndex = self.citiesDataFrame['distance'].idxmin()
        cityData = self.citiesDataFrame.loc[closestCityIndex]
        return cityData

    def showFavourites(self):
        menu = QMenu(self)
        action1 = menu.addAction("Dummy 1")
        action2 = menu.addAction("Dummy 2")
        selected_action = menu.exec_(self.favouritesButton.mapToGlobal(QPoint(0, self.favouritesButton.height())))
        if selected_action == action1:
            print("Option 1 selected")
        elif selected_action == action2:
            print("Option 2 selected")

    def useGpsLocation(self):
        g = geocoder.ip('me')
        if g.latlng:
            self.clearMarkers()
            closestCity = self.findClosestCity(g.latlng[0], g.latlng[1])
            self.addMarker(closestCity)
            self.setMapView(g.latlng[0], g.latlng[1], 12)

    def onSearchResultClicked(self):
        formattedCityName = self.searchBar.text()
        cityData = self.citiesDataFrame[self.citiesDataFrame['format'] == formattedCityName]
        if not cityData.empty:
            latitude = cityData['coord'].iloc[0]['lat']
            longitude = cityData['coord'].iloc[0]['lon']
            g = geocoder.location((longitude, latitude))
            if g.latlng:
                self.clearMarkers()
                self.addMarker(cityData.iloc[0])
                self.setMapView(g.latlng[1], g.latlng[0])
                print("Location:", g.latlng)

    def clearMarkers(self):
        zoom = self.foliumMap.options['zoom']
        newFoliumMap = folium.Map(location=self.foliumMap.location, zoom_start=zoom)
        # Save New Map
        mapPath = os.path.join(os.path.dirname(__file__), 'map.html')
        newFoliumMap.save(mapPath)
        self.mapView.setUrl(QUrl.fromLocalFile(mapPath))
        self.foliumMap = newFoliumMap

    def addMarker(self, cityData):
        popupText = cityData['format']
        longitude, latitude = cityData['coord']['lon'], cityData['coord']['lat']
        marker = folium.Marker(location=[latitude, longitude], popup=popupText)
        marker.add_to(self.foliumMap)
        markerTuple = (cityData, marker)
        self.markers.append(markerTuple)
        self.setMapView(latitude, longitude, 12)

    def showMap(self):
        self.foliumMap = folium.Map(location=[0, 0], zoom_start=12)
        mapPath = os.path.join(os.path.dirname(__file__), 'map.html')
        self.foliumMap.save(mapPath)
        self.mapView.setUrl(QUrl.fromLocalFile(mapPath))

    def setMapView(self, latitude, longitude, zoom=None):
        self.foliumMap.location = [latitude, longitude]
        if zoom is not None:
            self.foliumMap.zoom_start = zoom
        self.foliumMap.save(os.path.join(os.path.dirname(__file__), 'map.html'))
        self.mapView.reload()
