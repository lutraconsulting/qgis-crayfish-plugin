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

import os
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QVariant
from processing.algs.qgis.QgisAlgorithm import QgisAlgorithm
from qgis.core import (
    Qgis,
    QgsProcessingException,
    QgsProcessingParameterNumber,
    QgsProcessingParameterMeshLayer,
    QgsProcessingParameterFeatureSink,
    QgsMesh,
    QgsMeshDatasetIndex,
    QgsProject,
    QgsMeshUtils,
    QgsRasterFileWriter,
    QgsProcessingParameterExtent,
    QgsErrorMessage,
    QgsFeature,
    QgsFields,
    QgsField,
    QgsMesh,
    QgsMeshDatasetIndex,
    QgsProcessing,
    QgsProcessingParameterString,
    QgsWkbTypes,
    QgsMeshRendererScalarSettings
)
from qgis.analysis import (
    QgsMeshContours
)

from .parameters import DatasetParameter, TimestepParameter


class MeshContoursAlgorithm(QgisAlgorithm):
    INPUT_LAYER = 'CRAYFISH_INPUT_LAYER'
    INPUT_DATASETS = 'CRAYFISH_INPUT_DATASET'
    INPUT_TIMESTEP = 'CRAYFISH_INPUT_TIMESTEP'
    INPUT_STEP = 'CRAYFISH_INPUT_STEP'
    INPUT_MIN = 'CRAYFISH_INPUT_MIN'
    INPUT_MAX = 'CRAYFISH_INPUT_MAX'
    INPUT_LEVELS = 'CRAYFISH_INPUT_LEVELS'

    OUTPUT_LINE = 'OUTPUT_LINE'
    OUTPUT_POLY = 'OUTPUT_POLY'

    def icon(self):
        return QIcon(":/plugins/crayfish/images/crayfish.png")

    def name(self):
        return 'CrayfishContours'

    def displayName(self):
        return 'Export contours'

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterMeshLayer(
                    self.INPUT_LAYER,
                    'Input mesh layer',
                    optional=False))

        self.addParameter(DatasetParameter(
                    self.INPUT_DATASETS,
                    'Dataset groups',
                    self.INPUT_LAYER,
                    optional=True))

        self.addParameter(TimestepParameter(
                    self.INPUT_TIMESTEP,
                    'Timestep',
                    self.INPUT_LAYER,
                    optional=False))

        self.addParameter(QgsProcessingParameterNumber(self.INPUT_STEP,
                                                       self.tr('Increment between contour levels'),
                                                       type=QgsProcessingParameterNumber.Double,
                                                       minValue=0.0,
                                                       optional=True))

        self.addParameter(QgsProcessingParameterNumber(
                    self.INPUT_MIN,
                    self.tr('Minimum contour level'),
                    type=QgsProcessingParameterNumber.Double,
                    optional=True))

        self.addParameter(QgsProcessingParameterNumber(
                    self.INPUT_MAX,
                    self.tr('Maximum contour level'),
                    type=QgsProcessingParameterNumber.Double,
                    optional=True))

        self.addParameter(QgsProcessingParameterString(
                    self.INPUT_LEVELS,
                    self.tr('List of contour levels'),
                    optional=True))

        self.addParameter(QgsProcessingParameterFeatureSink(
                    self.OUTPUT_LINE,
                    'Exported contour lines',
                    type=QgsProcessing.TypeVectorLine))

        self.addParameter(QgsProcessingParameterFeatureSink(
                    self.OUTPUT_POLY,
                    'Exported contour polygons',
                    type=QgsProcessing.TypeVectorPolygon))

    def _export_lines(self, levels, runner, dp,
                      datasets, timestep, i, total, sink, feedback):
        for groupIndex in datasets:
            meta = dp.datasetGroupMetadata(groupIndex)
            name = meta.name()
            index = QgsMeshDatasetIndex(groupIndex, timestep)

            datasetMeta = dp.datasetMetadata(index)
            time = datasetMeta.time()

            for value in levels:
                # fetch values
                geom = runner.exportLines(index,
                                          value,
                                          QgsMeshRendererScalarSettings.NeighbourAverage,
                                          feedback)
                if geom:
                    attrs = []
                    attrs.append(name)
                    attrs.append(time)
                    attrs.append(value)

                    f = QgsFeature()
                    f.setGeometry(geom)
                    f.setAttributes(attrs)
                    sink.addFeature(f)
                feedback.setProgress(100 * i / total)
                i += 1

        return i

    def _export_polys(self, levels, runner, dp,
                      datasets, timestep, i, total, sink,
                      feedback):
        for groupIndex in datasets:
            meta = dp.datasetGroupMetadata(groupIndex)
            name = meta.name()
            index = QgsMeshDatasetIndex(groupIndex, timestep)
            datasetMeta = dp.datasetMetadata(index)
            time = datasetMeta.time()
            for i in range(len(levels)-1):
                lower_val = levels[i]
                upper_val = levels[i+1]
                # fetch values
                geom = runner.exportPolygons(index,
                                             lower_val, upper_val,
                                             QgsMeshRendererScalarSettings.NeighbourAverage,
                                             feedback)
                if geom:
                    attrs = []
                    attrs.append(name)
                    attrs.append(time)
                    attrs.append(lower_val)
                    attrs.append(upper_val)

                    f = QgsFeature()
                    f.setGeometry(geom)
                    f.setAttributes(attrs)
                    sink.addFeature(f)
                feedback.setProgress(100 * i / total)

                i += 1

        return i

    def _parse_levels(self, parameters, context):
        levels = self.parameterAsString(parameters, self.INPUT_LEVELS, context)
        if not levels:
            interval = self.parameterAsDouble(parameters, self.INPUT_STEP, context)
            minimal = self.parameterAsDouble(parameters, self.INPUT_MIN, context)
            maximal = self.parameterAsDouble(parameters, self.INPUT_MAX, context)

            if (interval is None) or (minimal is None) or (maximal is None):
                raise QgsProcessingException("Either levels or internal must be entered")

            if (minimal >= maximal) or (interval <= 0):
                raise QgsProcessingException("Invalid input values minimal < maximal")

            ret = []
            value = minimal
            while value < maximal:
                if value > maximal:
                    ret += [value]
                else:
                    ret += [value]
                value += interval
        else:
            ret = []
            levels = levels.split(",")
            for level in levels:
                try:
                    ret += [float(level)]
                except ValueError:
                    raise QgsProcessingException("Invalid format for level values, must be comma separated list")

        if len(ret) < 1:
            raise QgsProcessingException("At least one contour level is required")

        return ret

    def processAlgorithm(self, parameters, context, feedback):
        layer = self.parameterAsMeshLayer(parameters, self.INPUT_LAYER, context)
        levels = self._parse_levels(parameters, context)
        datasets = parameters[self.INPUT_DATASETS]
        timestep = parameters[self.INPUT_TIMESTEP]

        fields_line = QgsFields()
        fields_line.append(QgsField("group", QVariant.String))
        fields_line.append(QgsField("time", QVariant.Double))
        fields_line.append(QgsField("value", QVariant.Double))

        (sink_line, dest_id_line) = self.parameterAsSink(parameters,
                                               self.OUTPUT_LINE,
                                               context,
                                               fields_line,
                                               QgsWkbTypes.MultiLineString,
                                               layer.crs())

        if sink_line is None:
            raise QgsProcessingException(self.invalidSinkError(parameters, self.OUTPUT_LINE))

        fields_poly = QgsFields()
        fields_poly.append(QgsField("group", QVariant.String))
        fields_poly.append(QgsField("time", QVariant.Double))
        fields_poly.append(QgsField("min_value", QVariant.Double))
        fields_poly.append(QgsField("max_value", QVariant.Double))
        (sink_poly, dest_id_poly) = self.parameterAsSink(parameters,
                                               self.OUTPUT_POLY,
                                               context,
                                               fields_poly,
                                               QgsWkbTypes.MultiPolygon,
                                               layer.crs())

        if sink_poly is None:
            raise QgsProcessingException(self.invalidSinkError(parameters, self.OUTPUT_POLY))

        total = len(datasets) * len(levels)
        runner = QgsMeshContours(layer)
        dp = layer.dataProvider()

        i = self._export_lines(levels, runner, dp,
                      datasets, timestep, 1, total, sink_line, feedback)

        self._export_polys(levels, runner, dp,
                      datasets, timestep, i, total, sink_poly, feedback)

        feedback.setProgress(100)
        return {self.OUTPUT_LINE: dest_id_line, self.OUTPUT_POLY: dest_id_poly}
