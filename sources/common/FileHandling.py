import dataclasses
import os
import csv
from typing import Type

import pandas as pd
import numpy as np
import time

from ecom.database import Unit, Configuration
from ecom.datatypes import TypeInfo, DefaultValueInfo, EnumType

from sources.databases.balloondata import BalloonPackageDatabase


def nameGiving(nameList: list, baseName: str = '', parentheses=False, startingIndex=0):
    i = startingIndex
    if parentheses:
        name = baseName + ' (' + str(i) + ')'
    else:
        name = baseName + ' ' + str(i)
    while name in nameList:
        if parentheses:
            name = baseName + ' (' + str(i) + ')'
        else:
            name = baseName + ' ' + str(i)
        i += 1
    return name


def testSaving(path):
    database = BalloonPackageDatabase(path)

    ### ADDING CONSTANTS ###
    typeName = 'uint32_t'
    uint32Type = TypeInfo(TypeInfo.lookupBaseType(typeName), typeName, typeName)
    database.constants['someConstant'] = 1, 'some description', uint32Type

    ### ADDING CONFIG ###
    newConfigName = 'new config'
    for config in database.configurations:
        configEnum = config.id.__class__  # type: Type[Enum]
        break
    else:
        return
    existingEnumNames = [config.name for config in configEnum]
    existingEnumNames.append(newConfigName)
    configEnum = EnumType(configEnum.__name__, existingEnumNames, start=0)
    newConfigs = [
        dataclasses.replace(config, id=configId)
        for config, configId in zip(database.configurations, configEnum)
    ]
    newConfigs.append(Configuration(
        id=configEnum[newConfigName],
        name=newConfigName,
        type=TypeInfo(TypeInfo.lookupBaseType(typeName), typeName, typeName),
        defaultValue=1,
        description='A new configuration',
    ))
    database._configurations = newConfigs

    ### EDIT CONFIG ###

    ### ADDING UNITS ###
    unitName = 'unit1'
    database.units[unitName] = [Unit.fromTypeInfo(unitName, uint32Type, 'Some unit')]
    unitName = 'unit2'
    x = '10'
    if x:
        default = DefaultValueInfo(int(x))
    else:
        default = None
    database.units[unitName] = [
        Unit(TypeInfo.lookupBaseType(typeName), unitName, typeName, 'Some unit', default=default)]

    ### EDITING UNITS ###
    unitName = 'ms'
    database.units[unitName][0] = dataclasses.replace(database.units[unitName][0], description='Something else')

    database.units[unitName][0] = dataclasses.replace(database.units[unitName][0], type=int, baseTypeName='uint16_t')

    database.save(path + '1')

    ### DATABASE VERIFYING DEFAULT VALUES FOR CONFIGS COMPATIBLE WITH TYPES ###
    for config in database.configurations:
        if not isinstance(config.defaultValue, config.type.type):
            print(f'Default value {config.defaultValue!r} for config {config.name} is not valid')


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
        elif line[0] in ['AUTOSCROLL', 'AUTOSCALE', 'EMULATOR_MODE', 'RSSI']:
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
            elif setting in ['AUTOSCROLL', 'AUTOSCALE', 'EMULATOR_MODE', 'RSSI']:
                file.write(setting + '=' + str(int(parameters[setting])) + '\n')
            else:
                file.write(setting + '=' + str(parameters[setting]) + '\n')


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
