######################## IMPORTS ########################
import os

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
        self.api_key = self.settings['WEATHER_API_KEY']

        self.init_ui()

    def init_ui(self):
        layout = QGridLayout()

        if not self.api_key:
            info_label = QLabel("This feature works with OpenWeatherMap.")
            info_label.setFont(QFont("Arial", 12, QFont.Bold))
            info_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(info_label, 0, 0, 1, 2)

            api_key_button = QPushButton("Enter API Key")
            api_key_button.clicked.connect(self.show_api_key_dialog)

            create_account_button = QPushButton("Create Account")
            create_account_button.clicked.connect(self.create_openweathermap_account)

            button_layout = QHBoxLayout()
            button_layout.addWidget(api_key_button)
            button_layout.addWidget(create_account_button)

            layout.addLayout(button_layout, 1, 0, 1, 2)

        else:
            pass

        self.setLayout(layout)

    def show_api_key_dialog(self):
        dialog = ApiKeyDialog(self)
        result = dialog.exec_()
        if result == QDialog.Accepted:
            self.api_key = dialog.apiKeyLineEdit.text()
            self.settings['WEATHER_API_KEY'] = self.api_key
            save_settings(self.settings, 'settings')

    @staticmethod
    def create_openweathermap_account():
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