import os
import csv
import pandas as pd
import numpy as np
import time


def load_settings(path):
    parameters = {}
    with open(path, "r") as file:
        lines = file.readlines()
    for i in range(len(lines)):
        line = lines[i].split('=')
        if line[0] in ['AVAILABLE_BAUDS', 'FORMAT_FILES', 'OPENED_RECENTLY']:
            splitSetting = line[1].split(',')
            for j in range(len(splitSetting)):
                splitSetting[j] = splitSetting[j].rstrip("\n")
            if len(splitSetting) == 1 and splitSetting[0] == '':
                parameters[line[0]] = []
            else:
                parameters[line[0]] = splitSetting
        elif line[0] in ['RSSI', 'AUTOSCROLL', 'AUTOSCALE']:
            parameters[line[0]] = bool(int(line[1].rstrip("\n")))
        else:
            parameters[line[0]] = line[1].rstrip("\n")
    return parameters


def save_settings(parameters, path):
    with open(path, "r") as file:
        lines = file.readlines()
    with open(path, "w") as file:
        for i in range(len(lines)):
            line = lines[i].split('=')
            setting = line[0]
            if setting in ['AVAILABLE_BAUDS', 'FORMAT_FILES', 'OPENED_RECENTLY']:
                file.write(setting + '=' + ','.join(parameters[setting]) + '\n')
            elif setting in ['RSSI', 'AUTOSCROLL', 'AUTOSCALE']:
                file.write(setting + '=' + str(int(parameters[setting])) + '\n')
            else:
                file.write(setting + '=' + str(parameters[setting]) + '\n')


def save_format(packetFormat, path):
    lines = ['NAME' + ':' + packetFormat['NAME'] + '\n']
    if packetFormat['ID'] is not None:
        lines.append('ID:' + packetFormat['ID'] + '\n')
    elif packetFormat['PIN'] is not None:
        lines.append('PIN:' + packetFormat['PIN'] + '\n')
    elif packetFormat['CLOCK'] is not None:
        lines.append('CLOCK:' + packetFormat['CLOCK'] + ':' + '\n')
    names = list(packetFormat['DATA'].keys())
    for i in range(len(names)):
        data = packetFormat[names[i]]
        addendum = data['SIGN'] + ':' + data['TOTAL'] + ':' + data['FLOAT'] + ':' + data['UNIT']
        lines.append('VALUE:' + names[i] + ':' + addendum + '\n')
    lines[-1].rstrip('\n')
    with open(path, 'r') as file:
        for i in lines:
            file.write(i)


def load_format(path):
    # Accessing Lines
    with open(path, 'r') as file:
        lines = file.readlines()
    ID, PIN, CLOCK, FILE, DATA = None, None, None, '', {}
    # Getting Format Name
    lines[0] = lines[0].rstrip('\n')
    firstLine = lines[0].split(':')
    name = firstLine[1]
    for i in range(1, len(lines)):
        line = lines[i].split(':')
        if line[0] == 'VALUE':
            DATA[line[1]] = {'SIGN': line[2], 'TOTAL': line[3], 'FLOAT': line[4], 'UNIT': line[5].rstrip('\n')}
        elif line[0] == 'ID':
            ID = line[1].rstrip('\n')
        elif line[0] == 'PIN':
            PIN = line[1].rstrip('\n')
        elif line[0] == 'FILE':
            FILE = line[1].rstrip('\n')
        elif line[0] == 'CLOCK':
            CLOCK = line[1]
    return name, {'ID': ID, 'PIN': PIN, 'CLOCK': CLOCK, 'PATH': path, 'FILE': FILE, 'DATA': DATA}


def check_format(path):
    keywords = ['NAME', 'ID', 'PIN', 'CLOCK', 'FILE', 'VALUE']
    filename, file_extension = os.path.splitext(path)
    namePresent, filePresent = False, False
    if file_extension == '.config':
        with open(path, 'r') as file:
            lines = file.readlines()
        for i in range(len(lines)):
            line = lines[i].split(':')
            if len(lines[i]) != 0 and line[0] not in keywords:
                return False
            if line[0] == 'NAME':
                namePresent = True
            if line[0] == 'FILE':
                filePresent = True
        if filePresent and namePresent:
            return True
        else:
            return False
    else:
        return False


def csvRowCount(path, newLine=''):
    try:
        with open(os.path.join(path), "r", newline=newLine) as file:
            csvReader = csv.reader(file)
            return sum(1 for row in csvReader)
    except FileNotFoundError:
        return 0


def retrieveCSVData(path, packetFormat, start_date="", finish_date=""):
    if os.path.exists(path):
        if csvRowCount(path) <= 1:
            values = voidCSV(packetFormat)
            names = csvHeader(path)
            return names, values
        else:
            df = pd.read_csv(path)
            if start_date == "":
                start_date = np.array(df["UNIX"])[0]
            if finish_date == "":
                finish_date = np.array(df["UNIX"])[-1]
            time_mask = (df["UNIX"] >= start_date) & (df["UNIX"] <= finish_date)
            data = df.loc[time_mask]
            values = data.loc[:, data.columns != 'Reception Time']
            names = csvHeader(path)
            return names, np.array(values)
    else:
        values = voidCSV(packetFormat)
        names = csvHeader(path)
        return names, values


def voidCSV(packetFormat):
    keys = list(packetFormat.keys())
    nowUnix = time.time()
    nbValues = 1
    if 'DATA' in keys:
        nbValues += len(list(packetFormat['DATA'].keys()))
    if 'CLOCK' in keys:
        nbValues += 1
    line1 = [nowUnix - 1]
    line2 = [nowUnix]
    for i in range(nbValues):
        line1.append(np.nan)
        line2.append(np.nan)
    valueArray = [line1, line2]
    return np.array(valueArray)


def csvHeader(path):
    df = pd.read_csv(path)
    columnNames = list(df.columns)
    columnNames.pop(0)
    for i in range(len(columnNames)):
        if columnNames[i] != 'Internal Clock':
            columnNames[i] = columnNames[i].replace(' ', '_')
    return columnNames
