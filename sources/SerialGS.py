import os
import random
import string
from collections import OrderedDict
from enum import Enum
from typing import Dict, Any, Iterator

from PyQt5.QtCore import pyqtSignal, QThread
from ecom.checksum import ChecksumVerifier

from ecom.database import CommunicationDatabase
from ecom.datatypes import TypeInfo, StructType, ArrayType, DynamicSizeError
from ecom.message import TelemetryDatapointType, TelemetryType
from ecom.parser import TelemetryParser, Parser
from ecom.serializer import TelemetrySerializer
from serial import Serial
import time

# --------------------- Sources ----------------------- #
from sources.common.utilities.FileHandling import loadSettings
from sources.databases.balloondata import BalloonPackageDatabase


def iterateRequiredDatapoints(telecommand: TelemetryType) -> Iterator[TelemetryDatapointType]:
    parameters = OrderedDict()
    for parameter in telecommand.data:
        parameters[parameter.name] = parameter
        if issubclass(parameter.type.type, ArrayType):
            try:
                len(parameter.type.type)
            except DynamicSizeError as error:
                parameters.pop(error.sizeMember, None)
    return (parameter for parameter in parameters.values())


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
                for dataPointType in iterateRequiredDatapoints(telemetryType):
                    dataPoints[dataPointType.name] = self._randomValueForType(database, dataPointType.type, dataPoints)
                data += serializer.serialize(telemetryType, **dataPoints)
        time.sleep(1)
        return data

    @staticmethod
    def inWaiting() -> int:
        return 1

    def _randomValueForType(
            self, database: CommunicationDatabase, typeInfo: TypeInfo, pastValues: Dict[str, Any]) -> Any:
        if issubclass(typeInfo.type, StructType):
            children = {}
            for childName, childTypeInfo in typeInfo.type:
                children[childName] = self._randomValueForType(database, childTypeInfo, children)
            return typeInfo.type(children)
        if issubclass(typeInfo.type, ArrayType):
            elementTypeInfo = typeInfo.type.getElementTypeInfo()
            try:
                size = len(typeInfo.type)
            except DynamicSizeError as error:
                size = pastValues.get(error.sizeMember)
                if size is None:
                    maxBytes = min(Parser.DEFAULT_MAX_DYNAMIC_MEMBER_SIZE, 127)
                    elementSize = elementTypeInfo.getSize(database)
                    size = maxBytes // elementSize
            if issubclass(elementTypeInfo.type, bytes):
                return ''.join(random.choices(string.printable, k=size)).encode('utf-8', errors='ignore')
            return typeInfo.type([self._randomValueForType(database, elementTypeInfo, pastValues) for _ in range(size)])
        if issubclass(typeInfo.type, bool):
            return random.choice([True, False])
        if issubclass(typeInfo.type, Enum):
            return random.choice(list(typeInfo.type))
        if issubclass(typeInfo.type, int):
            minValue = typeInfo.getMinNumericValue(database)
            maxValue = typeInfo.getMaxNumericValue(database)
            return random.randint(minValue, maxValue)
        if issubclass(typeInfo.type, float):
            minValue = typeInfo.getMinNumericValue(database)
            maxValue = typeInfo.getMaxNumericValue(database)
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
        self.settings = loadSettings('settings')
        self.dataDir = os.path.join(self.currentDir, 'data')
        self.formatDir = os.path.join(self.currentDir, 'formats')

    def run(self):
        parsers = {}
        databases = {}
        self.settings = loadSettings('settings')
        for path in self.settings['FORMAT_FILES']:
            path = os.path.join(self.formatDir, path)
            name, database = os.path.basename(path), BalloonPackageDatabase(path)
            parsers[name] = TelemetryParser(database)
            databases[name] = database
        if self.settings['EMULATOR_MODE']:
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
