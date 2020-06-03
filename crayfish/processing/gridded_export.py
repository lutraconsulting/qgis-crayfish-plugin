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


from math import trunc
from .mesh_export import CfMeshExportAlgorithm
from qgis.core import (QgsProcessing,
                       QgsProcessingException,
                       QgsProcessingParameterMeshLayer,
                       QgsProcessingParameterEnum,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterNumber,
                       QgsGeometry,
                       QgsFeature,
                       QgsWkbTypes,
                       QgsFields,
                       QgsField,
                       QgsMesh,
                       QgsPoint,
                       QgsPointXY,
                       QgsMeshDatasetIndex)

from .parameters import DatasetParameter, TimestepParameter


class ExportGriddedValues(CfMeshExportAlgorithm):
    INPUT_GRIDSPACING = 'CRAYFISH_INPUT_GRIDSPACING'

    def name(self):
        return 'CrayfishExportGriddedValues'

    def displayName(self):
        return 'Export gridded value on mesh'

    def export_geometry_type(self):
        return QgsWkbTypes.Point

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterMeshLayer(
                    self.INPUT_LAYER,
                    'Input mesh layer',
                    optional=False))

        self.addParameter(DatasetParameter(
                    self.INPUT_DATASETS,
                    'Dataset groups',
                    self.INPUT_LAYER,
                    datasetGroupFilter=self.filter_dataset,
                    optional=True))

        self.addParameter(TimestepParameter(
                    self.INPUT_TIMESTEP,
                    'Timestep',
                    self.INPUT_LAYER,
                    optional=False))

        self.addParameter(QgsProcessingParameterEnum(
            self.INPUT_VECTOROPTIONS,
            'Vector values type',
            self.VECTOR_OPTION_TYPE,
            allowMultiple=False,
            defaultValue=0))

        self.addParameter(QgsProcessingParameterNumber(
            self.INPUT_GRIDSPACING,
            'Grid spacing',
            QgsProcessingParameterNumber.Double,
            defaultValue=10))

        self.addParameter(QgsProcessingParameterFeatureSink(
                    self.OUTPUT,
                    'Exported vector layer',
                    type=QgsProcessing.TypeVectorPolygon))

    def populateFeatures(self,parameters,sink, layer, datasets, exportVectorOption, context, feedback):

        dataProvider = layer.dataProvider()
        extent = layer.extent()
        gridSpacing = self.parameterAsDouble(parameters, self.INPUT_GRIDSPACING, context)
        pointXCount = trunc(extent.width() / gridSpacing)+1
        pointYCount = trunc(extent.height() / gridSpacing)+1

        timestep = parameters[self.INPUT_TIMESTEP]
        # fetch metadata and values
        group_meta = {}
        datasets_index = {}

        for groupIndex in datasets:
            datasets_index[groupIndex] = QgsMeshDatasetIndex(groupIndex, timestep)
            meta = dataProvider.datasetGroupMetadata(groupIndex)
            group_meta[groupIndex] = meta

        id=0
        for xi in range(pointXCount):
            for yi in range(pointYCount):
                attrs = [id]
                x = extent.xMinimum() + xi * gridSpacing
                y = extent.yMinimum() + yi * gridSpacing
                point = QgsPointXY(x, y)
                for groupIndex in datasets:
                    meta = group_meta[groupIndex]
                    value = layer.datasetValue(datasets_index[groupIndex], point)
                    if meta.isVector():
                        vector = self.vectorValue(value, exportVectorOption)
                        for v in vector:
                            attrs.append(v)
                    else:
                        attrs.append(value.scalar())

                f = QgsFeature()
                geometry = QgsGeometry(QgsPoint(point.x(), point.y()))
                f.setGeometry(geometry)
                f.setAttributes(attrs)
                sink.addFeature(f)
                id=id+1
            feedback.setProgress(100 * (xi / pointXCount))

        feedback.setProgress(100)

    def testLayer(self,layer):
        super().testLayer(layer)
        dataProvider=layer.dataProvider()
        if not dataProvider.contains(QgsMesh.Face):
            raise QgsProcessingException("Mesh layer must contain faces")
