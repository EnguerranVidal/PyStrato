import csv
import os
from datetime import datetime
from serial import Serial
import time

# --------------------- Sources ----------------------- #
from sources.common.parameters import load_settings


class SerialMonitor:
    def __init__(self, port, baud_rate, dataFiles=None, formatFiles=None, header="",
                 dataPath="", formatPath="", rssi=True, output=None):
        #### VARIABLES ####
        self.balloonPins = []
        self.rssi = rssi

        #### FORMATS ####
        # -------------- Initialization
        if formatFiles is None:
            self.formatFiles = []
        self.formatFiles = formatFiles
        if formatPath == "":
            formatPath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../formats")
        self.formatPath = formatPath
        # -------------- Loading Formats
        self.formats = []
        for i in range(len(self.formatFiles)):
            self.formats.append(self.loadFormat(self.formatFiles[i]))

        #### SAVES ####
        if output is None:
            output = "output"
        self.outputFile = output
        if dataFiles is None:
            dataFiles = []
        self.dataFiles = dataFiles
        if dataPath == "":
            dataPath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../data")
        self.dataPath = dataPath
        self.checkSaves()

        #### STARTING SERIAL CONNECTION ####
        self.header = str(header)
        self.header_length = len(header)
        self.port = port
        self.baud_rate = baud_rate
        self.connection = Serial(port, baud_rate)
        with open(self.outputFile, "a") as file:
            file.write("Connected to port " + port + " with baud rate of " + str(baud_rate) + "." + "\n")

        #### LOADING IDs ####
        self.balloonIds = []
        for i in range(len(self.formats)):
            for j in range(len(self.formats[i])):
                if self.formats[i][j][0] == "id":
                    self.balloonIds.append([self.formats[i][j][1], self.formats[i][j][2]])

    def checkSaves(self):
        # --- Creating data directory if non-existent
        if not os.path.exists(self.dataPath):
            os.mkdir(self.dataPath)
        backupPath = os.path.join(self.dataPath, "backups")
        if not os.path.exists(backupPath):
            os.mkdir(backupPath)
        # --- Creating files if non-existent
        for i in range(len(self.dataFiles)):
            saveFilename = self.dataFiles[i]
            if not os.path.exists(os.path.join(self.dataPath, saveFilename)):
                with open(self.outputFile, "a") as file:
                    file.write("Creating the " + saveFilename + " file ..." + "\n")
                with open(os.path.join(self.dataPath, saveFilename), "w", newline='') as file:
                    csv_writer = csv.writer(file)
                    header = self.formatHeader(i)
                    csv_writer.writerow(header)

    def startTracking(self):
        running = True
        self.balloonPins = []
        for i in range(len(self.balloonIds)):
            self.balloonPins.append('none')
        self.checkSaves()
        while running:
            received = str(self.connection.readline())
            packet = received[2:][:-3]
            with open(self.outputFile, "a") as file:
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
        for j in range(len(self.formats[i])):
            if self.formats[i][j][0] == "PIN":
                index = self.formats[i][j][-1]
                pin = int(packet[index:index + self.formats[i][j][1]])
            if self.formats[i][j][0] == "CLOCK":
                index = self.formats[i][j][-1]
                content.append(packet[index:index + len(self.formats[i][j][1])])
            if self.formats[i][j][0] == "VALUE":
                index = self.formats[i][j][-1]
                sign = self.formats[i][j][2]
                digits = self.formats[i][j][3]
                decimals = self.formats[i][j][4]
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
        for j in range(len(self.formats[i])):
            if self.formats[i][j][0] == "ID":
                return self.formats[i][j][1]

    def getPacketLength(self, i):
        line = self.formats[i][-1]
        return line[-1] + line[3] + line[2]

    def loadFormat(self, filename):
        path = os.path.join(self.formatPath, filename)
        with open(path, "r") as file:
            contentFormat = file.readlines()
        for i in range(len(contentFormat)):
            contentFormat[i] = contentFormat[i].split(":")
            for j in range(len(contentFormat[i])):
                contentFormat[i][j] = contentFormat[i][j].rstrip("\n")
            if i > 1:
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
        for j in range(len(self.formats[i])):
            if self.formats[i][j][0] == "CLOCK":
                header.append("Internal Clock")
            if self.formats[i][j][0] == "VALUE":
                title = self.formats[i][j][1].replace('_', ' ')
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
    parameters = load_settings(os.path.join('..', "settings"))
    parameter_formats_files = parameters["FORMAT_FILES"]
    parameter_saving_files = ['KeresData.csv', 'SparcData.csv']
    parameter_port = parameters["SELECTED_PORT"]
    parameter_baud_rate = int(parameters["SELECTED_BAUD"])
    parameter_rssi = parameters["RSSI"]
    parameter_header = parameters["HEADER"]
    parameter_output = parameters["OUTPUT_FILE"]
    ser = SerialMonitor(parameter_port, parameter_baud_rate, dataFiles=parameter_saving_files,
                        formatFiles=parameter_formats_files, header=parameter_header, rssi=parameter_rssi,
                        output=parameter_output)
    ser.startTracking()
