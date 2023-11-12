import dataclasses
import json
import os
import csv
import shutil
from collections import OrderedDict
from enum import Enum
from tempfile import TemporaryDirectory
from typing import Type, Any, TypeVar, List

from ecom.database import CommunicationDatabase, CommunicationDatabaseError, Unit, ConfigurationValueResponseType, \
    ConfigurationValueDatapoint, Configuration, Constant
from ecom.datatypes import TypeInfo, StructType, EnumType, ArrayType, DynamicSizeError, DefaultValueInfo
from ecom.message import TelecommandType, TelemetryType, DependantTelecommandResponseType

T = TypeVar('T')


def createNewDatabase(path):
    # SHARED DATA TYPES
    sharedDataTypes = {
        "TelecommandMessageHeader": {
            "__doc__": "The header of a telecommand send from the base.",
            "sync byte 1": {
                "__type__": "uint8",
                "__value__": "SYNC_BYTE_1",
                "__doc__": "The first synchronisation byte."
            },
            "sync byte 2": {
                "__type__": "uint8",
                "__value__": "SYNC_BYTE_2",
                "__doc__": "The second synchronisation byte."
            },
            "checksum": {
                "__type__": "uint16",
                "__doc__": "The checksum of the message.\n"
                           "The two sync bytes and the checksum itself are not included in the checksum."
            },
            "counter": {
                "__type__": "uint8",
                "__doc__": "A number identifying this command."
            },
            "type": {
                "__type__": "TelecommandType",
                "__doc__": "The type of telecommand."
            }
        },
        "TelemetryMessageHeader": {
            "__doc__": "The header of a message for the base.",
            "sync byte 1": {
                "__type__": "uint8",
                "__value__": "SYNC_BYTE_1",
                "__doc__": "The first synchronisation byte."
            },
            "sync byte 2": {
                "__type__": "uint8",
                "__value__": "SYNC_BYTE_2",
                "__doc__": "The second synchronisation byte."
            },
            "checksum": {
                "__type__": "uint16",
                "__doc__": "The checksum of the message.\nThe two sync bytes and the checksum "
                           "are not included in the checksum, but the telemetry data is included."
            },
            "type": {
                "__type__": "TelemetryType",
                "__doc__": "The type of telemetry that is send in this message."
            }
        }
    }
    sharedDataTypesPath = os.path.join(path, 'sharedDataTypes.json')
    with open(sharedDataTypesPath, 'w', encoding='utf-8') as outputFile:
        json.dump(sharedDataTypes, outputFile, indent=2, ensure_ascii=True, cls=EComValueJsonEncoder)
    # SHARED CONSTANTS
    sharedConstants = [
        ['SYNC_BYTE_1', '170', 'uint8', 'The first byte of every message between the secondary device and the base.'],
        ['SYNC_BYTE_2', '85', 'uint8', 'The second byte of every message between the secondary device and the base.']]
    sharedConstantsPath = os.path.join(path, 'sharedConstants.csv')
    with open(sharedConstantsPath, "w", newline='', encoding='utf-8') as file:
        csvWriter = csv.writer(file)
        csvWriter.writerow(['Name', 'Value', 'Type', 'Description'])
        for constant in sharedConstants:
            csvWriter.writerow(constant)
    # TELEMETRY AND TELECOMMAND TYPES
    telemetriesPath = os.path.join(path, 'telemetry.csv')
    telecommandsPath = os.path.join(path, 'commands.csv')
    with open(telemetriesPath, "w", newline='', encoding='utf-8') as file:
        csvWriter = csv.writer(file)
        csvWriter.writerow(['Name', 'Description'])
    with open(telecommandsPath, "w", newline='', encoding='utf-8') as file:
        csvWriter = csv.writer(file)
        csvWriter.writerow(['Name', 'Debug', 'Description', 'Response name', 'Response type', 'Response description'])


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


class ConstantValue:
    """ A value that originates from a constant. """
    @property
    def constant(self) -> Constant:
        """ The constant that this value originates from. """
        # The _constant attribute is set when loading the value.
        # noinspection PyUnresolvedReferences
        return self._constant


class UpdatableCommunicationDatabase(CommunicationDatabase):
    def updateConstant(self, constant: Constant, oldName: str):
        if not isinstance(constant.value, constant.type.type):
            raise ValueError(f'Invalid value type for constant {constant.name}: '
                             f'Should be {constant.type.type}, got {type(constant.value)}')
        if constant.type.default is not None and constant.type.default.constantName == constant.name:
            raise ValueError(f'Invalid constant type info for constant {constant.name}: '
                             f'Type info default value cannot be the constant itself')
        if constant.name != oldName:
            if constant.name in self.constants:
                raise ValueError(f'Invalid constant name: {constant.name} already exists')
            if constant.name in self.AUTOGENERATED_CONSTANT_NAMES:
                raise ValueError(f'Invalid constant name: {constant.name} is a reserved autogenerated name')
        # TODO: Check that the constants type is not a custom type

        oldConstant = self.constants[oldName]
        self._constants = OrderedDict((constant.name, constant) if name == oldName else (name, constant)
                                      for name, constant in self._constants.items())
        try:
            # Don't need to update units, they can't depend on constants.

            # Update the default values of all constant type infos that use this constant.
            canUseNewConstant = False
            for name, otherConstant in self._constants.items():
                if not canUseNewConstant:
                    if name == constant.name:
                        canUseNewConstant = True
                    continue
                if otherConstant.type.default is not None and otherConstant.type.default.constantName == oldName:
                    newType = dataclasses.replace(otherConstant.type, default=DefaultValueInfo(
                        value=self._loadConstantValue(constant), constantName=constant.name
                    ), baseTypeName=constant.type.baseTypeName)
                    self.updateConstant(dataclasses.replace(otherConstant, type=newType), oldName=name)

            # Update the default values of all types that use this constant.
            for name, typeInfo in self._typeMapping.items():
                if typeInfo.default is not None and typeInfo.default.constantName == oldName:
                    newType = dataclasses.replace(typeInfo, default=DefaultValueInfo(
                        value=self._loadConstantValue(constant), constantName=constant.name))
                    if typeInfo.baseTypeName != constant.type.baseTypeName:
                        raise RuntimeError('TODO: Handle different bast types')  # TODO
                    self.updateType(newType, newName=name, oldName=name)

            # Update all defaults of telecommands that use this constant.
            for telecommand in self._telecommandTypes:
                newTelecommand = None
                if (telecommand.response is not None
                        and not isinstance(telecommand.response, DependantTelecommandResponseType)
                        and telecommand.response.typeInfo.default is not None
                        and telecommand.response.typeInfo.default.constantName == oldName):
                    newResponse = dataclasses.replace(telecommand.response, typeInfo=dataclasses.replace(
                        telecommand.response.typeInfo, default=DefaultValueInfo(
                            value=self._loadConstantValue(constant), constantName=constant.name
                        )
                    ))
                    if newResponse.typeInfo.baseTypeName != constant.type.baseTypeName:
                        raise RuntimeError('TODO: Handle different bast types')  # TODO
                    newTelecommand = dataclasses.replace(telecommand, response=newResponse)

                argumentsToReplace = []
                for i, argument in enumerate(telecommand.data):
                    if isinstance(argument.default, ConstantValue) and argument.default.constant == oldConstant:
                        # TODO: What about the type info of the argument?
                        argumentsToReplace.append(
                            (i, dataclasses.replace(argument, default=self._loadConstantValue(constant))))

                if newTelecommand is not None or argumentsToReplace:
                    if argumentsToReplace:
                        arguments = list(telecommand.data)
                        for i, newArgument in argumentsToReplace:
                            arguments[i] = newArgument
                        newTelecommand = dataclasses.replace(
                            telecommand if newTelecommand is None else newTelecommand, data=arguments)
                    self.updateTelecommand(newTelecommand, oldId=telecommand.id)

            # Update type infos of telemetries that use this constant.
            for telemetry in self._telemetryTypes:
                argumentsToReplace = []
                for i, argument in enumerate(telemetry.data):
                    pass  # TODO
                if argumentsToReplace:
                    arguments = list(telemetry.data)
                    for i, newArgument in argumentsToReplace:
                        arguments[i] = newArgument
                    self.updateTelemetry(dataclasses.replace(telemetry, data=arguments), oldId=telemetry.id)

            # Update all configuration defaults that use this constant.
            for configuration in self._configurations:
                if (isinstance(configuration.defaultValue, ConstantValue)
                        and configuration.defaultValue.constant == oldConstant):
                    newConfiguration = dataclasses.replace(
                        configuration, defaultValue=self._loadConstantValue(constant))
                    # TODO: What about the type info of the configuration?
                    self.updateConfiguration(newConfiguration, oldId=configuration.id)
        except Exception:
            # TODO: Enable recovery attempt when things are more stable
            # self.updateConstant(oldConstant, oldName=constant.name)
            raise
        for listener in self._changeListeners:
            listener()

    def updateType(self, typeInfo: TypeInfo, newName: str, oldName: str):
        raise NotImplemented()  # TODO

    def updateTelecommand(self, telecommand: TelecommandType, oldId: EnumType):
        raise NotImplemented()  # TODO

    def updateTelemetry(self, telemetry: TelemetryType, oldId: EnumType):
        raise NotImplemented()  # TODO

    def updateConfiguration(self, configuration: Configuration, oldId: EnumType):
        raise NotImplemented()  # TODO

    def moveUnit(self, unit: Unit, newIndex: int):
        raise NotImplemented()  # TODO

    def moveConstant(self, constant: Constant, newIndex: int):
        raise NotImplemented()  # TODO

    def moveType(self, typeInfo: TypeInfo, newIndex: int):
        raise NotImplemented()  # TODO

    def moveConfiguration(self, configuration: Configuration, newIndex: int):
        raise NotImplemented()  # TODO

    def moveTelecommand(self, telecommand: TelecommandType, newIndex: int):
        raise NotImplemented()  # TODO

    def moveTelecommandDatapoint(self, telecommand: TelecommandType, oldDatapointIndex: int, newDatapointIndex: int):
        raise NotImplemented()  # TODO

    def moveTelemetry(self, telemetry: TelemetryType, newIndex: int):
        raise NotImplemented()  # TODO

    def moveTelemetryDatapoint(self, telemetry: TelemetryType, oldDatapointIndex: int, newDatapointIndex: int):
        raise NotImplemented()  # TODO

    def addConfiguration(self, name: str, **kwargs):
        self._appendElementTo(self._configurations, Configuration, name, **kwargs)

    def addTelecommand(self, name: str, **kwargs):
        self._appendElementTo(self._telecommandTypes, TelecommandType, name, **kwargs)

    def addTelemetry(self, name: str, **kwargs):
        self._appendElementTo(self._telemetryTypes, TelemetryType, name, **kwargs)

    def _appendElementTo(self, elements: List[T], elementClass: Type[T], name: str, **kwargs):
        for element in elements:
            elementEnum = element.id.__class__  # type: Type[Enum]
            break
        else:
            return
        existingEnumNames = [config.name for config in elementEnum]
        existingEnumNames.append(name)
        elementEnum = EnumType(elementEnum.__name__, existingEnumNames, start=0)
        self.replaceType(elementEnum.__class__)
        newElements = [
            dataclasses.replace(element, id=elementId)
            for element, elementId in zip(elements, elementEnum)
        ]
        newElement = elementClass(
            id=elementEnum[name],
            name=name,
            **kwargs,
        )
        newElements.append(newElement)

    def _loadConstantValue(self, constant: Constant) -> Any:
        constantType = type(constant.name, (constant.type.type, ConstantValue), {})
        value = constantType(super()._loadConstantValue(constant))
        value._constant = constant
        return value


class SavableCommunicationDatabase(UpdatableCommunicationDatabase):

    def __init__(self, dataDirectory: str):
        super().__init__(dataDirectory)
        self._path = dataDirectory

    @property
    def path(self) -> str:
        return self._path

    def save(self, dataDirectory: str):
        with TemporaryDirectory() as tempDirPath:
            self._saveUnits(os.path.join(tempDirPath, self.UNIT_DEFINITIONS_FILE_NAME))
            self._saveConstants(os.path.join(tempDirPath, self.CONSTANT_DEFINITIONS_FILE_NAME))
            self._saveConfigurations(os.path.join(tempDirPath, self.CONFIGURATION_DEFINITIONS_FILE_NAME))
            self._saveTelemetry(os.path.join(tempDirPath, self.TELEMETRY_DEFINITIONS_FILE_NAME))
            self._saveTelemetryArguments(os.path.join(tempDirPath, self.TELEMETRY_ARGUMENTS_DIRECTORY_NAME))
            self._saveTypes(os.path.join(tempDirPath, self.DATA_TYPE_DEFINITIONS_FILE_NAME))

            self._saveTelecommands(os.path.join(tempDirPath, self.COMMAND_DEFINITIONS_FILE_NAME))
            self._saveTelecommandArguments(os.path.join(tempDirPath, self.COMMAND_ARGUMENTS_DIRECTORY_NAME))
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

    def _serializeDataTypes(self):
        types = {}
        for name, typInfo in self.dataTypes.items():
            if name not in self.AUTOGENERATED_TYPE_NAMES:
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
        if not self.constants:
            return
        try:
            with open(sharedConstantsFilePath, "w", newline='', encoding='utf-8') as file:
                csvWriter = csv.writer(file)
                csvWriter.writerow(['Name', 'Value', 'Type', 'Description'])
                for constantName, constant in self.constants.items():
                    if constantName not in self.AUTOGENERATED_CONSTANT_NAMES:
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
            with open(telecommandsFilePath, 'w', newline='', encoding='utf-8') as file:
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
            with open(telemetriesFilePath, 'w', newline='', encoding='utf-8') as file:
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
            with open(filePath, 'w', newline='', encoding='utf-8') as file:
                csvWriter = csv.writer(file)
                csvWriter.writerow(['Name', 'Type', 'Description'])
                for dataPoint in telemetryResponseType.data:
                    dataPointType = self._getTypeName(dataPoint.type)
                    csvWriter.writerow([dataPoint.name, dataPointType, dataPoint.description])

    def _getTypeName(self, typeInfo: TypeInfo) -> str:
        typeName = typeInfo.name
        try:
            if isinstance(typeInfo, Unit) and self.units[typeName][0].baseTypeName != typeInfo.baseTypeName:
                typeName = f'{typeInfo.baseTypeName} ({typeName})'
        except KeyError:
            # Unit does not exist anymore: Not searching for variants
            pass
        return typeName


class BalloonPackageDatabase(SavableCommunicationDatabase):
    """
    The shared communication database for balloon packages. Contains all information about the telecommunication.
    """

    def getTypeName(self, typeInfo: TypeInfo) -> str:
        return self._getTypeName(typeInfo)

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

    def getSharedDataTypes(self):
        types = []
        for name, typInfo in self.dataTypes.items():
            if name not in self.AUTOGENERATED_TYPE_NAMES:
                types.append(name)
        return types
