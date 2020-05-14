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

from math import sqrt, atan, pi, copysign
from PyQt5.QtGui import QIcon
from qgis.PyQt.QtCore import QVariant
from processing.algs.qgis.QgisAlgorithm import QgisAlgorithm
from qgis.core import (QgsProcessing,
                       QgsProcessingException,
                       QgsProcessingParameterMeshLayer,
                       QgsProcessingParameterEnum,
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
    INPUT_VECTOROPTIONS = 'CRAYFISH_INPUT_VECTOROPTIONS'
    INPUT_TIMESTEP = 'CRAYFISH_INPUT_TIMESTEP'
    OUTPUT = 'OUTPUT'

    VECTOR_OPTION_TYPE = ['Cartesian (x,y)', 'Polar (magnitude,degree)', 'Cartesian and Polar']

    def icon(self):
        return QIcon(":/plugins/crayfish/images/crayfish.png")

    def processAlgorithm(self, parameters, context, feedback):
        layer = self.parameterAsMeshLayer(parameters, self.INPUT_LAYER, context)
        dp = layer.dataProvider()

        # parameterAsEnums doesn't work with updated options
        # datasets = self.parameterAsEnums(parameters, self.INPUT_DATASETS, context)
        datasets = parameters[self.INPUT_DATASETS]

        exportVectorOption = self.parameterAsEnum(parameters, self.INPUT_VECTOROPTIONS, context)

        (sink, dest_id) = self.createSink(parameters, layer, dp, datasets, exportVectorOption, context)

        if sink is None:
            raise QgsProcessingException(self.invalidSinkError(parameters, self.OUTPUT))

        self.populateFeatures(parameters, sink, layer, datasets, exportVectorOption, context, feedback)

        return {self.OUTPUT: dest_id}

    def createSink(self, parameters, layer, dataProvider, datasets, exportVectorOption, context):

        fields = QgsFields()
        fields.append(QgsField('fid', QVariant.Int))
        for groupIndex in datasets:
            meta = dataProvider.datasetGroupMetadata(groupIndex)
            name = meta.name()
            if meta.isVector():
                if exportVectorOption == 0 or exportVectorOption == 2:
                    fields.append(QgsField('{}_x'.format(name), QVariant.Double))
                    fields.append(QgsField('{}_y'.format(name), QVariant.Double))
                if exportVectorOption == 1 or exportVectorOption == 2:
                    fields.append(QgsField('{}_mag'.format(name), QVariant.Double))
                    fields.append(QgsField('{}_dir'.format(name), QVariant.Double))
            else:
                fields.append(QgsField(name, QVariant.Double))

        return self.parameterAsSink(parameters, self.OUTPUT, context,
                                    fields, self.export_geometry_type(), layer.crs())

    def filter_dataset(self, datasetGroupMetadata):
        """Extended algorithms can implement custom filter for valid input dataset groups."""
        return True

    def populateFeatures(self, parameters, sink, layer, datasets, exportVectorOption, context, feedback):
        raise NotImplementedError

    def vectorValue(self, datasetValue, option):   # option : 0 cartesian, 1: polar, 2 : both
        vector=[]
        if option == 0 or option == 2:
            vector.append(datasetValue.x())
            vector.append(datasetValue.y())
        if option == 1 or option == 2:
            x = datasetValue.x()
            y = datasetValue.y()
            magnitude = sqrt(x * x + y * y)
            if x > 0:
                direction = atan(x / y)
            elif x < 0:
                direction = pi + atan(x / y)
            elif y != 0:  # x==0
                direction = copysign(pi / 2, y)
            else:
                direction = 0

            if direction < 0:
                direction = 2 * pi - direction
            direction = direction / (2 * pi) * 360
            vector.append(magnitude)
            vector.append(direction)

        return vector;


class CfMeshExportMesh(CfMeshExportAlgorithm):

    def export_geometry_type(self):
        raise NotImplementedError

    def get_mesh_geometry(self, mesh, index):
        raise NotImplementedError

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

        self.addParameter(QgsProcessingParameterFeatureSink(
                    self.OUTPUT,
                    'Exported vector layer',
                    type=QgsProcessing.TypeVectorPolygon))

    def populateFeatures(self,parameters,sink, layer, datasets, exportVectorOption, context, feedback):

        dataProvider = layer.dataProvider()
        mesh = QgsMesh()
        dataProvider.populateMesh(mesh)
        count = self.export_objects_count(mesh)

        timestep = parameters[self.INPUT_TIMESTEP]

        offset = 0
        batch_size = 100
        while offset < count:
            iterations = min(batch_size, count - offset)

            # fetch metadata and values
            group_meta = {}
            datasets_values = {}

            for groupIndex in datasets:
                datasets_values[groupIndex] = dataProvider.datasetValues(QgsMeshDatasetIndex(groupIndex, timestep),
                                                                         offset, iterations)
                meta = dataProvider.datasetGroupMetadata(groupIndex)
                group_meta[groupIndex] = meta

            for i in range(iterations):
                attrs = [offset + i]
                for groupIndex in datasets:
                    value = datasets_values[groupIndex].value(i)
                    meta = group_meta[groupIndex]
                    if meta.isVector():
                        if meta.isVector():
                            vector = self.vectorValue(value, exportVectorOption)
                            for v in vector:
                                attrs.append(v)
                    else:
                        attrs.append(value.scalar())

                f = QgsFeature()
                f.setGeometry(self.get_mesh_geometry(mesh, offset + i))
                f.setAttributes(attrs)
                sink.addFeature(f)
                feedback.setProgress(100 * ((offset + i + 1) / count))

            offset += iterations

        feedback.setProgress(100)
