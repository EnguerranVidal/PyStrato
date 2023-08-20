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
from sources.common.FileHandling import load_settings, save_settings, nameGiving
from sources.common.Widgets import FlatButton, SearchBar


######################## CLASSES ########################
class WeatherWidget(QMainWindow):
    def __init__(self, path: str = os.path.dirname(__file__)):
        super().__init__()
        self.currentDir = path
        self.settings = load_settings('settings')
        self.apiKey = self.settings['WEATHER_API_KEY']
        self.central_widget = QStackedWidget()
        self.setCentralWidget(self.central_widget)

        self.weather_forecast_widget = WeatherForecastWidget(self, self.currentDir)
        self.central_widget.addWidget(self.weather_forecast_widget)

        if not self.apiKey:
            self.api_registration_widget = ApiRegistrationWidget(self)
            self.api_registration_widget.validApiRegistration.connect(self.switchToForecast)
            self.central_widget.addWidget(self.api_registration_widget)
            self.central_widget.setCurrentWidget(self.api_registration_widget)
        else:
            self.central_widget.setCurrentWidget(self.weather_forecast_widget)

    def switchToForecast(self, apiKey: str):
        self.apiKey = apiKey
        self.settings['WEATHER_API_KEY'] = apiKey
        save_settings(self.settings, 'settings')
        self.central_widget.setCurrentWidget(self.weather_forecast_widget)


class WeatherForecastWidget(QWidget):
    def __init__(self, parent=None, path: str = os.path.dirname(__file__)):
        super().__init__(parent)
        self.currentDir = path
        self.forecastLabel = None
        self.parent = parent
        self.citiesDataFrame = None
        layout = QVBoxLayout()
        self.forecastLabel = QLabel("Weather Forecast:")
        layout.addWidget(self.forecastLabel, alignment=Qt.AlignCenter)
        self.mapButton = QPushButton("Open Map")
        self.mapButton.clicked.connect(self.showMapDialog)
        layout.addWidget(self.mapButton, alignment=Qt.AlignCenter)
        self.setLayout(layout)

    def showMapDialog(self):
        dialog = MapDialog(self, self.currentDir)
        if dialog.exec_() == QDialog.Accepted:
            lastMarker = dialog.markers[-1]
            cityData = lastMarker[0]
            print(cityData['coord'])
            latitude, longitude = cityData['coord']['lat'], cityData['coord']['lon']
            print("Marker Popup:", cityData['format'])
            print("City Name:", cityData['name'])
            print("Latitude:", latitude)
            print("Longitude:", longitude)


class MapDialog(QDialog):
    def __init__(self, parent: WeatherForecastWidget = None, path: str = os.path.dirname(__file__), cityData: dict = None):
        super().__init__(parent)
        self.citiesDataFrame = None
        self.currentDir = path
        self.iconPath = os.path.join(self.currentDir, 'sources/icons')
        self.foliumMap = None
        self.markers = []
        self.setWindowTitle("Setting location")
        self.setGeometry(100, 100, 800, 600)
        layout = QVBoxLayout()
        topLayout = QHBoxLayout()

        # SEARCH BAR
        self.loadSearchItemsFromJson()
        self.searchBar = SearchBar(options=self.citiesDataFrame['format'])
        self.searchBar.setFixedHeight(25)
        self.searchBar.suggestionSelected.connect(self.onSearchResultClicked)
        topLayout.addWidget(self.searchBar, 1)

        # GPS LOCATION BUTTON
        self.gpsButton = FlatButton(os.path.join(self.iconPath, 'light-theme/icons8-my-location-96.png'))
        self.gpsButton.setToolTip('Show Your Location')
        self.gpsButton.clicked.connect(self.useGpsLocation)
        topLayout.addWidget(self.gpsButton)

        # FAVOURITES BUTTON
        self.favouritesButton = FlatButton(os.path.join(self.iconPath, 'light-theme/icons8-star-empty-96.png'))
        self.favouritesButton.clicked.connect(self.showFavourites)
        # topLayout.addWidget(self.favouritesButton)

        layout.addLayout(topLayout)
        self.mapView = QWebEngineView()
        layout.addWidget(self.mapView)
        self.doneButton = QPushButton("Done")
        self.doneButton.clicked.connect(self.accept)
        layout.addWidget(self.doneButton)
        self.setLayout(layout)

        self.showMap()
        if cityData is None:
            self.useGpsLocation()
        else:
            self.addMarker(cityData)
    
    def loadSearchItemsFromJson(self):
        path = os.path.join(self.currentDir, 'sources/weather/city.list.json')
        self.citiesDataFrame = pd.read_json(path)
        self.citiesDataFrame['format'] = self.citiesDataFrame.apply(
            lambda row: f"{row['name']}, {row['state']}, {row['country']}" if row[
                'state'] else f"{row['name']}, {row['country']}",
            axis=1)

    def findClosestCity(self, latitude, longitude):
        self.citiesDataFrame['distance'] = ((self.citiesDataFrame['coord'].apply(lambda x: x['lat']) - latitude) ** 2 +
                                            (self.citiesDataFrame['coord'].apply(lambda x: x['lon']) - longitude) ** 2) ** 0.5
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
            print("IP Location:", g.latlng)

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


class ApiRegistrationWidget(QWidget):
    validApiRegistration = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.apiKey = None
        layout = QGridLayout()
        info_label = QLabel("This feature works with OpenWeatherMap.")
        info_label.setFont(QFont("Arial", 12, QFont.Bold))
        info_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(info_label, 0, 0, 1, 2)

        api_key_button = QPushButton("Enter API Key", self)
        api_key_button.setFixedWidth(120)
        api_key_button.clicked.connect(self.showAPIKeyDialog)

        create_account_button = QPushButton("Create Account", self)
        create_account_button.setFixedWidth(120)
        create_account_button.clicked.connect(self.createAPIAccount)

        layout.addWidget(api_key_button, 1, 0, Qt.AlignRight)
        layout.addWidget(create_account_button, 1, 1, Qt.AlignLeft)
        self.setLayout(layout)

    def showAPIKeyDialog(self):
        dialog = ApiKeyDialog(self)
        result = dialog.exec_()
        if result == QDialog.Accepted:
            newApiKey = dialog.apiKeyLineEdit.text()
            if self.isValidAPIKey(newApiKey):
                self.validApiRegistration.emit(newApiKey)
            else:
                QMessageBox.critical(self, "Invalid API Key",
                                     "The entered API key is invalid. Please enter a valid API key.")

    @staticmethod
    def isValidAPIKey(api_key):
        url = f"http://api.openweathermap.org/data/2.5/weather?q=Paris&appid={api_key}"
        response = requests.get(url)
        return response.status_code == 200

    @staticmethod
    def createAPIAccount():
        import webbrowser
        webbrowser.open('https://home.openweathermap.org/users/sign_up')


class ApiKeyDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Enter API Key")
        self.apiKeyLineEdit = QLineEdit()
        self.apiKeyLineEdit.setEchoMode(QLineEdit.Password)

        self.toggleButton = QPushButton("", self)
        self.toggleButton.setStyleSheet("background-color: transparent; border: none;")
        self.toggleButton.setFlat(True)
        self.toggleButton.setIconSize(QSize(16, 16))
        self.updateToggleIcon()
        self.toggleButton.clicked.connect(self.toggleEchoMode)

        layout = QHBoxLayout()
        layout.addWidget(self.toggleButton)
        layout.addWidget(self.apiKeyLineEdit)

        buttonLayout = QVBoxLayout()
        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)
        buttonLayout.addLayout(layout)
        buttonLayout.addWidget(buttonBox)

        self.setLayout(buttonLayout)

    def toggleEchoMode(self):
        if self.apiKeyLineEdit.echoMode() == QLineEdit.Password:
            self.apiKeyLineEdit.setEchoMode(QLineEdit.Normal)
        else:
            self.apiKeyLineEdit.setEchoMode(QLineEdit.Password)
        self.updateToggleIcon()

    def updateToggleIcon(self):
        if self.apiKeyLineEdit.echoMode() == QLineEdit.Password:
            self.toggleButton.setIcon(
                QIcon('sources/icons/light-theme/icons8-eye-96.png'))
        else:
            self.toggleButton.setIcon(
                QIcon('sources/icons/light-theme/icons8-hide-96.png'))
