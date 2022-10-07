import csv
import os
from datetime import datetime
from serial import Serial
import time

# --------------------- Sources ----------------------- #
from sources.common.parameters import load_settings, load_format


class SerialMonitor:
    def __init__(self):
        self.formatDir = 'formats'
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
        self.connection = Serial(self.settings['SELECTED_PORT'], self.settings['SELECTED_BAUD'])
        with open(self.settings['OUTPUT_FILE'], "a") as file:
            file.write("Connected to port " + self.settings['SELECTED_PORT'] + " with baud rate of " +
                       self.settings['SELECTED_BAUD'] + "." + "\n")
        #### LOADING IDs ####
        self.balloonIds = [self.balloonFormats[name]['ID'] for name in list(self.balloonFormats.keys())]

    def checkSaves(self):
        # --- Creating data directory if non-existent
        if not os.path.exists(self.dataDir):
            os.mkdir(self.dataDir)
        backupPath = os.path.join(self.dataDir, "backups")
        if not os.path.exists(backupPath):
            os.mkdir(backupPath)
        # --- Creating files if non-existent
        names = list(self.balloonFormats.keys())
        for i in range(len(self.dataFiles)):
            saveFilename = self.dataFiles[i]
            if not os.path.exists(os.path.join(self.dataDir, saveFilename)):
                with open(self.settings['OUTPUT_FILE'], "a") as file:
                    file.write("Creating the " + saveFilename + " file ..." + "\n")
                with open(saveFilename, "w", newline='') as file:
                    csv_writer = csv.writer(file)
                    header = self.formatHeader(names[i])
                    csv_writer.writerow(header)

    def startTracking(self):
        running = True
        self.balloonPins = ['NONE'] * len(self.dataFiles)
        self.checkSaves()
        while running:
            received = str(self.connection.readline())
            packet = received[2:][:-3]
            with open(self.settings['OUTPUT_FILE'], "a") as file:
                file.write(datetime.now().strftime("%H:%M:%S") + " -> " + packet + '\n')
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
                                print(content)
                                self.saveCSV(i, content)
                                self.balloonPins[i] = pin

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

    def formatHeader(self, i):
        header = ["Reception Time", "UNIX"]
        keys = list(self.balloonFormats[i].keys())
        if 'CLOCK' in keys:
            header.append("Internal Clock")
        if 'DATA' in keys:
            names = [name.replace('_', ' ') for name in list(self.balloonFormats[i]['DATA'].keys())]
            header += names
        header.append("RSSI")
        return header

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
        with open(os.path.join(saveFilename), "a", newline='') as file:
            csvWriter = csv.writer(file)
            csvWriter.writerow(content)


if __name__ == '__main__':
    monitor = SerialMonitor()
    monitor.startTracking()
