import os
import csv
import pandas as pd
import numpy as np
import time

from ecom.database import CommunicationDatabase, CommunicationDatabaseError


class BalloonPackageDatabase(CommunicationDatabase):
    """ The shared communication database for balloon packages. Contains all information about the telecommunication.
    """

    def save(self, dataDirectory):
        self._saveUnits(os.path.join(dataDirectory, 'units.csv'))
        self._saveConstants(os.path.join(dataDirectory, 'sharedConstants.csv'))
        self._saveConfigurations(os.path.join(dataDirectory, 'configuration.csv'))
        self._saveTelemetry(os.path.join(dataDirectory, 'telemetry.csv'))
        self._saveTelemetryArguments(os.path.join(dataDirectory, 'packagesArguments'))

    def _saveTypes(self, typesFilePath):
        """
        Save the shared datatype information.

        :param typesFilePath: The path to the shared data types file.
        """
        pass

    def _saveConstants(self, sharedConstantsFilePath):
        """
        Save the shared constants.

        :param sharedConstantsFilePath: The path to the shared constants file.
        """
        try:
            with open(sharedConstantsFilePath, "a", newline='') as file:
                csvWriter = csv.writer(file)
                csvWriter.writerow(['Name', 'Value', 'Type', 'Description'])
                for constantName, constant in self.constants.items():
                    csvWriter.writerow([constantName, constant[0], constant[2].baseTypeName, constant[1]])
        except IOError as error:
            raise CommunicationDatabaseError(f'Error writing {sharedConstantsFilePath}: {error}')

    def _saveConfigurations(self, configurationsFilePath):
        """
        Save the secondary device configuration items.

        :param configurationsFilePath: The path to the configurations file.
        """
        pass

    def _saveUnits(self, unitsFilePath):
        """
        Save the unit types.

        :param unitsFilePath: The path to the units file.
        """
        try:
            with open(unitsFilePath, "a", newline='') as file:
                csvWriter = csv.writer(file)
                csvWriter.writerow(['Name', 'Type', 'Description'])
                for unitName, unit in self.units.items():
                    csvWriter.writerow([unit[0].name, unit[0].baseTypeName, unit[0].description])
        except IOError as error:
            raise CommunicationDatabaseError(f'Error writing {unitsFilePath}: {error}')

    def _saveTelecommands(self, telecommandsFilePath):
        """
        Save the telecommands.

        :param telecommandsFilePath: The path to the file containing information about the telecommands.
        """
        pass

    def _saveTelemetry(self, telemetriesFilePath):
        """
        Save the telemetry types.

        :param telemetriesFilePath: The path to the file containing information about the telemetry.
        """
        try:
            with open(telemetriesFilePath, "a", newline='') as file:
                csvWriter = csv.writer(file)
                csvWriter.writerow(['Name', 'Description'])
                for telemetryResponseType in self.telemetryTypes:
                    csvWriter.writerow([telemetryResponseType.id._name_, telemetryResponseType.id.__doc__])
        except IOError as error:
            raise CommunicationDatabaseError(f'Error writing {telemetriesFilePath}: {error}')

    def _saveTelemetryArguments(self, telemetryArgumentsFolder):
        """
        Save the arguments for the telemetry types.

        :param telemetryArgumentsFolder: The path to the folder containing the files where the telemetry
                                         arguments information is going to be saved.
        """
        for telemetryResponseType in self.telemetryTypes:
            print(telemetryResponseType)


