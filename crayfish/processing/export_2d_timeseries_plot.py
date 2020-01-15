# -*- coding: utf-8 -*-

# Crayfish - A collection of tools for TUFLOW and other hydraulic modelling packages
# Copyright (C) 2020 Lutra Consulting

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
    QgsProcessingParameterFileDestination,
    QgsProcessingParameterFeatureSource,
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
from ..plot import timeseries_plot_data

from .parameters import DatasetParameter

class Export2dTimeseriesPlotAlgorithm(QgisAlgorithm):
    INPUT_LAYER = 'CRAYFISH_INPUT_LAYER'
    INPUT_DATASETS = 'CRAYFISH_INPUT_DATASET'
    INPUT_POINTS = 'CRAYFISH_INPUT_POINTS'
    OUTPUT_FILE = 'OUTPUT_FILE'

    def icon(self):
        return QIcon(":/plugins/crayfish/images/crayfish.png")

    def name(self):
        return 'Crayfish2dTimeseriesPlot'

    def displayName(self):
        return 'Export 2D timeseries plot data'

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterMeshLayer(
                    self.INPUT_LAYER,
                    'Input mesh layer',
                    optional=False))

        self.addParameter(DatasetParameter(
                    self.INPUT_DATASETS,
                    'Dataset groups',
                    self.INPUT_LAYER,
                    allowMultiple=False,
                    optional=False))

        self.addParameter(QgsProcessingParameterFeatureSource(
                    self.INPUT_POINTS,
                    'Points for data export',
                    [QgsProcessing.TypeVectorPoint]))

        self.addParameter(QgsProcessingParameterFileDestination(
                    self.OUTPUT_FILE,
                    'Exported data CSV file',
                    'CSV file (*.csv)'))

    def processAlgorithm(self, parameters, context, feedback):
        layer = self.parameterAsMeshLayer(parameters, self.INPUT_LAYER, context)
        group = parameters[self.INPUT_DATASETS]
        source = self.parameterAsSource(parameters, self.INPUT_POINTS, context)
        csv = self.parameterAsFileOutput(parameters, self.OUTPUT_FILE, context)

        total = 100.0 / source.featureCount() if source.featureCount() else 0
        features = source.getFeatures()

        header = ['fid', 'x', 'y', 'group', 'time', 'value']

        if os.path.exists(csv):
            os.remove(csv)

        with open(csv, 'w') as output_file:
          line = ','.join(name for name in header) + "\n"
          output_file.write(line)
          for current, f in enumerate(features):
              if feedback.isCanceled():
                  break
              geom = f.geometry()
              point = geom.asPoint()
              times, values = timeseries_plot_data(layer=layer, ds_group_index=group, geometry=geom)
              for i in range(len(times)):
                  data = [f.id(), point.x(), point.y(), group, times[i], values[i]]
                  line = ','.join(str(name) for name in data) + '\n'
                  output_file.write( line )
              feedback.setProgress(int(current * total))

        return {self.OUTPUT_FILE: csv}
