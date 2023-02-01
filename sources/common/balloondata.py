import dataclasses
import json
import os
import csv
import shutil
from enum import Enum
from tempfile import TemporaryDirectory
from typing import Optional, Type, Any

from ecom.database import CommunicationDatabase, CommunicationDatabaseError, Unit, ConfigurationValueResponseType, \
    ConfigurationValueDatapoint, Configuration, TelecommandType
from ecom.datatypes import TypeInfo, StructType, EnumType, ArrayType, DynamicSizeError

from ecom.message import TelemetryType


class EComValueJsonEncoder(json.JSONEncoder):
    """ A json encoder that allows writing ECom values. """
    def default(self, x):
        if isinstance(x, bytes):
            return x.decode('utf-8')
        if isinstance(x, Enum):
            return x.name
        return super().default(x)


def serializeTypedValue(value: Any, typ: Type) -> str:
    """
    Serialize a value with the given type.

    :param value: A value.
    :param typ: The type of the parsed value.
    :return: The serialized value.
    """
    if not isinstance(value, (typ, str)):
        if isinstance(value, bytes) and issubclass(typ, ArrayType):
            childType = typ.getElementTypeInfo().type
            if issubclass(childType, bytes):
                try:
                    if len(value) > len(typ):
                        raise ValueError(f'Value for bytes list is too large: {len(value)} (max is {len(typ)})')
                except DynamicSizeError:
                    pass
                return value.decode('utf-8')
        raise ValueError(f'Invalid value for {typ.__name__} type: {value!r} ({type(value)})')
    if issubclass(typ, bool):
        if not isinstance(value, str):
            return 'true' if value else 'false'
        if value not in ['true', 'false']:
            raise ValueError(f'Invalid value for bool type: {value!r} ({type(value)})')
        return value
    if issubclass(typ, bytes):
        if isinstance(value, bytes):
            return value.decode('utf-8')
        return value
    if issubclass(typ, StructType):
        if not isinstance(value, dict):
            raise ValueError(f'Invalid value for struct type: {value!r} ({type(value)})')
        return json.dumps(value, cls=EComValueJsonEncoder)
    if issubclass(typ, ArrayType):
        if not isinstance(value, list):
            raise ValueError(f'Invalid value for array type: {value!r} ({type(value)})')
        return json.dumps(value, cls=EComValueJsonEncoder)
    if isinstance(value, Enum):
        return value.name
    return json.dumps(value, cls=EComValueJsonEncoder)


class BalloonPackageDatabase(CommunicationDatabase):
    """ The shared communication database for balloon packages. Contains all information about the telecommunication.
    """

    def __init__(self, dataDirectory: str):
        super().__init__(dataDirectory)
        self._path = dataDirectory

    @property
    def path(self) -> str:
        return self._path

    def save(self, dataDirectory: str):
        with TemporaryDirectory() as tempDirPath:
            self._saveUnits(os.path.join(tempDirPath, 'units.csv'))
            self._saveConstants(os.path.join(tempDirPath, 'sharedConstants.csv'))
            self._saveConfigurations(os.path.join(tempDirPath, 'configuration.csv'))
            self._saveTelemetry(os.path.join(tempDirPath, 'telemetry.csv'))
            self._saveTelemetryArguments(os.path.join(tempDirPath, 'telemetryArguments'))
            self._saveTypes(os.path.join(tempDirPath, 'sharedDataTypes.json'))

            self._saveTelecommands(os.path.join(tempDirPath, 'commands.csv'))
            self._saveTelecommandArguments(os.path.join(tempDirPath, 'commandArguments'))
            tempDataDir = dataDirectory + '.backup'
            while os.path.exists(tempDataDir):
                tempDataDir = tempDataDir + '.backup'
            try:
                shutil.move(dataDirectory, tempDataDir)
            except FileNotFoundError:
                pass
            try:
                shutil.move(tempDirPath, dataDirectory)
            except IOError:
                try:
                    shutil.move(tempDataDir, dataDirectory)
                except FileNotFoundError:
                    pass
                raise
            try:
                shutil.rmtree(tempDataDir)
            except FileNotFoundError:
                pass

    def _saveTypes(self, typesFilePath):
        """
        Saves the shared datatype information.

        :param typesFilePath: The path to the shared data types file.
        """
        types = self._serializeDataTypes()
        with open(typesFilePath, 'w', encoding='utf-8') as outputFile:
            json.dump(types, outputFile, indent=2, ensure_ascii=True, cls=EComValueJsonEncoder)

    def nestedPythonTypes(self, telemetryName: str, searchedType=int):
        telemetryType = self.getTelemetryByName(telemetryName)
        dataPoints = {dataPoint.name: dataPoint.type for dataPoint in telemetryType.data}
        dataTypeNames = [name for name, typInfo in self.dataTypes.items()]
        dataUnits = [unitName for unitName, unit in self.units.items()]

        def retrieveDataTypes(dataTypeInfo):
            types = {}
            units = {}
            if issubclass(dataTypeInfo.type, Enum):  # Enumerations
                types = issubclass(dataTypeInfo.type, searchedType)
            elif issubclass(dataTypeInfo.type, StructType):  # Structs
                for name, child in dataTypeInfo.type:
                    if child.baseTypeName not in self.dataTypes:
                        types[name], units[name] = retrieveDataTypes(child)
                    else:
                        types[name] = issubclass(child.type, searchedType)

                        if child.baseTypeName in dataUnits:
                            units[name] = child.baseTypeName
                        else:
                            units[name] = None
            else:
                types = issubclass(dataTypeInfo.type, searchedType)
                if dataTypeInfo.baseTypeName in dataUnits:
                    units = dataTypeInfo.baseTypeName
                else:
                    units = None
            return types, units

        selectedTypes = {}
        selectedUnits = {}
        for dataName, dataType in dataPoints.items():
            if dataType.name in dataTypeNames:
                typeInfo = self.dataTypes[dataType.name]
                selectedTypes[dataName], selectedUnits[dataName] = retrieveDataTypes(typeInfo)

            elif dataType.name in dataUnits:
                selectedTypes[dataName] = issubclass(self.units[dataType.name][0].type, searchedType)
                selectedUnits[dataName] = dataType.name
            else:
                selectedTypes[dataName] = issubclass(dataType.type, searchedType)
                selectedUnits[dataName] = None
        return selectedTypes, selectedUnits

    def _serializeDataTypes(self):
        types = {}
        autogeneratedTypes = [
            'ConfigurationId',
            'Configuration',
            'Telecommand',
            'TelemetryType',
        ]
        for name, typInfo in self.dataTypes.items():
            if name not in autogeneratedTypes:
                types[name] = self._serializeType(typInfo)
        return types

    def _serializeType(self, typeInfo: TypeInfo):
        serializedType = {}
        self._serializeBasicTypeInfo(serializedType, typeInfo)
        if issubclass(typeInfo.type, Enum):  # Enumerations
            serializedType['__type__'] = typeInfo.baseTypeName
            if all(not child.__doc__ for child in typeInfo.type):
                values = [enumValue.name for enumValue in typeInfo.type]
            else:
                values = {
                    enumValue.name: {'__doc__': enumValue.__doc__}
                    for enumValue in typeInfo.type
                }
            serializedType['__values__'] = values
        elif issubclass(typeInfo.type, StructType):  # Structures
            for name, child in typeInfo.type:
                if child.baseTypeName not in self.dataTypes:
                    serializedType[name] = self._serializeType(child)
                else:
                    serializedChild = {}
                    self._serializeBasicTypeInfo(serializedChild, child)
                    if not serializedChild:  # Simple case
                        serializedChild = child.baseTypeName
                    else:
                        serializedChild['__type__'] = child.baseTypeName
                    serializedType[name] = serializedChild
        else:  # Others
            if not serializedType:  # Simple case
                return typeInfo.baseTypeName
            serializedType['__type__'] = typeInfo.baseTypeName
        return serializedType

    @staticmethod
    def _serializeBasicTypeInfo(serializedType, typeInfo):
        if typeInfo.description:
            serializedType['__doc__'] = typeInfo.description
        if typeInfo.default is not None:
            serializedType['__value__'] = typeInfo.default.constantName \
                if typeInfo.default.constantName is not None else typeInfo.default.value

    def _saveConstants(self, sharedConstantsFilePath):
        """
        Saves the shared constants.

        :param sharedConstantsFilePath: The path to the shared constants file.
        """
        autogeneratedConstantNames = [
            'NUM_CONFIGURATIONS',
            'DEFAULT_CONFIGURATION',
            'MAX_TELECOMMAND_DATA_SIZE',
            'MAX_TELECOMMAND_RESPONSE_SIZE',
        ]
        if not self.constants:
            return
        try:
            with open(sharedConstantsFilePath, "w", newline='', encoding='utf-8') as file:
                csvWriter = csv.writer(file)
                csvWriter.writerow(['Name', 'Value', 'Type', 'Description'])
                for constantName, constant in self.constants.items():
                    if constantName not in autogeneratedConstantNames:
                        csvWriter.writerow([constantName, constant.value,
                                            constant.type.baseTypeName, constant.description])
        except IOError as error:
            raise CommunicationDatabaseError(f'Error writing {sharedConstantsFilePath}: {error}')

    def _saveConfigurations(self, configurationsFilePath):
        """
        Saves the secondary device configuration items.

        :param configurationsFilePath: The path to the configurations file.
        """
        if not self.configurations:
            return
        try:
            with open(configurationsFilePath, "w", newline='', encoding='utf-8') as file:
                csvWriter = csv.writer(file)
                csvWriter.writerow(['Name', 'Type', 'Default Value', 'Description'])
                for configuration in self.configurations:
                    csvWriter.writerow([configuration.name, self._getTypeName(configuration.type),
                                        serializeTypedValue(configuration.defaultValue, configuration.type.type),
                                        configuration.description])
        except IOError as error:
            raise CommunicationDatabaseError(f'Error writing {configurationsFilePath}: {error}')

    def _saveUnits(self, unitsFilePath):
        """
        Saves the unit types.

        :param unitsFilePath: The path to the units file.
        """
        if not self.units:
            return
        try:
            with open(unitsFilePath, "w", newline='', encoding='utf-8') as file:
                csvWriter = csv.writer(file)
                csvWriter.writerow(['Name', 'Type', 'Description'])
                for unitName, unitVariants in self.units.items():
                    unit = unitVariants[0]
                    csvWriter.writerow([unit.name, unit.baseTypeName, unit.description])
        except IOError as error:
            raise CommunicationDatabaseError(f'Error writing {unitsFilePath}: {error}')

    def _saveTelecommands(self, telecommandsFilePath):
        """
        Saves the telecommands.

        :param telecommandsFilePath: The path to the file containing information about the telecommands.
        """
        if not self.telecommandTypes:
            return
        try:
            with open(telecommandsFilePath, "w", newline='', encoding='utf-8') as file:
                csvWriter = csv.writer(file)
                csvWriter.writerow(['Name', 'Debug', 'Description', 'Response name',
                                    'Response type', 'Response description'])
                for telecommand in self.telecommandTypes:
                    responseName, responseType, responseDescription = '', '', ''
                    if telecommand.response:
                        responseName = telecommand.response.name
                        responseDescription = telecommand.response.description
                        if isinstance(telecommand.response, ConfigurationValueResponseType):
                            responseType = 'config?'
                        else:
                            responseType = self._getTypeName(telecommand.response.typeInfo)
                    csvWriter.writerow([telecommand.id.name, str(telecommand.isDebug).lower(), telecommand.description,
                                        responseName, responseType, responseDescription])
        except IOError as error:
            raise CommunicationDatabaseError(f'Error writing {telecommandsFilePath}: {error}')

    def _saveTelecommandArguments(self, telecommandsArgumentsFolder):
        """
        Saves the arguments for the telecommands.

        :param telecommandsArgumentsFolder: The path to the folder containing the files where the telecommand
                                            arguments information is to be saved.
        """
        os.makedirs(telecommandsArgumentsFolder, exist_ok=True)
        for telecommand in self.telecommandTypes:
            filePath = os.path.join(telecommandsArgumentsFolder, telecommand.id.name + '.csv')
            if not telecommand.data:
                continue
            with open(filePath, "w", newline='', encoding='utf-8') as file:
                csvWriter = csv.writer(file)
                csvWriter.writerow(['Name', 'Type', 'Default', 'Description'])
                for argument in telecommand.data:
                    if isinstance(argument, ConfigurationValueDatapoint):
                        dataPointType = 'config?'
                    else:
                        dataPointType = self._getTypeName(argument.type)
                    default = '' if argument.default is None else \
                        serializeTypedValue(argument.default, argument.type.type)
                    csvWriter.writerow([argument.name, dataPointType, default, argument.description])

    def _saveTelemetry(self, telemetriesFilePath):
        """
        Saves the telemetry types.

        :param telemetriesFilePath: The path to the file containing information about the telemetry.
        """
        if not self.telemetryTypes:
            return
        try:
            with open(telemetriesFilePath, "w", newline='', encoding='utf-8') as file:
                csvWriter = csv.writer(file)
                csvWriter.writerow(['Name', 'Description'])
                for telemetryResponseType in self.telemetryTypes:
                    csvWriter.writerow([telemetryResponseType.id.name, telemetryResponseType.id.__doc__])
        except IOError as error:
            raise CommunicationDatabaseError(f'Error writing {telemetriesFilePath}: {error}')

    def _saveTelemetryArguments(self, telemetryArgumentsFolder):
        """
        Saves the arguments for the telemetry types.

        :param telemetryArgumentsFolder: The path to the folder containing the files where the telemetry
                                         arguments information is going to be saved.
        """
        os.makedirs(telemetryArgumentsFolder, exist_ok=True)
        for telemetryResponseType in self.telemetryTypes:
            if not telemetryResponseType.data:
                continue
            filePath = os.path.join(telemetryArgumentsFolder, telemetryResponseType.id.name + '.csv')
            with open(filePath, "w", newline='', encoding='utf-8') as file:
                csvWriter = csv.writer(file)
                csvWriter.writerow(['Name', 'Type', 'Description'])
                for dataPoint in telemetryResponseType.data:
                    dataPointType = self._getTypeName(dataPoint.type)
                    csvWriter.writerow([dataPoint.name, dataPointType, dataPoint.description])

    def _getTypeName(self, typeInfo):
        typeName = typeInfo.name
        try:
            if isinstance(typeInfo, Unit) and self.units[typeName][0].baseTypeName != typeInfo.baseTypeName:
                typeName = f'{typeInfo.baseTypeName} ({typeName})'
        except KeyError:
            # Unit does not exist anymore : not searching for variants
            pass
        return typeName

    def getTypeName(self, typeInfo):
        return self._getTypeName(typeInfo)

    def addConfiguration(self, name: str, replaceIndex: Optional[int] = None, **kwargs):
        self._configurations = self._editElement(
            name, self._configurations, Configuration, replaceIndex=replaceIndex, **kwargs)

    def addTelecommand(self, name: str, replaceIndex: Optional[int] = None,  **kwargs):
        self._telecommandTypes = self._editElement(
            name, self._telecommandTypes, TelecommandType, replaceIndex=replaceIndex, **kwargs)

    def addTelemetry(self, name: str, replaceIndex: Optional[int] = None,  **kwargs):
        self._telemetryTypes = self._editElement(
            name, self._telemetryTypes, TelemetryType, replaceIndex=replaceIndex, **kwargs)

    @staticmethod
    def _editElement(name: str, elements, typeClass, replaceIndex: Optional[int] = None, **kwargs):
        for element in elements:
            elementEnum = element.id.__class__  # type: Type[Enum]
            break
        else:
            return
        existingEnumNames = [config.name for config in elementEnum]
        existingEnumNames.append(name)
        elementEnum = EnumType(elementEnum.__name__, existingEnumNames, start=0)
        newElements = [
            dataclasses.replace(element, id=elementId)
            for element, elementId in zip(elements, elementEnum)
        ]
        newElement = typeClass(
            id=elementEnum[name],
            name=name,
            **kwargs,
        )
        if replaceIndex is None:
            newElements.append(newElement)
        else:
            newElements[replaceIndex] = newElement
        return newElements
