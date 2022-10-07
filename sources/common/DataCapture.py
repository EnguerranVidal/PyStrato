from PyQt5.QtCore import QObject, pyqtSignal
import os
import time

from sources.common.parameters import load_settings, load_format, csvRowCount, retrieveCSVData, voidCSV


class DataWorker(QObject):
    finished = pyqtSignal()
    progress = pyqtSignal(list)

    def __init__(self, path):
        super().__init__()
        self._active = False
        self.formats = None
        self.settings = None
        self.start_date = ""
        self.dataFiles = []
        self.rowCounts = []
        self.currentDir = path
        self.dataDir = os.path.join(self.currentDir, 'data')
        self.formatDir = os.path.join(self.currentDir, 'formats')

    def interrupt(self):
        self._active = False

    def run(self):
        self.dataFiles = []
        self.settings = load_settings('settings')
        # Getting Data Files
        self.formats = {}
        for i in range(len(self.settings['FORMAT_FILES'])):
            name, formatLine = load_format(os.path.join(self.formatDir, self.settings['FORMAT_FILES'][i]))
            self.formats[name] = formatLine
            self.dataFiles.append(os.path.join(self.dataDir, formatLine['FILE']))
        self.rowCounts = [csvRowCount(dataFile) for dataFile in self.dataFiles]
        self._active = True
        while self._active:
            content = []
            time.sleep(1)
            for i in range(len(self.dataFiles)):
                name = list(self.formats.keys())[i]
                dataUNIX, dataValues = retrieveCSVData(self.dataFiles[i], self.formats[name], self.start_date)
                content.append([dataUNIX, dataValues])
            self.progress.emit(content)
        self.finished.emit()


