######################## IMPORTS ########################
from collections import Counter
from datetime import datetime, timedelta
import geocoder
import numpy as np
import pyqtgraph as pg
import requests
from scipy.interpolate import make_interp_spline

# ------------------- PyQt Modules -------------------- #
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

# --------------------- Sources ----------------------- #
from sources.common.Functions import getTextHeight
from sources.common.Widgets import ArrowWidget


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
            if isValidAPIKey(newApiKey):
                self.validApiRegistration.emit(newApiKey)
            else:
                QMessageBox.critical(self, "Invalid API Key", "The entered API key is invalid. Please enter a valid API key.")

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


class WeatherObservationDisplay(QWidget):
    def __init__(self, observationData, pollutionData, metric=True):
        super().__init__()
        self.metric = metric
        self.observationData = observationData
        self.pollutionData = pollutionData
        self.observationTime = datetime.fromtimestamp(self.observationData['dt'])

        # OBSERVATION LAYOUT ----------------------------------
        observationFrame = QFrame()
        observationFrame.setFrameShape(QFrame.Box)
        observationFrame.setLineWidth(2)
        observationFrame.setAutoFillBackground(True)
        palette = observationFrame.palette()
        palette.setColor(observationFrame.backgroundRole(), QColor("#96bee0"))
        observationFrame.setPalette(palette)
        observationLayout = QVBoxLayout()
        observationLabel = QLabel(f"<b><font size='4'>CURRENT WEATHER {self.observationTime.strftime('%a %d')}</font></b>")
        topRowLayout = QGridLayout()
        bottomRow = QGridLayout()
        # Weather Icon
        self.iconLabel = QLabel()
        weatherIconCode = self.observationData['weather'][0]['icon']
        weatherIconUrl = f"http://openweathermap.org/img/wn/{weatherIconCode}.png"
        iconImage = requests.get(weatherIconUrl)
        pixmap = QPixmap()
        pixmap.loadFromData(iconImage.content)
        combinedLabelHeight = getTextHeight(20) + getTextHeight(10)
        iconPixmap = pixmap.scaledToHeight(combinedLabelHeight)
        self.iconLabel.setPixmap(iconPixmap)
        topRowLayout.addWidget(self.iconLabel, 0, 0, 2, 2)
        # Temperature Label
        temperatureLabel = QLabel()
        temperatureLabel.setAlignment(Qt.AlignCenter)
        temperature = int(self.observationData['main']['temp'])
        temperatureUnit = '°C' if self.metric else '°F'
        temperature_text = f"<b><font size='30'>{temperature}</font><sup><font size='10'>{temperatureUnit}</font></sup></b>"
        temperatureLabel.setText(temperature_text)
        topRowLayout.addWidget(temperatureLabel, 0, 2, 2, 2, alignment=Qt.AlignLeft)
        # Weather Description
        weatherDescriptionLabel = QLabel()
        weatherDescription = self.observationData['weather'][0]['description']
        weatherDescription = weatherDescription.capitalize()
        weatherDescriptionLabel.setText(f"<b>{weatherDescription}</b>")
        topRowLayout.addWidget(weatherDescriptionLabel, 0, 4, alignment=Qt.AlignLeft)
        # Feels Like Temperature
        feelLikeTemperatureLabel = QLabel()
        feelLikeTemperature = int(self.observationData['main']['feels_like'])
        feelLikeTemperatureLabel.setText(f'Feels like {feelLikeTemperature}°')
        topRowLayout.addWidget(feelLikeTemperatureLabel, 1, 4, alignment=Qt.AlignLeft)
        # Wind Speed and Direction
        windTitleLabel = QLabel("Wind")
        bottomRow.addWidget(windTitleLabel, 0, 0)
        windInfoLayout = QHBoxLayout()
        windSpeed = self.observationData['wind']['speed'] * 3.6 if self.metric else self.observationData['wind']['speed']
        windSpeedLabel = QLabel(f"<b>{int(windSpeed):.1f} km/h</b>")
        windInfoLayout.addWidget(windSpeedLabel, alignment=Qt.AlignLeft)
        windDirectionWidget = ArrowWidget("../sources/icons/light-theme/icons8-navigation-96.png", self.observationData["wind"]["deg"] + 180)
        windInfoLayout.addWidget(windDirectionWidget, alignment=Qt.AlignLeft)
        bottomRow.addLayout(windInfoLayout, 1, 0, 1, 1, alignment=Qt.AlignLeft)
        # Humidity Level
        humidityTitleLabel = QLabel("Humidity")
        bottomRow.addWidget(humidityTitleLabel, 0, 2)
        humidityLabel = QLabel(f"<b>{self.observationData['main']['humidity']}%</b>")
        bottomRow.addWidget(humidityLabel, 1, 2)
        # Visibility Level
        visibilityTitleLabel = QLabel("Visibility")
        bottomRow.addWidget(visibilityTitleLabel, 0, 3)
        visibilityValue = self.observationData['visibility'] / 1000 if self.metric else self.observationData['visibility'] / 1609.34
        visibilityLabel = QLabel(f"<b>{int(visibilityValue)} km</b>")
        bottomRow.addWidget(visibilityLabel, 1, 3)
        # Air Pressure
        pressureTitleLabel = QLabel("Pressure")
        bottomRow.addWidget(pressureTitleLabel, 0, 4)
        pressureValue = self.observationData['main']['pressure']
        pressureUnit = 'hPa' if self.metric else 'inHg'
        pressureLabel = QLabel(f"<b>{pressureValue} {pressureUnit}</b>")
        bottomRow.addWidget(pressureLabel, 1, 4)
        observationLayout.addLayout(topRowLayout)
        observationLayout.addLayout(bottomRow)
        # Storing Labels
        self.temperatureLabel = temperatureLabel
        self.weatherDescriptionLabel = weatherDescriptionLabel
        self.feelLikeTemperatureLabel = feelLikeTemperatureLabel
        self.windSpeedLabel = windSpeedLabel
        self.humidityLabel = humidityLabel
        self.visibilityLabel = visibilityLabel
        self.pressureLabel = pressureLabel
        # Frame
        observationFrame.setLayout(observationLayout)

        # AIR POLLUTION LAYOUT ----------------------------------
        airQualityFrame = QFrame()
        airQualityFrame.setFrameShape(QFrame.Box)
        airQualityFrame.setLineWidth(2)
        airQualityFrame.setAutoFillBackground(True)
        airQualityPalette = airQualityFrame.palette()
        airQualityPalette.setColor(airQualityFrame.backgroundRole(), QColor("#96bee0"))
        airQualityFrame.setPalette(airQualityPalette)
        airQualityLabel = QLabel(f"<b><font size='4'>AIR QUALITY </font></b>")
        pollutionLayout = QGridLayout()
        # Carbon Monoxide Level
        coTitleLabel = QLabel('Carbon Monoxide (CO)')
        pollutionLayout.addWidget(coTitleLabel, 0, 0, alignment=Qt.AlignLeft)
        coValue = self.pollutionData['list'][0]['components']['co']
        coLabel = QLabel(f"<b>{coValue} μg/m<sup>3</sup></b>")
        pollutionLayout.addWidget(coLabel, 1, 0, alignment=Qt.AlignLeft)
        # Nitrogen Monoxide Level
        noTitleLabel = QLabel('Nitrogen Monoxide (NO)')
        pollutionLayout.addWidget(noTitleLabel, 0, 1, alignment=Qt.AlignLeft)
        noValue = self.pollutionData['list'][0]['components']['no']
        noLabel = QLabel(f"<b>{noValue} μg/m<sup>3</sup></b>")
        pollutionLayout.addWidget(noLabel, 1, 1, alignment=Qt.AlignLeft)
        # Nitrogen Dioxide Level
        no2TitleLabel = QLabel('Nitrogen Dioxide (NO2)')
        pollutionLayout.addWidget(no2TitleLabel, 2, 0, alignment=Qt.AlignLeft)
        no2Value = self.pollutionData['list'][0]['components']['no2']
        no2Label = QLabel(f"<b>{no2Value} μg/m<sup>3</sup></b>")
        pollutionLayout.addWidget(no2Label, 3, 0, alignment=Qt.AlignLeft)
        # Ozone Level
        o3TitleLabel = QLabel('Ozone (O3)')
        pollutionLayout.addWidget(o3TitleLabel, 2, 1, alignment=Qt.AlignLeft)
        o3Value = self.pollutionData['list'][0]['components']['o3']
        o3Label = QLabel(f"<b>{o3Value} μg/m<sup>3</sup></b>")
        pollutionLayout.addWidget(o3Label, 3, 1, alignment=Qt.AlignLeft)
        # Sulphur Dioxide Level
        so2TitleLabel = QLabel('Sulphur Dioxide (SO2)')
        pollutionLayout.addWidget(so2TitleLabel, 4, 0, alignment=Qt.AlignLeft)
        so2Value = self.pollutionData['list'][0]['components']['so2']
        so2Label = QLabel(f"<b>{so2Value} μg/m<sup>3</sup></b>")
        pollutionLayout.addWidget(so2Label, 5, 0, alignment=Qt.AlignLeft)
        # Sulphur Dioxide Level
        nh3TitleLabel = QLabel('Ammonia (NH3)')
        pollutionLayout.addWidget(nh3TitleLabel, 4, 1, alignment=Qt.AlignLeft)
        nh3Value = self.pollutionData['list'][0]['components']['nh3']
        nh3Label = QLabel(f"<b>{nh3Value} μg/m<sup>3</sup></b>")
        pollutionLayout.addWidget(nh3Label, 5, 1, alignment=Qt.AlignLeft)
        # Storing Labels
        self.coLabel = coLabel
        self.noLabel = noLabel
        self.no2Label = no2Label
        self.o3Label = o3Label
        self.so2Label = so2Label
        self.nh3Label = nh3Label
        # Frame
        airQualityFrame.setLayout(pollutionLayout)

        # MAIN LAYOUT ----------------------------------
        mainLayout = QVBoxLayout()
        mainLayout.addWidget(observationLabel)
        mainLayout.addWidget(observationFrame)
        mainLayout.addWidget(airQualityLabel)
        mainLayout.addWidget(airQualityFrame)
        self.setLayout(mainLayout)
        self.setFixedSize(self.sizeHint())

    def updateWeatherData(self, observationData):
        self.observationData = observationData
        # Update Weather Display
        temperature = int(observationData['main']['temp'])
        temperatureUnit = "°C" if self.metric else "°F"
        temperature_text = f"<b><font size='30'>{temperature}</font><sup><font size='10'>{temperatureUnit}</font></sup></b>"
        self.temperatureLabel.setText(temperature_text)
        weatherDescription = observationData['weather'][0]['description']
        weatherDescription = weatherDescription.capitalize()
        self.weatherDescriptionLabel.setText(f"<b>{weatherDescription}</b>")
        feelLikeTemperature = int(observationData['main']['feels_like'])
        self.feelLikeTemperatureLabel.setText(f'Feels like {feelLikeTemperature}°')
        windSpeed = observationData['wind']['speed'] * 3.6 if self.metric else observationData['wind']['speed']
        self.windSpeedLabel.setText(f"<b>{int(windSpeed):.1f} km/h</b>")
        humidity = observationData['main']['humidity']
        self.humidityLabel.setText(f"<b>{humidity}%</b>")
        visibilityValue = observationData['visibility'] / 1000 if self.metric else observationData['visibility'] / 1609.34
        self.visibilityLabel.setText(f"<b>{int(visibilityValue)} km</b>")
        pressureValue = observationData["main"]["pressure"]
        pressureUnit = "hPa" if self.metric else "inHg"
        self.pressureLabel.setText(f"<b>{pressureValue} {pressureUnit}</b>")
        weatherIconCode = observationData['weather'][0]["icon"]
        weatherIconUrl = f"http://openweathermap.org/img/wn/{weatherIconCode}.png"
        iconImage = requests.get(weatherIconUrl)
        pixmap = QPixmap()
        pixmap.loadFromData(iconImage.content)
        combinedLabelHeight = getTextHeight(20) + getTextHeight(10)
        iconPixmap = pixmap.scaledToHeight(combinedLabelHeight)
        self.iconLabel.setPixmap(iconPixmap)
        windDirection = observationData["wind"]["deg"] + 180
        self.windDirectionWidget.setAngle(windDirection)

    def updateAirQualityData(self, pollutionData):
        self.pollutionData = pollutionData
        # Update Air Quality Display
        coValue = pollutionData['list'][0]['components']['co']
        self.coLabel.setText(f"<b>{coValue} μg/m<sup>3</sup></b>")
        noValue = pollutionData['list'][0]['components']['no']
        self.noLabel.setText(f"<b>{noValue} μg/m<sup>3</sup></b>")
        no2Value = pollutionData['list'][0]['components']['no2']
        self.no2Label.setText(f"<b>{no2Value} μg/m<sup>3</sup></b>")
        o3Value = pollutionData['list'][0]['components']['o3']
        self.o3Label.setText(f"<b>{o3Value} μg/m<sup>3</sup></b>")
        so2Value = pollutionData['list'][0]['components']['so2']
        self.so2Label.setText(f"<b>{so2Value} μg/m<sup>3</sup></b>")
        nh3Value = pollutionData['list'][0]['components']['nh3']
        self.nh3Label.setText(f"<b>{nh3Value} μg/m<sup>3</sup></b>")


class WeatherForecastWidget(QWidget):
    def __init__(self, observationData, forecastData, metric=True):
        super().__init__()
        self.forecastedData = None
        self.forecastInterpolated = None
        self.metric = metric
        self.observationData = observationData
        self.forecastData = list(forecastData)
        self.selectedDate = datetime.now().strftime('%Y-%m-%d')

        mainLayout = QVBoxLayout()
        self.dayWidgets = []
        topLayout = QHBoxLayout()
        now = datetime.now()
        today = now.strftime('%Y-%m-%d')
        for index, dayData in enumerate(self.forecastData):
            if not index:
                newDayData = dayData.copy()
                # Before 18:00
                if newDayData["date"] == today and len(newDayData["time"]) > 2:
                    dayFrame = DayFrame(newDayData)
                # After 18:00
                elif newDayData["date"] == today:
                    times = newDayData["time"] + self.forecastData[index + 1]["time"]
                    data = newDayData['temperatures'] + self.forecastData[index + 1]["temperatures"]
                    icons = newDayData['icons'] + self.forecastData[index + 1]["icons"]
                    newDayData["times"], newDayData['temperatures'], newDayData['icons'] = times, data, icons
                    dayFrame = DayFrame(newDayData, tonight=True)
                # After 21:00
                else:
                    # Add a Tonight Day Widget
                    dayFrame = DayFrame(dayData, date=today, tonight=True)
                    dayFrame.day_clicked.connect(self.updateSelectedDate)
                    self.dayWidgets.append(dayFrame)
                    topLayout.addWidget(dayFrame)
                    # Add the Normal Day Widget
                    dayFrame = DayFrame(dayData)
                dayFrame.dayClicked.connect(self.updateSelectedDate)
                self.dayWidgets.append(dayFrame)
                topLayout.addWidget(dayFrame)

            if index and len(dayData["time"]) == 8:
                dayFrame = DayFrame(dayData)
                dayFrame.dayClicked.connect(self.updateSelectedDate)
                self.dayWidgets.append(dayFrame)
                topLayout.addWidget(dayFrame)

        mainLayout.addLayout(topLayout)
        self.plotView = pg.PlotWidget()
        mainLayout.addWidget(self.plotView)

        self.setLayout(mainLayout)
        self.updateWeatherForecast(self.observationData, self.forecastData)
        self.updatePlot()
        self.setFixedSize(self.sizeHint())

    def updateSelectedDate(self, date):
        self.selectedDate = date
        self.updatePlot()

    def updateWeatherForecast(self, observationData, forecastData):
        self.observationData = observationData
        self.forecastData = forecastData
        now = datetime.utcnow().replace(second=0, microsecond=0)
        temperature = int(self.observationData["main"]["temp"])
        times, data = [now], [temperature]
        for dayData in self.forecastData:
            dt = datetime.strptime(dayData['date'], '%Y-%m-%d')
            times += [dt.replace(hour=int(time.split(':')[0]), minute=int(time.split(':')[1]), second=0, microsecond=0)
                      for time in dayData['time']]
            data += dayData['temperatures']

        self.forecastedData = (np.array(times), np.array(data))
        totalIntervals = int((times[-1] - times[1]).total_seconds() / 60) + 1
        xSmooth = np.linspace(0, (times[-1] - times[0]).total_seconds(), totalIntervals)
        timeInSeconds = np.linspace(0, (times[-1] - times[0]).total_seconds(), len(times))
        xSmoothTime = np.array([times[0] + timedelta(seconds=delta) for delta in xSmooth])
        xSmoothTime = np.array([dt.replace(second=0, microsecond=0) for dt in xSmoothTime])
        xSmoothTimestamps = np.array([dt.timestamp() for dt in xSmoothTime])
        spl = make_interp_spline(timeInSeconds, data, k=3)
        dataSmooth = spl(xSmooth)
        self.forecastInterpolated = (xSmoothTime, dataSmooth)
        self.plotView.clear()

        # Create a single brush for the fill area
        fillBrush = pg.mkBrush(pg.mkColor('#a0c8f0'))
        self.plotView.plot(xSmoothTimestamps, dataSmooth, fillLevel=0, fillBrush=fillBrush)

        # Add annotations and text items
        for x, y in zip(self.forecastedData[0][1:], self.forecastedData[1][1:]):
            self.plotView.plot([x.timestamp()], [y], pen=None, symbol='o', symbolPen='w', symbolBrush='w',
                               symbolSize=10)

            text_item = pg.TextItem(text=str(int(y)), anchor=(0, 1), color=(255, 255, 255))
            self.plotView.addItem(text_item)
            text_item.setPos(x.timestamp(), y)
        y_buffer = 1  # Adjust the buffer as needed
        min_temp_smooth = min(dataSmooth) - y_buffer
        max_temp_smooth = max(dataSmooth) + y_buffer

        # Set y-axis range for the plotView
        self.plotView.setYRange(min_temp_smooth, max_temp_smooth)

    def updatePlot(self):
        for weatherData in self.forecastData:
            if weatherData['date'] == self.selectedDate:
                if self.selectedDate == datetime.now().strftime('%Y-%m-%d'):
                    startTime = self.forecastInterpolated[0][0]
                    finishTime = startTime + timedelta(hours=24)
                else:
                    dateObject = datetime.strptime(weatherData['date'], '%Y-%m-%d')
                    startTime = dateObject.replace(hour=0, minute=0, second=0, microsecond=0)
                    finishTime = startTime + timedelta(hours=24)
                self.plotView.setXRange(startTime.timestamp(), finishTime.timestamp())
                return
        if self.selectedDate == datetime.now().strftime('%Y-%m-%d'):
            startTime = self.forecastInterpolated[0][0]
            finishTime = startTime + timedelta(hours=24)
            self.plotView.setXRange(startTime.timestamp(), finishTime.timestamp())
            return


class DayFrame(QFrame):
    dayClicked = pyqtSignal(str)

    def __init__(self, day_data, parent=None, date=None, tonight=False):
        super().__init__(parent)
        self.setFrameShape(QFrame.Box)
        self.setLineWidth(2)
        self.dayData = day_data
        if date is None:
            self.date = self.dayData["date"]
        else:
            self.date = date
        self.tonight = tonight
        self.dayLayout = QGridLayout()

        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(self.backgroundRole(), QColor("#96bee0"))
        self.setPalette(palette)
        if self.tonight:
            nightIcons = [icon for icon in self.dayData["icons"] if icon.endswith('d')]
            weatherIconCode = Counter(nightIcons).most_common(1)[0][0]
            dateText = 'Tonight'
            maxTemp = '--'
            minTemp = int(min(self.dayData["temperatures"]))
        else:
            weatherIconCode = self.dayData["weather_icon"]
            dt = datetime.strptime(self.dayData["date"], '%Y-%m-%d')
            dateText = dt.strftime('%a %d')
            maxTemp = int(self.dayData["max_temp"])
            minTemp = int(self.dayData["min_temp"])

        # Day Date
        self.dateLabel = QLabel(dateText)
        self.dateLabel.setFont(QFont("Arial", 12, QFont.Bold))
        self.dateLabel.setAlignment(Qt.AlignCenter)
        self.dayLayout.addWidget(self.dateLabel, 0, 0, 1, 3)

        # Weather Icon
        self.weatherIconLabel = QLabel()
        weatherIconUrl = f"http://openweathermap.org/img/wn/{weatherIconCode}.png"
        iconImage = requests.get(weatherIconUrl)
        pixmap = QPixmap()
        pixmap.loadFromData(iconImage.content)
        iconSize = QSize(80, 80)
        pixmap = pixmap.scaled(iconSize, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.weatherIconLabel.setPixmap(pixmap)
        self.dayLayout.addWidget(self.weatherIconLabel, 1, 0, 2, 2)

        # Max Temperature Label
        self.maxTempLabel = QLabel()
        maxTemp_text = f"<b><font size='15'>{maxTemp}°</font></b>"
        self.maxTempLabel.setText(maxTemp_text)
        self.maxTempLabel.setAlignment(Qt.AlignRight)
        self.dayLayout.addWidget(self.maxTempLabel, 1, 2)

        # Min Temperature Label
        self.minTempLabel = QLabel()
        minTempText = f"<b><font size='15'>{minTemp}°</font></b>"
        self.minTempLabel.setText(minTempText)
        self.minTempLabel.setAlignment(Qt.AlignRight)
        self.dayLayout.addWidget(self.minTempLabel, 2, 2)  # Row 2, Column 2

        self.setLayout(self.dayLayout)

    def updateDayData(self, dayData):
        # WEATHER ICON
        self.dayData = dayData
        weatherIconCode = self.dayData["weather_icon"]
        weatherIconUrl = f"http://openweathermap.org/img/wn/{weatherIconCode}.png"
        iconImage = requests.get(weatherIconUrl)
        pixmap = QPixmap()
        pixmap.loadFromData(iconImage.content)
        iconSize = QSize(60, 60)
        pixmap = pixmap.scaled(iconSize, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.weatherIconLabel.setPixmap(pixmap)
        # DATE LABEL
        dt = datetime.strptime(self.dayData["date"], '%Y-%m-%d')
        self.dateLabel.setText(dt.strftime('%a %d'))
        # TEMPERATURES
        minTemp = int(self.dayData["min_temp"])
        minTempText = f"<b><font size='15'>{minTemp}°</font></b>"
        maxTemp = int(self.dayData["max_temp"])
        maxTempText = f"<b><font size='15'>{maxTemp}°</font></b>"
        self.maxTempLabel.setText(maxTempText)
        self.minTempLabel.setText(minTempText)

    def mousePressEvent(self, event):
        self.dayClicked.emit(self.date)


######################## FUNCTIONS ########################
def getForecastWeatherData(city, state, country, api_key, metric=True):
    baseUrl = "http://api.openweathermap.org/data/2.5/forecast"
    params = {
        "q": f"{city},{state},{country}",
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


def getAirPollutionData(city, state, country, api_key):
    location = f"{city}, {state}, {country}"
    print(location)
    g = geocoder.osm(location)
    print(g.latlng)
    if g.ok:
        latitude, longitude = g.latlng
    else:
        print("Error: Unable to retrieve coordinates.")
        return None
    base_url = "http://api.openweathermap.org/data/2.5/air_pollution"
    params = {"lat": latitude, "lon": longitude, "appid": api_key}
    response = requests.get(base_url, params=params)
    data = response.json()
    if data.get("list"):
        return data


def isValidAPIKey(api_key):
    url = f"http://api.openweathermap.org/data/2.5/weather?q=Paris&appid={api_key}"
    response = requests.get(url)
    return response.status_code == 200
