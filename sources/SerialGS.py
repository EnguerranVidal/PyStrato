import csv
import os
import random
import string
from datetime import datetime
from enum import Enum
from typing import Dict, Any

from PyQt5.QtCore import pyqtSignal, QThread
from ecom.checksum import ChecksumVerifier

from ecom.database import CommunicationDatabase
from ecom.datatypes import TypeInfo, StructType, ArrayType, DynamicSizeError
from ecom.parser import TelemetryParser
from ecom.serializer import TelemetrySerializer
from serial import Serial
import time

# --------------------- Sources ----------------------- #
from sources.common.FileHandling import load_settings, load_format
from sources.common.balloondata import BalloonPackageDatabase


class SerialEmulator:
    def __init__(self, databases: Dict[str, CommunicationDatabase]):
        self._databases = databases

    def read(self, _: int) -> bytes:
        data = b''
        for database in self._databases.values():
            verifier = ChecksumVerifier(database)
            serializer = TelemetrySerializer(database, verifier=verifier)
            for telemetryType in database.telemetryTypes:
                dataPoints = {}
                for dataPointType in telemetryType.data:
                    dataPoints[dataPointType.name] = self._randomValueForType(dataPointType.type, dataPoints)
                data += serializer.serialize(telemetryType, **dataPoints)
        return data

    @staticmethod
    def inWaiting() -> int:
        return 1

    def _randomValueForType(self, typeInfo: TypeInfo, pastValues: Dict[str, Any]) -> Any:
        if issubclass(typeInfo.type, StructType):
            children = {}
            for childName, childTypeInfo in typeInfo.type:
                children[childName] = self._randomValueForType(childTypeInfo, children)
            return typeInfo.type(children)
        if issubclass(typeInfo.type, ArrayType):
            elementTypeInfo = typeInfo.type.getElementTypeInfo()
            try:
                size = len(typeInfo.type)
            except DynamicSizeError as error:
                size = pastValues[error.sizeMember]
            if issubclass(elementTypeInfo.type, bytes):
                return ''.join(random.choices(string.printable, k=size))
            return typeInfo.type([self._randomValueForType(elementTypeInfo, pastValues) for _ in range(size)])
        if issubclass(typeInfo.type, bool):
            return random.choice([True, False])
        if issubclass(typeInfo.type, Enum):
            return random.choice(list(typeInfo.type))
        if issubclass(typeInfo.type, int):
            minValue = typeInfo.getMinNumericValue(self._databases)
            maxValue = typeInfo.getMaxNumericValue(self._databases)
            return random.randint(minValue, maxValue)
        if issubclass(typeInfo.type, float):
            minValue = typeInfo.getMinNumericValue(self._databases)
            maxValue = typeInfo.getMaxNumericValue(self._databases)
            return random.uniform(minValue, maxValue)
        if issubclass(typeInfo.type, str):
            return random.choice(string.printable)
        raise TypeError(f'Unsupported type {typeInfo}')


class SerialMonitor(QThread):
    progress = pyqtSignal(dict)
    output = pyqtSignal(str)

    def __init__(self, path):
        super().__init__()
        self.currentDir = path
        self._active = False
        self.settings = load_settings('settings')
        self.dataDir = os.path.join(self.currentDir, 'data')
        self.formatDir = os.path.join(self.currentDir, 'formats')

    def run(self):
        parsers = {}
        databases = {}
        for path in self.settings['FORMAT_FILES']:
            path = os.path.join(self.formatDir, path)
            name, database = os.path.basename(path), BalloonPackageDatabase(path)
            parsers[name] = TelemetryParser(database)
            databases[name] = database
        if True:
            connection = SerialEmulator(databases)
        else:
            connection = Serial(self.settings['SELECTED_PORT'], self.settings['SELECTED_BAUD'], timeout=1)
        self.output.emit("Connected to port " + self.settings['SELECTED_PORT'] + " with baud rate of " +
                         self.settings['SELECTED_BAUD'] + ".")
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


if __name__ == '__main__':
    monitor = SerialMonitor()
    monitor.startTracking()
