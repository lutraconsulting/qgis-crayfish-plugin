# -*- coding: utf-8 -*-

# Crayfish - A collection of tools for TUFLOW and other hydraulic modelling packages
# Copyright (C) 2016 Lutra Consulting

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

import datetime

from qgis.PyQt.QtCore import QVariant
from processing.gui.wrappers import EnumWidgetWrapper
from qgis.core import (QgsProcessing,
                       QgsProcessingException,
                       QgsProcessingParameterMeshLayer,
                       QgsProcessingParameterFeatureSink,
                       QgsWkbTypes,
                       QgsGeometry,
                       QgsPolygon,
                       QgsLineString,
                       QgsFeature,
                       QgsFields,
                       QgsField,
                       QgsMesh,
                       QgsMeshDatasetIndex)

from .cf_alg import CfGeoAlgorithm
from .parameters import DatasetParameter, TimestepParameter


class ExportAlgorithm(CfGeoAlgorithm):
    INPUT_LAYER = 'CRAYFISH_INPUT_LAYER'
    INPUT_DATASETS = 'CRAYFISH_INPUT_DATASETS'
    INPUT_TIMESTEP = 'CRAYFISH_INPUT_TIMESTEP'
    OUTPUT = 'OUTPUT'

    def name(self):
        return 'MeshExport'

    def displayName(self):
        return 'Mesh Export'

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterMeshLayer(
                    self.INPUT_LAYER,
                    'Input vector layer',
                    optional=False))

        self.addParameter(DatasetParameter(
                    self.INPUT_DATASETS,
                    'Datasets',
                    self.INPUT_LAYER,
                    optional=True))

        self.addParameter(TimestepParameter(
                    self.INPUT_TIMESTEP,
                    'Timestep',
                    self.INPUT_LAYER,
                    optional=False))

        self.addParameter(QgsProcessingParameterFeatureSink(
                    self.OUTPUT,
                    'Exported layer',
                    type=QgsProcessing.TypeVectorPolygon))


    def processAlgorithm(self, parameters, context, feedback):
        layer = self.parameterAsMeshLayer(parameters, self.INPUT_LAYER, context)
        dp = layer.dataProvider()

        # parameterAsEnums doesn't work with updated options
        # datasets = self.parameterAsEnums(parameters, self.INPUT_DATASETS, context)
        datasets = parameters[self.INPUT_DATASETS]
        timestep = parameters[self.INPUT_TIMESTEP]

        feedback.setProgress(100)
        return {}
