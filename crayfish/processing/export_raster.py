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
from processing.algs.qgis.QgisAlgorithm import QgisAlgorithm
from qgis.core import (Qgis,
                       QgsProcessing,
                       QgsProcessingException,
                       QgsProcessingParameterNumber,
                       QgsProcessingParameterMeshLayer,
                       QgsProcessingParameterRasterDestination,
                       QgsMesh,
                       QgsMeshDatasetIndex,
                       QgsRasterBlock,
                       QgsProject,
                       QgsMeshUtils,
                       QgsRasterFileWriter,
                       QgsMapToPixel,
                       QgsProcessingParameterExtent,
                       QgsErrorMessage
                       )
import qgis
from .parameters import DatasetParameter, TimestepParameter


class MeshExportRasterAlgorithm(QgisAlgorithm):
    INPUT_LAYER = 'CRAYFISH_INPUT_LAYER'
    INPUT_DATASET_GROUPS = 'CRAYFISH_INPUT_GROUP'
    INPUT_TIMESTEP = 'CRAYFISH_INPUT_TIMESTEP'
    INPUT_EXTENT = 'CRAYFISH_INPUT_EXTENT'
    OUTPUT = 'CRAYFISH_OUTPUT_RASTER'
    MAP_UNITS_PER_PIXEL = 'MAP_UNITS_PER_PIXEL'

    def icon(self):
        return QIcon(":/plugins/crayfish/images/crayfish.png")

    def name(self):
        return 'CrayfishExportRaster'

    def displayName(self):
        return 'Rasterize'

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterMeshLayer(
                    self.INPUT_LAYER,
                    'Input mesh layer',
                    optional=False))

        self.addParameter(
            QgsProcessingParameterExtent(self.INPUT_EXTENT, description=u'Minimum extent to render'))

        self.addParameter(QgsProcessingParameterNumber(
            self.MAP_UNITS_PER_PIXEL,
            self.tr(
                'Map units per pixel'),
            defaultValue=100,
            minValue=0,
            type=QgsProcessingParameterNumber.Double
        ))

        self.addParameter(DatasetParameter(
                    self.INPUT_DATASET_GROUPS,
                    'Dataset group',
                    self.INPUT_LAYER,
                    optional=False))

        self.addParameter(TimestepParameter(
                    self.INPUT_TIMESTEP,
                    'Timestep',
                    self.INPUT_LAYER,
                    optional=False))

        # We add a raster layer as output
        self.addParameter(QgsProcessingParameterRasterDestination(
            self.OUTPUT,
            self.tr(
                'Output layer')))

    def processAlgorithm(self, parameters, context, feedback):
        layer = self.parameterAsMeshLayer(parameters, self.INPUT_LAYER, context)
        datasets = parameters[self.INPUT_DATASET_GROUPS]
        timestep = parameters[self.INPUT_TIMESTEP]

        mupp = self.parameterAsDouble(
            parameters,
            self.MAP_UNITS_PER_PIXEL,
            context)

        extent = self.parameterAsExtent(
            parameters,
            self.INPUT_EXTENT,
            context)

        output_layer = self.parameterAsOutputLayer(
            parameters,
            self.OUTPUT,
            context)

        if not datasets:
            raise QgsProcessingException(u'No dataset groups selected')

        no_bands = len(datasets)
        width = extent.width()/mupp
        height = extent.height()/mupp
        map_settings = qgis.utils.iface.mapCanvas().mapSettings()
        crs = map_settings.destinationCrs()
        transform_context = QgsProject.instance().transformContext()
        outputFormat = QgsRasterFileWriter.driverForExtension(os.path.splitext(output_layer)[1])

        rfw = QgsRasterFileWriter(output_layer)
        rfw.setOutputProviderKey('gdal')
        rfw.setOutputFormat(outputFormat)
        rdp = rfw.createMultiBandRaster(
            Qgis.Float64,
            width,
            height,
            extent,
            crs,
            no_bands
        )
        if rdp is None:
            raise QgsProcessingException(self.tr("Could not create raster output: {}").format(output_layer))
        if not rdp.isValid():
            raise QgsProcessingException(self.tr("Could not create raster output {}: {}").format(output_layer,
                                                                                                 rdp.error().message(
                                                                                                     QgsErrorMessage.Text)))

        rdp.setEditable(True)

        band_index = 1 # numbered from 1
        for groupIndex in datasets:
            datasetIndex = QgsMeshDatasetIndex(groupIndex, timestep)

            block = QgsMeshUtils.exportRasterBlock(
                layer,
                datasetIndex,
                crs,
                transform_context,
                mupp,
                extent
            )
            rdp.writeBlock(block, band_index)
            rdp.setNoDataValue(band_index, block.noDataValue())
            feedback.setProgress(band_index / no_bands * 100)
            band_index =+ 1

        rdp.setEditable(False)

        feedback.setProgress(100)
        return {self.OUTPUT: output_layer}
