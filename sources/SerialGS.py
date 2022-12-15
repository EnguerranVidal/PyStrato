import csv
import os
from datetime import datetime
from PyQt5.QtCore import pyqtSignal, QThread

from ecom.database import CommunicationDatabase
from ecom.parser import TelemetryParser
from serial import Serial
import time

# --------------------- Sources ----------------------- #
from sources.common.FileHandling import load_settings, load_format
from sources.common.balloondata import BalloonPackageDatabase


class SerialMonitor(QThread):
    progress = pyqtSignal(dict)
    output = pyqtSignal(str)

    def __init__(self, path):
        super().__init__()
        self.currentDir = path
        self._active = False
        self.settings = load_settings('settings')
        self.dataDir = os.path.join(self.currentDir, 'data')
        self.formatDir = os.path.join(self.currentDir, 'databases')

    def run(self):
        connection = Serial(self.settings['SELECTED_PORT'], self.settings['SELECTED_BAUD'], timeout=1)
        self.output.emit("Connected to port " + self.settings['SELECTED_PORT'] + " with baud rate of " +
                         self.settings['SELECTED_BAUD'] + ".")
        parsers = {}
        for path in self.settings['FORMAT_FILES']:
            path = os.path.join(self.currentDir, 'databases', path)
            if os.path.isdir(path):
                name, database = os.path.basename(path), BalloonPackageDatabase(path)
                parsers[name] = TelemetryParser(database)
            else:
                name, _ = load_format(path)
                parsers[name] = OldParser(self.output)
        self._active = True
        while self._active:
            received = connection.read(connection.inWaiting() or 1)
            for parserName, parser in parsers.items():
                telemetries = parser.parse(received, errorHandler=lambda error: print(error))
                if telemetries:
                    for telemetry in telemetries:
                        if isinstance(telemetry, dict):
                            content = telemetry
                            telemetryType = 'Default'
                        else:
                            self.output.emit(str(telemetry))
                            content = telemetry.data
                            telemetryType = telemetry.type.name
                        self.progress.emit({'parser': parserName, 'type': telemetryType, 'data': content})
        self.finished.emit()

    def interrupt(self):
        self._active = False


class OldParser:
    def __init__(self, outputSignal):
        super().__init__()
        self._output = outputSignal
        self._buffer = ''
        self.formatDir = 'databases'
        self.dataDir = 'data'
        self.settings = load_settings('settings')
        self.balloonFormats = {}
        self.balloonNames = []
        for fileName in self.settings['FORMAT_FILES']:
            name, packetFormat = load_format(os.path.join(self.formatDir, fileName))
            self.balloonNames.append(name)
            self.balloonFormats[name] = packetFormat
        self.balloonPins = []
        self.dataFiles = [os.path.join(self.dataDir, self.balloonFormats[name]['FILE'])
                          for name in list(self.balloonFormats.keys())]
        self.checkSaves()
        self.balloonPins = ['NONE'] * len(self.dataFiles)
        self.settings = load_settings('settings')
        #### LOADING IDs ####
        self.balloonIds = [self.balloonFormats[name]['ID'] for name in list(self.balloonFormats.keys())]

    def parse(self, buffer, errorHandler=None):
        self.checkSaves()
        self._buffer += str(buffer)[2:][:-1]
        lines = self._buffer.split('\\n')
        self._buffer = lines.pop()
        packages = []
        for packet in lines:
            self._output.emit(datetime.now().strftime("%H:%M:%S") + " -> " + packet)
            # Verifying for header
            if packet[0:len(self.settings['HEADER'])] == self.settings['HEADER']:
                for i in range(len(self.balloonIds)):
                    # Knowing which balloon
                    id_index = len(self.balloonIds[i]) + len(self.settings['HEADER']) - 1
                    if packet[id_index] == self.balloonIds[i][0]:
                        payload = packet[len(self.settings['HEADER']):].split()
                        if len(payload[0]) == self.getPacketLength(i):
                            content, pin = self.disassemblePacket(i, packet)
                            if pin != self.balloonPins[i]:
                                self.saveCSV(i, content)
                                self.balloonPins[i] = pin
                                packages.append({self.formatHeader(i): value for i, value in enumerate(content)})
        return packages

    def checkSaves(self):
        # --- Creating data directory if non-existent
        if not os.path.exists(self.dataDir):
            os.mkdir(self.dataDir)
        backupPath = os.path.join(self.dataDir, 'backups')
        if not os.path.exists(backupPath):
            os.mkdir(backupPath)
        # --- Creating files if non-existent
        names = list(self.balloonFormats.keys())
        for i in range(len(self.dataFiles)):
            saveFilename = self.dataFiles[i]
            if not os.path.exists(saveFilename):
                self._output.emit('Creating the ' + saveFilename + ' file ...')
                with open(saveFilename, "w", newline='') as file:
                    csv_writer = csv.writer(file)
                    header = self.formatHeader(names[i])
                    csv_writer.writerow(header)

    def formatHeader(self, i):
        header = ['Reception Time', 'UNIX']
        keys = list(self.balloonFormats[i].keys())
        if 'CLOCK' in keys:
            header.append('Internal Clock')
        if 'DATA' in keys:
            names = [name.replace('_', ' ') for name in list(self.balloonFormats[i]['DATA'].keys())]
            header += names
        header.append('RSSI')
        return header

    def disassemblePacket(self, i, packet):
        packet = packet[len(self.settings['HEADER']):]
        content = [datetime.now().strftime("%Y-%m-%d %H:%M:%S"), int(time.time())]
        name = list(self.balloonFormats.keys())[i]
        balloonFormat = self.balloonFormats[name]
        mainKeys = list(balloonFormat.keys())
        index = len(balloonFormat['ID'])
        for j in range(len(mainKeys)):
            if mainKeys[j] == 'PIN':
                pin = int(packet[index:index + int(balloonFormat['PIN'])])
                index += int(balloonFormat['PIN'])
            if mainKeys[j] == 'CLOCK':
                content.append(packet[index:index + len(balloonFormat['CLOCK'].rstrip('\n'))])
                index += len(balloonFormat['CLOCK'].rstrip('\n'))
            if mainKeys[j] == 'DATA':
                valueKeys = list(balloonFormat['DATA'].keys())
                for k in range(len(valueKeys)):
                    dataValue = balloonFormat['DATA'][valueKeys[k]]
                    sign = int(dataValue['SIGN'])
                    digits = int(dataValue['TOTAL'])
                    decimals = int(dataValue['FLOAT'])
                    value = packet[index:index + sign + digits]
                    index += sign + digits
                    if self.verifyMessageData(str(value), sign):
                        content.append(int(value) / 10 ** decimals)
                    else:
                        content.append('')
        if bool(int(self.settings['RSSI'])):
            data = packet.split()
            content.append(int(data[-1].rstrip("\n")))
        else:
            content.append('')
        return content, pin

    def getPacketLength(self, i):
        name = list(self.balloonFormats.keys())[i]
        balloonFormat = self.balloonFormats[name]
        count = len(balloonFormat['ID']) + int(balloonFormat['PIN'])
        if balloonFormat['CLOCK'] is not None:
            count += len(balloonFormat['CLOCK'].rstrip('\n'))
        values = [balloonFormat['DATA'][value] for value in list(balloonFormat['DATA'].keys())]
        for value in values:
            count += int(value['SIGN']) + int(value['TOTAL'])
        return count

    @staticmethod
    def verifyMessageData(string, sign):
        if not string[sign:].replace('.', '', 1).isdigit():
            return False
        else:
            return True

    def saveCSV(self, i, content):
        for j in range(len(content)):
            content[j] = str(content[j])
        saveFilename = self.dataFiles[i]
        with open(saveFilename, "a", newline='') as file:
            csvWriter = csv.writer(file)
            csvWriter.writerow(content)


if __name__ == '__main__':
    monitor = SerialMonitor()
    monitor.startTracking()
