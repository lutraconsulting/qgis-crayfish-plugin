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

from PyQt5.QtGui import QIcon
from qgis.PyQt.QtCore import QVariant
from processing.algs.qgis.QgisAlgorithm import QgisAlgorithm
from qgis.core import (QgsProcessing,
                       QgsProcessingException,
                       QgsProcessingParameterMeshLayer,
                       QgsProcessingParameterFeatureSink,
                       QgsFeature,
                       QgsFields,
                       QgsField,
                       QgsMesh,
                       QgsMeshDatasetIndex)

from .parameters import DatasetParameter, TimestepParameter


class CfMeshExportAlgorithm(QgisAlgorithm):
    INPUT_LAYER = 'CRAYFISH_INPUT_LAYER'
    INPUT_DATASETS = 'CRAYFISH_INPUT_DATASETS'
    INPUT_TIMESTEP = 'CRAYFISH_INPUT_TIMESTEP'
    OUTPUT = 'OUTPUT'

    def icon(self):
        return QIcon(":/plugins/crayfish/images/crayfish.png")

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

        self.addParameter(QgsProcessingParameterFeatureSink(
                    self.OUTPUT,
                    'Exported vector layer',
                    type=QgsProcessing.TypeVectorPolygon))


    def filter_dataset(self, datasetGroupMetadata):
        """Extended algorithms can implement custom filter for valid input dataset groups."""
        return True

    def export_geometry_type(self):
        raise NotImplementedError

    def get_mesh_geometry(self, mesh, index):
        raise NotImplementedError

    def processAlgorithm(self, parameters, context, feedback):
        layer = self.parameterAsMeshLayer(parameters, self.INPUT_LAYER, context)
        dp = layer.dataProvider()

        # parameterAsEnums doesn't work with updated options
        # datasets = self.parameterAsEnums(parameters, self.INPUT_DATASETS, context)
        datasets = parameters[self.INPUT_DATASETS]
        timestep = parameters[self.INPUT_TIMESTEP]

        groups_meta = {}
        fields = QgsFields()
        fields.append(QgsField('fid', QVariant.Int))
        for groupIndex in datasets:
            meta = dp.datasetGroupMetadata(groupIndex)
            groups_meta[groupIndex] = meta
            name = meta.name()
            fields.append(QgsField(name, QVariant.Double))
            if meta.isVector():
                fields.append(QgsField('{}_x'.format(name), QVariant.Double))
                fields.append(QgsField('{}_y'.format(name), QVariant.Double))


        (sink, dest_id) = self.parameterAsSink(parameters, self.OUTPUT, context,
                                               fields, self.export_geometry_type(), layer.crs())

        if sink is None:
            raise QgsProcessingException(self.invalidSinkError(parameters, self.OUTPUT))

        mesh = QgsMesh()
        dp.populateMesh(mesh)
        count = self.export_objects_count(mesh)

        offset = 0
        batch_size = 100
        while offset < count:
            iterations = min(batch_size, count - offset)

            # fetch values
            datasets_values = {}
            for groupIndex in datasets:
                datasets_values[groupIndex] = dp.datasetValues(QgsMeshDatasetIndex(groupIndex, timestep), offset, iterations)

            for i in range(iterations):
                attrs = [offset + i]
                for groupIndex in datasets:
                    value = datasets_values[groupIndex].value(i)
                    meta = groups_meta[groupIndex]
                    attrs.append(value.scalar())
                    if meta.isVector():
                        attrs.append(value.x())
                        attrs.append(value.y())

                f = QgsFeature()
                f.setGeometry(self.get_mesh_geometry(mesh, offset + i))
                f.setAttributes(attrs)
                sink.addFeature(f)
                feedback.setProgress(100 * ((offset + i + 1) / count))

            offset += iterations

        feedback.setProgress(100)
        return {self.OUTPUT: dest_id}
