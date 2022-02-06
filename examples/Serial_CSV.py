from serial import Serial
import csv
import os
import time
from tendo import singleton


def verify_message_data(data):
    for i in range(1, len(data)):
        if not data[i].replace('.', '', 1).isdigit():
            return False
    return True

print("Initializing")
# Verify if other instance of same code exists
me = singleton.SingleInstance()

# Creating data directory if non existent
data_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
if not os.path.exists(data_path):
    os.mkdir(data_path)

header = ['time', 'CPM', 'dose']
# connecting to Arduino port for Serial listening
arduino_port_win = "COM7"
arduino_port_rasp = "/dev/ttyACM0"
baud = 9600
ser = Serial(arduino_port_win, baud)
print("Connected to Arduino port:" + arduino_port_win)

# Getting the captors list
with open("Captors", "r") as file:
    captors = file.readlines()
for i in range(len(captors)):
    captors[i] = captors[i].replace("\n", "")
n = len(captors)

# Creating data pins list
data_pins = ['n' for i in range(n)]

continuing = 1
while continuing:
    # Updating the captors list in case of addition by the GUI
    with open("Captors", "r") as file:
        new_captors = file.readlines()
    for i in range(len(new_captors)):
        new_captors[i] = new_captors[i].replace("\n", "")

    # Checking for added or deleted captors in the list
    if len(new_captors) > len(captors):  # Captor added
        added_indices = [new_captors.index(ele) for ele in new_captors if ele not in captors]
        for j in added_indices:
            data_pins.insert(j, 'n')

    elif len(new_captors) < len(captors):  # Captor deleted
        deleted_indices = [captors.index(ele) for ele in captors if ele not in new_captors]
        for j in deleted_indices:
            data_pins.pop(j)

    else:  # Captor modified
        modified_indices = [captors.index(ele) for ele in new_captors if ele not in captors]
        for j in modified_indices:
            data_pins[j] = 'n'
    captors = new_captors

    # Getting Serial Message
    getData = str(ser.readline())
    data = getData[0:][:-2]

    # Translating data for CSV writing
    data = data.split("'")
    info = data[1]
    info = info.split()

    # Verifying validity of message
    if info[0] in captors and verify_message_data(info):
        i = captors.index(info[0])
        if data_pins[i] != info[1]:
            string = time.strftime("%Y-%m-%d %H:%M:%S")
            name = info[0]
            info[0] = string  # getting the time stamp of reception
            print(name, " ", info)
            pin = info.pop(1)  # Getting rid of data pin

            with open(os.path.join(data_path, name + ".csv"), "a") as file:
                csv_writer = csv.writer(file)
                csv_writer.writerow(info)
            data_pins[i] = pin
        print(data_pins)
