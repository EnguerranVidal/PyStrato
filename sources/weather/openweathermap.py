######################## IMPORTS ########################
from collections import Counter
import requests
from datetime import datetime
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


######################## FUNCTIONS ########################
def getForecastWeatherData(city, state, country, api_key, metric=True):
    baseUrl = "http://api.openweathermap.org/data/2.5/forecast"
    location = f"{city},{state},{country}"
    params = {
        "q": location,
        "appid": api_key,
        "units": "metric" if metric else "imperial"
    }
    response = requests.get(baseUrl, params=params)
    if response.status_code == 200:
        data = response.json()
        weatherData = {}
        for singleForecast in data["list"]:
            date = datetime.utcfromtimestamp(singleForecast["dt"]).strftime('%Y-%m-%d')
            time = datetime.utcfromtimestamp(singleForecast["dt"]).strftime('%H:%M')
            weather_icon = singleForecast["weather"][0]["icon"]
            temperature = singleForecast["main"]["temp"]
            rainProbability = singleForecast.get("rain", {}).get("3h", 0)
            if date not in weatherData:
                weatherData[date] = {
                    "date": date,
                    "time": [time],
                    "weather_icon": [weather_icon],
                    "max_temp": temperature,
                    "min_temp": temperature,
                    "temperatures": [temperature],
                    "rain_probabilities": [rainProbability],
                    "icons": [weather_icon]
                }
            else:
                if temperature > weatherData[date]["max_temp"]:
                    weatherData[date]["max_temp"] = temperature
                if temperature < weatherData[date]["min_temp"]:
                    weatherData[date]["min_temp"] = temperature
                weatherData[date]["weather_icon"].append(weather_icon)
                weatherData[date]["icons"].append(weather_icon)
                weatherData[date]["time"].append(time)
                weatherData[date]["temperatures"].append(temperature)
                weatherData[date]["rain_probabilities"].append(rainProbability)

        for date, dayData in weatherData.items():
            day_icons = [icon for icon in dayData["weather_icon"] if icon.endswith('d')]
            if day_icons:
                mostCommonIcon = Counter(day_icons).most_common(1)[0][0]
            else:
                target = datetime.strptime("12:00", '%H:%M').time()
                timeDiffs = [abs((datetime.combine(datetime.today(),
                                                   datetime.strptime(time_str, '%H:%M').time()) - datetime.combine(
                    datetime.today(), target)).seconds) for time_str in dayData["time"]]
                closestTimeIndex = timeDiffs.index(min(timeDiffs))
                mostCommonIcon = dayData["weather_icon"][closestTimeIndex]
            weatherData[date]["weather_icon"] = mostCommonIcon
        # Remove days with incomplete forecasts (except today)
        return weatherData.values()
    else:
        print("Error:", response.status_code)
        return None


def getObservationWeatherData(city, state, country, api_key, metric=True):
    base_url = "http://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": f"{city},{state},{country}",
        "appid": api_key,
        "units": "metric" if metric else "imperial"
    }
    response = requests.get(base_url, params=params)
    data = response.json()
    if data.get("main") and data.get("weather") and data.get("wind"):
        return data
