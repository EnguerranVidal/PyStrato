######################## IMPORTS ########################
import os

import requests
# ------------------- PyQt Modules -------------------- #
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

# --------------------- Sources ----------------------- #
from sources.common.FileHandling import load_settings, save_settings, nameGiving


######################## CLASSES ########################
class WeatherWidget(QWidget):
    def __init__(self, path: str):
        super().__init__()
        self.currentDir = path
        self.settings = load_settings('settings')
        self.apiKey = self.settings['WEATHER_API_KEY']

        self.initUI()

    def initUI(self):
        layout = QGridLayout()

        if not self.apiKey:
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

        else:
            pass

        self.setLayout(layout)

    def clear_layout(self):
        for i in reversed(range(self.layout().count())):
            widget = self.layout().itemAt(i).widget()
            if widget is not None:
                widget.deleteLater()

    def showAPIKeyDialog(self):
        dialog = ApiKeyDialog(self)
        result = dialog.exec_()
        if result == QDialog.Accepted:
            new_api_key = dialog.apiKeyLineEdit.text()
            if self.isValidAPIKey(new_api_key):
                self.apiKey = new_api_key
                self.settings['WEATHER_API_KEY'] = self.apiKey
                save_settings(self.settings, 'settings')
                self.clear_layout()
                self.initUI()
            else:
                QMessageBox.critical(self, "Invalid API Key",
                                     "The entered API key is invalid. Please enter a valid API key.")

    @staticmethod
    def isValidAPIKey(api_key):
        url = f"http://api.openweathermap.org/data/2.5/version?appid={api_key}"
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