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
            print(packetFormat)
        self.balloonPins = []
        self.dataFiles = [os.path.join(self.dataDir, self.balloonFormats[name]['FILE'])
                          for name in list(self.balloonFormats.keys())]

        self.checkSaves()
        self.connection = Serial(self.settings['SELECTED_PORT'], self.settings['SELECTED_BAUD'])
        with open(self.outputFile, "a") as file:
            file.write("Connected to port " + self.settings['SELECTED_PORT'] + " with baud rate of " +
                       self.settings['SELECTED_BAUD'] + "." + "\n")
        #### LOADING IDs ####
        self.balloonIds = [self.balloonFormats[name]['FILE'] for name in list(self.balloonFormats.keys())]

    def checkSaves(self):
        # --- Creating data directory if non-existent
        if not os.path.exists(self.dataDir):
            os.mkdir(self.dataDir)
        backupPath = os.path.join(self.dataDir, "backups")
        if not os.path.exists(backupPath):
            os.mkdir(backupPath)
        # --- Creating files if non-existent
        for i in range(len(self.dataFiles)):
            saveFilename = self.dataFiles[i]
            if not os.path.exists(os.path.join(self.dataDir, saveFilename)):
                with open(self.settings['OUTPUT_FILE'], "a") as file:
                    file.write("Creating the " + saveFilename + " file ..." + "\n")
                with open(os.path.join(self.dataDir, saveFilename), "w", newline='') as file:
                    csv_writer = csv.writer(file)
                    header = self.formatHeader(i)
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
            if packet[0:len(self.header)] == self.header:
                for i in range(len(self.balloonIds)):
                    # Knowing which balloon
                    id_index = self.balloonIds[i][1] + self.header_length
                    if packet[id_index] == self.balloonIds[i][0]:
                        payload = packet[len(self.header):].split()
                        if len(payload[0]) == self.getPacketLength(i):
                            content, pin = self.disassemblePacket(i, packet)
                            if pin != self.balloonPins[i]:
                                self.saveCSV(i, content)
                                self.balloonPins[i] = pin

    def disassemblePacket(self, i, packet):
        packet = packet[len(self.header):]
        content = [datetime.now().strftime("%Y-%m-%d %H:%M:%S"), int(time.time())]
        for j in range(len(self.balloonFormats[i])):
            if self.balloonFormats[i][j][0] == "PIN":
                index = self.balloonFormats[i][j][-1]
                pin = int(packet[index:index + self.balloonFormats[i][j][1]])
            if self.balloonFormats[i][j][0] == "CLOCK":
                index = self.balloonFormats[i][j][-1]
                content.append(packet[index:index + len(self.balloonFormats[i][j][1])])
            if self.balloonFormats[i][j][0] == "VALUE":
                index = self.balloonFormats[i][j][-1]
                sign = self.balloonFormats[i][j][2]
                digits = self.balloonFormats[i][j][3]
                decimals = self.balloonFormats[i][j][4]
                value = packet[index:index + sign + digits]
                if self.verifyMessageData(str(value), sign):
                    content.append(int(value) / 10 ** decimals)
                else:
                    content.append('')
        if self.rssi:
            data = packet.split()
            content.append(int(data[-1].rstrip("\n")))
        else:
            content.append('')
        return content, pin

    def getFormatId(self, i):
        for j in range(len(self.balloonFormats[i])):
            if self.balloonFormats[i][j][0] == "ID":
                return self.balloonFormats[i][j][1]

    def getPacketLength(self, i):
        line = self.balloonFormats[i][-1]
        return line[-1] + line[3] + line[2]

    def loadFormat(self, filename):
        path = os.path.join(self.formatPath, filename)
        with open(path, "r") as file:
            contentFormat = file.readlines()
        for i in range(len(contentFormat)):
            contentFormat[i] = contentFormat[i].split(":")
            for j in range(len(contentFormat[i])):
                contentFormat[i][j] = contentFormat[i][j].rstrip("\n")
            if i > 2:
                contentFormat[i][-1] = int(contentFormat[i][-1])
            if contentFormat[i][0] == "VALUE":
                contentFormat[i][2] = int(contentFormat[i][2])
                contentFormat[i][3] = int(contentFormat[i][3])
                contentFormat[i][4] = int(contentFormat[i][4])
            if contentFormat[i][0] == "PIN":
                contentFormat[i][1] = int(contentFormat[i][1])
        print(contentFormat)
        return contentFormat

    def formatHeader(self, i):
        header = ["Reception Time", "UNIX"]
        for j in range(len(self.balloonFormats[i])):
            if self.balloonFormats[i][j][0] == "CLOCK":
                header.append("Internal Clock")
            if self.balloonFormats[i][j][0] == "VALUE":
                title = self.balloonFormats[i][j][1].replace('_', ' ')
                header.append(title)
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
        with open(os.path.join(self.dataPath, saveFilename), "a", newline='') as file:
            csvWriter = csv.writer(file)
            csvWriter.writerow(content)


if __name__ == '__main__':
    monitor = SerialMonitor()
    monitor.startTracking()
