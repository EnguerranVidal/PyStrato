import csv
import os
from datetime import datetime
from serial import Serial
import time


class Serial_Monitor:
    def __init__(self, port, baud_rate, data_files=None, format_files=None, header="",
                 data_path="", format_path="", rssi=True, output=None):
        #### VARIABLES ####
        self.balloon_pins = []
        self.rssi = rssi

        #### FORMATS ####
        # -------------- Initialization
        if format_files is None:
            self.format_files = []
        self.format_files = format_files
        if format_path == "":
            format_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../formats")
        self.format_path = format_path
        # -------------- Loading Formats
        self.formats = []
        for i in range(len(self.format_files)):
            self.formats.append(self.load_format(self.format_files[i]))

        #### SAVES ####
        if output is None:
            output = "output"
        self.output_file = output
        if data_files is None:
            data_files = []
        self.data_files = data_files
        if data_path == "":
            data_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../data")
        self.data_path = data_path
        self.check_saves()

        #### STARTING SERIAL CONNECTION ####
        self.header = str(header)
        self.header_length = len(header)
        self.port = port
        self.baud_rate = baud_rate
        self.connection = Serial(port, baud_rate)
        with open(self.output_file, "a") as file:
            file.write("Connected to port " + port + " with baud rate of " + str(baud_rate) + "." + "\n")

        #### LOADING IDs ####
        self.balloon_ids = []
        for i in range(len(self.formats)):
            for j in range(len(self.formats[i])):
                if self.formats[i][j][0] == "id":
                    self.balloon_ids.append([self.formats[i][j][1], self.formats[i][j][2]])

    def check_saves(self):
        # --- Creating data directory if non-existent
        if not os.path.exists(self.data_path):
            os.mkdir(self.data_path)
        backup_path = os.path.join(self.data_path, "backups")
        if not os.path.exists(backup_path):
            os.mkdir(backup_path)
        # --- Creating files if non-existent
        for i in range(len(self.data_files)):
            save_filename = self.data_files[i]
            if not os.path.exists(os.path.join(self.data_path, save_filename)):
                with open(self.output_file, "a") as file:
                    file.write("Creating the " + save_filename + " file ..." + "\n")
                with open(os.path.join(self.data_path, save_filename), "w", newline='') as file:
                    csv_writer = csv.writer(file)
                    header = self.format_header(i)
                    csv_writer.writerow(header)

    def start_tracking(self):
        running = True
        self.balloon_pins = []
        for i in range(len(self.balloon_ids)):
            self.balloon_pins.append('none')
        self.check_saves()
        while running:
            received = str(self.connection.readline())
            packet = received[2:][:-3]
            with open(self.output_file, "a") as file:
                file.write(datetime.now().strftime("%H:%M:%S") + " -> " + packet + '\n')
            # Verifying for header
            if packet[0:len(self.header)] == self.header:
                for i in range(len(self.balloon_ids)):
                    # Knowing which balloon
                    id_index = self.balloon_ids[i][1] + self.header_length
                    if packet[id_index] == self.balloon_ids[i][0]:
                        payload = packet[len(self.header):].split()
                        if len(payload[0]) == self.get_packet_length(i):
                            content, pin = self.disassemble_packet(i, packet)
                            if pin != self.balloon_pins[i]:
                                self.save_CSV(i, content)
                                self.balloon_pins[i] = pin

    def disassemble_packet(self, i, packet):
        packet = packet[len(self.header):]
        content = [datetime.now().strftime("%Y-%m-%d %H:%M:%S"), int(time.time())]
        for j in range(len(self.formats[i])):
            if self.formats[i][j][0] == "pin":
                index = self.formats[i][j][-1]
                pin = int(packet[index:index + self.formats[i][j][1]])
            if self.formats[i][j][0] == "clock":
                index = self.formats[i][j][-1]
                content.append(packet[index:index + len(self.formats[i][j][1])])
            if self.formats[i][j][0] == "value":
                index = self.formats[i][j][-1]
                sign = self.formats[i][j][2]
                digits = self.formats[i][j][3]
                decimals = self.formats[i][j][4]
                value = packet[index:index + sign + digits]
                if self.verify_message_data(str(value), sign):
                    content.append(int(value) / 10 ** decimals)
                else:
                    content.append('')
        if self.rssi:
            data = packet.split()
            content.append(int(data[-1].rstrip("\n")))
        else:
            content.append('')
        return content, pin

    def get_format_id(self, i):
        for j in range(len(self.formats[i])):
            if self.formats[i][j][0] == "id":
                return self.formats[i][j][1]

    def get_packet_length(self, i):
        line = self.formats[i][-1]
        return line[-1] + line[3] + line[2]

    def load_format(self, filename):
        path = os.path.join(self.format_path, filename)
        with open(path, "r") as file:
            content_format = file.readlines()
        for i in range(len(content_format)):
            content_format[i] = content_format[i].split(":")
            for j in range(len(content_format[i])):
                content_format[i][j] = content_format[i][j].rstrip("\n")
            if i != 0:
                content_format[i][-1] = int(content_format[i][-1])
            if content_format[i][0] == "value":
                content_format[i][2] = int(content_format[i][2])
                content_format[i][3] = int(content_format[i][3])
                content_format[i][4] = int(content_format[i][4])
            if content_format[i][0] == "pin":
                content_format[i][1] = int(content_format[i][1])
        return content_format

    def format_header(self, i):
        header = ["Reception Time", "UNIX"]
        for j in range(len(self.formats[i])):
            if self.formats[i][j][0] == "clock":
                header.append("Internal Clock")
            if self.formats[i][j][0] == "value":
                title = self.formats[i][j][1].replace('_', ' ')
                header.append(title)
        header.append("RSSI")
        return header

    @staticmethod
    def verify_message_data(string, sign):
        if not string[sign:].replace('.', '', 1).isdigit():
            return False
        else:
            return True

    def save_CSV(self, i, content):
        for j in range(len(content)):
            content[j] = str(content[j])
        save_filename = self.data_files[i]
        with open(os.path.join(self.data_path, save_filename), "a", newline='') as file:
            csv_writer = csv.writer(file)
            csv_writer.writerow(content)


def load_parameters(filename):
    dict_parameters = {}
    with open(filename, "r") as file:
        lines = file.readlines()
    for i in range(len(lines)):
        line = lines[i].split(';')
        if line[0] == "available_bauds" or line[0] == "format_files" or line[0] == "save_files":
            bauds = line[1].split(',')
            for j in range(len(bauds)):
                bauds[j] = bauds[j].rstrip("\n")
            dict_parameters[line[0]] = bauds
        elif line[0] == "rssi" or line[0] == "autoscroll":
            dict_parameters[line[0]] = bool(int(line[1].rstrip("\n")))
        else:
            dict_parameters[line[0]] = line[1].rstrip("\n")
    return dict_parameters


if __name__ == '__main__':
    parameters = load_parameters("parameters")
    parameter_formats_files = parameters["format_files"]
    parameter_saving_files = parameters["save_files"]
    parameter_port = parameters["selected_port"]
    parameter_baud_rate = int(parameters["selected_baud"])
    parameter_rssi = parameters["rssi"]
    parameter_header = parameters["header"]
    parameter_output = parameters["output_file"]
    ser = Serial_Monitor(parameter_port, parameter_baud_rate, header=parameter_header, output=parameter_output,
                         format_files=parameter_formats_files, data_files=parameter_saving_files, rssi=parameter_rssi)
    ser.start_tracking()
