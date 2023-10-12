######################## IMPORTS ########################
import requests

# ------------------- PyQt Modules -------------------- #
from PyQt5.QtGui import *

# --------------------- Sources ----------------------- #


######################## CLASSES ########################

def getTextHeight(fontSize):
    font = QFont()
    font.setPointSize(fontSize)
    fontMetrics = QFontMetrics(font)
    textHeight = fontMetrics.height()
    return textHeight


def isInternetAvailable(url="http://www.google.com", timeout=5):
    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException:
        pass
    return False
