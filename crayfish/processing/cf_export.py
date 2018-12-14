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
        return 'ExportFaces'

    def displayName(self):
        return 'Export Faces'

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

        groups_meta = {}
        fields = QgsFields()
        for groupIndex in datasets:
            meta = dp.datasetGroupMetadata(groupIndex)
            groups_meta[groupIndex] = meta
            name = meta.name()
            fields.append(QgsField(name, QVariant.Double))
            if meta.isVector():
                fields.append(QgsField('{}_x'.format(name), QVariant.Double))
                fields.append(QgsField('{}_y'.format(name), QVariant.Double))


        (sink, dest_id) = self.parameterAsSink(parameters, self.OUTPUT, context,
                                               fields, QgsWkbTypes.Polygon, layer.crs())

        if sink is None:
            raise QgsProcessingException(self.invalidSinkError(parameters, self.OUTPUT))

        mesh = QgsMesh()
        dp.populateMesh(mesh)
        count = mesh.faceCount()

        offset = 0
        batch_size = 100
        while offset < count:
            iterations = min(batch_size, count - offset)

            # fetch values
            datasets_values = {}
            for groupIndex in datasets:
                datasets_values[groupIndex] = dp.datasetValues(QgsMeshDatasetIndex(groupIndex, timestep), offset, iterations)

            for i in range(iterations):
                face = mesh.face(offset + i)
                points = [mesh.vertex(v) for v in face]
                polygon = QgsPolygon()
                polygon.setExteriorRing(QgsLineString(points))
                geom = QgsGeometry(polygon)

                f = QgsFeature()
                f.setGeometry(geom)

                attrs = []
                for groupIndex in datasets:
                    value = datasets_values[groupIndex].value(i)
                    meta = groups_meta[groupIndex]
                    attrs.append(value.scalar())
                    if meta.isVector():
                        attrs.append(value.x())
                        attrs.append(value.y())
                f.setAttributes(attrs)

                sink.addFeature(f)
                # sink.addFeature(f, QgsFeatureSink.FastInsert)
                feedback.setProgress(100 * ((offset + i + 1) / count))

            offset += iterations

        feedback.setProgress(100)
        return {self.OUTPUT: dest_id}
