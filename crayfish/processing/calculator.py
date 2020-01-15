# -*- coding: utf-8 -*-

# Crayfish - A collection of tools for TUFLOW and other hydraulic modelling packages
# Copyright (C) 2019 Lutra Consulting

# info at lutraconsulting dot co dot uk
# Lutra Consulting
# 23 Chestnut Close
# Burgess Hill
# West Sussex
# RH15 8HN

# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

from PyQt5.QtGui import QIcon
from qgis.PyQt.QtCore import QVariant
from processing.algs.qgis.QgisAlgorithm import QgisAlgorithm
from qgis.core import (QgsProcessing,
                       QgsProcessingException,
                       QgsProcessingParameterMeshLayer,
                       QgsProcessingParameterFileDestination,
                       QgsProcessingParameterString,
                       QgsProcessingParameterExtent,
                       QgsProcessingParameterEnum,
                       QgsMesh,
                       QgsMeshDatasetIndex)
from qgis.analysis import QgsMeshCalculator
from .parameters import TimestepParameter
from qgis.core import QgsProviderRegistry

try:
    from qgis.core import QgsMeshDriverMetadata
    have_qgis310_api = False
except ImportError:
    have_qgis310_api = True


class MeshCalculatorAlgorithm(QgisAlgorithm):
    INPUT_LAYER = 'CRAYFISH_INPUT_LAYER'
    INPUT_STARTTIME = 'CRAYFISH_INPUT_STARTTIME'
    INPUT_ENDTIME = 'CRAYFISH_INPUT_ENDTIME'
    INPUT_FORMULA = 'CRAYFISH_INPUT_FORMULA'
    INPUT_EXTENT = 'CRAYFISH_INPUT_EXTENT'
    OUTPUT_FILE = 'CRAYFISH_OUTPUT_FILE'
    OUTPUT_GROUP = 'CRAYFISH_OUTPUT_GROUP'
    OUTPUT_DRIVER = 'CRAYFISH_OUTPUT_DRIVER'

    def name(self):
        return 'CrayfishMeshCalculator'

    def displayName(self):
        return 'Mesh calculator'

    def icon(self):
        return QIcon(":/plugins/crayfish/images/crayfish.png")

    def meshWriteDrivers(self):
        assert( not have_qgis310_api)
        meshDrivers = []
        providerMetadata = QgsProviderRegistry.instance().providerMetadata("mdal")
        if providerMetadata:
            allDrivers = providerMetadata.meshDriversMetadata()
            for meta in allDrivers:
                if (meta.capabilities() & QgsMeshDriverMetadata.MeshDriverCapability.CanWriteFaceDatasets) or (
                        meta.capabilities() & QgsMeshDriverMetadata.MeshDriverCapability.CanWriteVertexDatasets):
                    meshDrivers += [meta.name()]
        else:
            meshDrivers = ["DAT"]
        return meshDrivers

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterMeshLayer(
                    self.INPUT_LAYER,
                    'Input mesh layer',
                    optional=False))

        self.addParameter(QgsProcessingParameterString(
            self.INPUT_FORMULA,
            'Formula',
            multiLine=True,
            optional=False))

        self.addParameter(QgsProcessingParameterExtent(
            self.INPUT_EXTENT,
            'Extent',
            optional=False
        ))

        self.addParameter(TimestepParameter(
                    self.INPUT_STARTTIME,
                    'Start Time',
                    self.INPUT_LAYER,
                    optional=False))

        self.addParameter(TimestepParameter(
                    self.INPUT_ENDTIME,
                    'End Time',
                    self.INPUT_LAYER,
                    optional=False))

        if have_qgis310_api:
            # only dat file exporter is implemented in MDAL
            self.addParameter(QgsProcessingParameterFileDestination(
                        self.OUTPUT_FILE,
                        'Exported dataset group file',
                        'binary DAT (*.dat)',
                        ))
        else:
            self.addParameter(QgsProcessingParameterFileDestination(
                        self.OUTPUT_FILE,
                        'Exported dataset group file',
                        'MDAL file (*.*)',
                        ))

            self.addParameter(QgsProcessingParameterString(
                self.OUTPUT_GROUP,
                'Name of the exported dataset group'
            ))

            self.drivers = self.meshWriteDrivers()
            self.addParameter(QgsProcessingParameterEnum(
                self.OUTPUT_DRIVER,
                'Driver to write results with',
                self.drivers
            ))


    def processAlgorithm(self, parameters, context, feedback):
        layer = self.parameterAsMeshLayer(parameters, self.INPUT_LAYER, context)
        startDatasetIndex = parameters[self.INPUT_STARTTIME]
        endDatasetIndex = parameters[self.INPUT_ENDTIME]
        extent = self.parameterAsExtent(parameters, self.INPUT_EXTENT, context)
        formula = self.parameterAsString(parameters, self.INPUT_FORMULA, context)
        outputFile = self.parameterAsFileOutput(parameters, self.OUTPUT_FILE, context)

        if have_qgis310_api:
            calculator = QgsMeshCalculator(
                formula,
                outputFile,
                extent,
                startDatasetIndex,
                endDatasetIndex,
                layer)
        else:
            outputDriver = self.drivers[parameters[self.OUTPUT_DRIVER]]
            outputGroup = self.parameterAsString(parameters, self.OUTPUT_GROUP, context)

            calculator = QgsMeshCalculator(
                formula,
                outputDriver,
                outputGroup,
                outputFile,
                extent,
                startDatasetIndex,
                endDatasetIndex,
                layer)

        res = calculator.processCalculation( feedback )
        if res != QgsMeshCalculator.Success:
            raise QgsProcessingException("Could not calculate output group (err: {})".format(res))

        feedback.setProgress(100)
        return {self.OUTPUT_FILE: outputFile}
