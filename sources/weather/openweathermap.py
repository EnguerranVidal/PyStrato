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
from sources.common.Widgets import ArrowWidget, ScrollableWidget


######################## CLASSES ########################
class ApiRegistrationWidget(QWidget):
    validApiRegistration = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.apiKey = None
        layout = QGridLayout()
        infoLabel = QLabel("This feature works with OpenWeatherMap.")
        infoLabel.setFont(QFont("Arial", 12, QFont.Bold))
        infoLabel.setAlignment(Qt.AlignCenter)
        layout.addWidget(infoLabel, 0, 0, 1, 2)

        apiKeyButton = QPushButton("Enter API Key", self)
        apiKeyButton.setFixedWidth(120)
        apiKeyButton.clicked.connect(self.showAPIKeyDialog)

        createAccountButton = QPushButton("Create Account", self)
        createAccountButton.setFixedWidth(120)
        createAccountButton.clicked.connect(self.createAPIAccount)

        layout.addWidget(apiKeyButton, 1, 0, Qt.AlignRight)
        layout.addWidget(createAccountButton, 1, 1, Qt.AlignLeft)
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
        windDirectionWidget = ArrowWidget("sources/icons/light-theme/icons8-navigation-96.png", self.observationData["wind"]["deg"] + 180)
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
        mainLayout = QGridLayout()
        mainLayout.addWidget(observationLabel, 0, 0, 1, 1)
        mainLayout.addWidget(observationFrame, 1, 0, 1, 1)
        mainLayout.addWidget(airQualityLabel, 0, 1, 1, 1)
        mainLayout.addWidget(airQualityFrame, 1, 1, 1, 1)
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


class WeatherDisplay(QWidget):
    def __init__(self, path, observationData, pollutionData, forecastData, metric=True):
        super().__init__()
        self.currentDir = path
        self.maxTempSmooth, self.minTempSmooth = None, None
        self.forecastedData, self.forecastInterpolated = None, None
        self.metric = metric
        self.observationData = observationData
        self.pollutionData = pollutionData
        self.forecastData = list(forecastData)
        self.selectedDate = datetime.now().strftime('%Y-%m-%d')

        # DAY WIDGETS
        self.dayWidgets = []
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
                    dayFrame.dayClicked.connect(self.updateSelectedDate)
                    self.dayWidgets.append(dayFrame)
                    # Add the Normal Day Widget
                    dayFrame = DayFrame(dayData)
                dayFrame.dayClicked.connect(self.updateSelectedDate)
                self.dayWidgets.append(dayFrame)
            if index and len(dayData["time"]) == 8:
                dayFrame = DayFrame(dayData)
                dayFrame.dayClicked.connect(self.updateSelectedDate)
                self.dayWidgets.append(dayFrame)
        self.scrollableDayWidget = ScrollableWidget(self.currentDir, self.dayWidgets)

        # TEMPERATURE PLOT WIDGET
        self.plotView = pg.PlotWidget()
        self.plotView.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.updateWeatherForecast(self.observationData, self.forecastData)
        self.updatePlot()

        # OBSERVATION AND POLLUTION DISPLAY
        self.observationDisplay = WeatherObservationDisplay(observationData, pollutionData, metric=True)

        # MAIN LAYOUT
        mainLayout = QGridLayout()
        mainLayout.addWidget(self.observationDisplay, 0, 0, 1, 1)
        mainLayout.addWidget(self.scrollableDayWidget, 0, 1, 1, 2)
        mainLayout.addWidget(self.plotView, 1, 0, 1, 3)
        self.setLayout(mainLayout)

    def updateSelectedDate(self, date):
        self.selectedDate = date
        self.updatePlot()

    def updateWeatherForecast(self, observationData, forecastData):
        self.plotView.clear()
        self.observationData = observationData
        self.forecastData = forecastData
        now = self.observationData['dt']
        temperature = int(self.observationData["main"]["temp"])
        times, data = [now], [temperature]
        for dayData in self.forecastData:
            times += [int(dt.timestamp()) for dt in dayData['time']]
            data += dayData['temperatures']
        sortedIndices = np.argsort(times)
        times, data = np.array(times)[sortedIndices], np.array(data)[sortedIndices]
        self.forecastedData = (times, data)
        totalIntervals = int((times[-1] - times[1]) / 60)
        xSmooth = np.linspace(times[1], times[-1], totalIntervals)
        spl = make_interp_spline(times, data, k=3)
        dataSmooth = spl(xSmooth)
        self.forecastInterpolated = (xSmooth, dataSmooth)
        self.plotView.clear()

        # FILL AREA BRUSH
        fillBrush = pg.mkBrush(pg.mkColor('#a0c8f0'))
        self.plotView.plot(xSmooth, dataSmooth, fillLevel=0, fillBrush=fillBrush)

        # TEMPERATURE ANNOTATIONS
        for x, y in zip(self.forecastedData[0][1:], self.forecastedData[1][1:]):
            self.plotView.plot([x], [y], pen=None, symbol='o', symbolPen='w', symbolBrush='w', symbolSize=10)
            textItem = pg.TextItem(text=str(int(y)), anchor=(0.5, 1.2), color=(255, 255, 255))
            self.plotView.addItem(textItem)
            textItem.setPos(x, y)

        # X-AXIS DATETIMES
        xAxis = pg.AxisItem(orientation='bottom')
        self.plotView.setAxisItems({'bottom': xAxis})
        xTimes = oddFullHoursBetween(now, xSmooth[-1])
        xTimes = [(dt.timestamp(), dt.strftime('%H:%M')) for dt in xTimes]
        xAxis.setTicks([xTimes])

        # Y-AXIS RANGE
        self.minTempSmooth = min(dataSmooth) - 1
        self.maxTempSmooth = max(dataSmooth) + 1
        self.plotView.setYRange(self.minTempSmooth, self.maxTempSmooth)
        self.plotView.getAxis('left').setStyle(showValues=False)
        self.plotView.getAxis('left').setTicks([])
        self.plotView.setMouseEnabled(y=False)

        # MIDNIGHT LINES AND DAY LABELS
        midnights = midnightsBetween(now, xSmooth[-1])
        for midnight in midnights:
            midnightLine = pg.InfiniteLine(midnight.timestamp(), angle=90, pen=(255, 255, 255, 50))
            self.plotView.addItem(midnightLine)

            # Add day label
            dayLabel = midnight.strftime('%a %d')
            textItem = pg.TextItem(text=dayLabel, anchor=(0.5, 0.5), color=(255, 255, 255, 200))
            textItem.setPos(midnight.timestamp(), self.maxTempSmooth)
            self.plotView.addItem(textItem)

    def updatePlot(self):
        self.plotView.setYRange(self.minTempSmooth, self.maxTempSmooth)
        for weatherData in self.forecastData:
            if weatherData['date'] == self.selectedDate:
                if self.selectedDate == datetime.now().strftime('%Y-%m-%d'):
                    startTime = self.forecastInterpolated[0][0]
                    finishTime = startTime + 3600 * 24
                    self.plotView.setXRange(startTime, finishTime)
                else:
                    dateObject = datetime.strptime(weatherData['date'], '%Y-%m-%d')
                    startTime = dateObject.replace(hour=0, minute=0, second=0, microsecond=0).timestamp()
                    finishTime = startTime + 3600 * 24
                    self.plotView.setXRange(startTime, finishTime)
                return
        if self.selectedDate == datetime.now().strftime('%Y-%m-%d'):
            startTime = self.forecastInterpolated[0][0]
            finishTime = startTime + 3600 * 24
            self.plotView.setXRange(startTime, finishTime)
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
        iconSize = QSize(40, 40)
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
def get5Day3HoursForecastWeatherData(city, state, country, apiKey, metric=True):
    baseUrl = "http://api.openweathermap.org/data/2.5/forecast"
    location = f"{city},{state},{country}"
    params = {
        "q": location,
        "appid": apiKey,
        "units": "metric" if metric else "imperial"
    }
    response = requests.get(baseUrl, params=params)
    if response.status_code == 200:
        data = response.json()
        weatherData = {}
        for singleForecast in data["list"]:
            date = datetime.utcfromtimestamp(singleForecast["dt"]).strftime('%Y-%m-%d')
            time = datetime.utcfromtimestamp(singleForecast["dt"])
            weatherIcon = singleForecast["weather"][0]["icon"]
            temperature = singleForecast["main"]["temp"]
            rainProbability = singleForecast.get("rain", {}).get("3h", 0)
            if date not in weatherData:
                weatherData[date] = {
                    "date": date,
                    "time": [time],
                    "weather_icon": [weatherIcon],
                    "max_temp": temperature,
                    "min_temp": temperature,
                    "temperatures": [temperature],
                    "rain_probabilities": [rainProbability],
                    "icons": [weatherIcon]
                }
            else:
                if temperature > weatherData[date]["max_temp"]:
                    weatherData[date]["max_temp"] = temperature
                if temperature < weatherData[date]["min_temp"]:
                    weatherData[date]["min_temp"] = temperature
                weatherData[date]["weather_icon"].append(weatherIcon)
                weatherData[date]["icons"].append(weatherIcon)
                weatherData[date]["time"].append(time)
                weatherData[date]["temperatures"].append(temperature)
                weatherData[date]["rain_probabilities"].append(rainProbability)

        for date, dayData in weatherData.items():
            day_icons = [icon for icon in dayData["weather_icon"] if icon.endswith('d')]
            if day_icons:
                mostCommonIcon = Counter(day_icons).most_common(1)[0][0]
            else:
                target = datetime.strptime("12:00", '%H:%M').time()
                timeDiffs = [abs((dateTime - datetime.combine(datetime.today(), target)).seconds) for dateTime in dayData["time"]]
                closestTimeIndex = timeDiffs.index(min(timeDiffs))
                mostCommonIcon = dayData["weather_icon"][closestTimeIndex]
            weatherData[date]["weather_icon"] = mostCommonIcon
        # Remove days with incomplete forecasts (except today)
        return weatherData.values()
    else:
        print("Error:", response.status_code)
        return None


def getObservationWeatherData(city, state, country, apiKey, metric=True):
    base_url = "http://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": f"{city},{state},{country}",
        "appid": apiKey,
        "units": "metric" if metric else "imperial"
    }
    response = requests.get(base_url, params=params)
    data = response.json()
    if data.get("main") and data.get("weather") and data.get("wind"):
        return data


def getAirPollutionData(city, state, country, apiKey):
    location = f"{city}, {state}, {country}"
    g = geocoder.osm(location)
    if g.ok:
        latitude, longitude = g.latlng
    else:
        print("Error: Unable to retrieve coordinates.")
        return None
    base_url = "http://api.openweathermap.org/data/2.5/air_pollution"
    params = {"lat": latitude, "lon": longitude, "appid": apiKey}
    response = requests.get(base_url, params=params)
    data = response.json()
    if data.get("list"):
        return data


def getLocationInfo(latitude, longitude, apiKey):
    baseUrl = 'http://api.openweathermap.org/data/2.5/weather'
    params = {'lat': latitude, 'lon': longitude, 'appid': apiKey}
    response = requests.get(baseUrl, params=params)
    if response.status_code == 200:
        data = response.json()
        cityName = data['name']
        state = data.get('sys', {}).get('state', '')
        country = data['sys']['country']

        return cityName, state, country
    else:
        print(f"Error: {response.status_code}")
        return None


def oddFullHoursBetween(startTimestamp, endTimestamp):
    startDateTime = datetime.utcfromtimestamp(startTimestamp)
    endDateTime = datetime.utcfromtimestamp(endTimestamp)
    startDateTime -= timedelta(minutes=startDateTime.minute, seconds=startDateTime.second, microseconds=startDateTime.microsecond)
    endDateTime += timedelta(hours=1, minutes=-endDateTime.minute, seconds=-endDateTime.second, microseconds=-endDateTime.microsecond)
    if startDateTime.hour % 2 == 0:
        startDateTime += timedelta(hours=1)
    currentDateTime = startDateTime
    result = []
    while currentDateTime < endDateTime:
        result.append(currentDateTime)
        currentDateTime += timedelta(hours=2)
    return result


def midnightsBetween(startTimestamp, endTimestamp, includeBorders=True):
    startDateTime = datetime.utcfromtimestamp(startTimestamp)
    endDateTime = datetime.utcfromtimestamp(endTimestamp)
    startDateTime -= timedelta(days=startDateTime.day, hours=startDateTime.hour, minutes=startDateTime.minute, seconds=startDateTime.second, microseconds=startDateTime.microsecond)
    endDateTime += timedelta(days=1, hours=-endDateTime.hour, minutes=-endDateTime.minute, seconds=-endDateTime.second, microseconds=-endDateTime.microsecond)
    if not includeBorders:
        startDateTime += timedelta(days=1)
        endDateTime -= timedelta(days=1)
    currentDateTime = startDateTime
    result = []
    while currentDateTime < endDateTime:
        result.append(currentDateTime)
        currentDateTime += timedelta(days=1)
    return result


def isValidAPIKey(api_key):
    url = f"http://api.openweathermap.org/data/2.5/weather?q=Paris&appid={api_key}"
    response = requests.get(url)
    return response.status_code == 200
