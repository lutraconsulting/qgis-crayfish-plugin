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


from math import sqrt
from osgeo import gdal

from PyQt5.QtCore import QCoreApplication
from PyQt5.QtGui import QIcon

from qgis.core import (
    Qgis,
    QgsRasterBlock,
    QgsRasterFileWriter,
    QgsProcessingParameterRasterLayer,
    QgsProcessingParameterRasterDestination,
    QgsProcessingAlgorithm
)
from qgis.utils import iface


class SagaFlowToGribAlgorithm(QgsProcessingAlgorithm):

    OUTPUT = 'CRAYFISH_OUTPUT_GRIB'
    INPUT = 'CRAYFISH_INPUT_RASTER'

    def icon(self):
        return QIcon(":/plugins/crayfish/images/crayfish.png")

    def name(self):
        return 'CrayfishConvertSagaFlowToGrib'

    def displayName(self):
        return 'SAGA Flow to GRIB'

    def group(self):
        return 'Conversions'

    def groupId(self):
        return 'Conversions'

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return SagaFlowToGribAlgorithm()

    def initAlgorithm(self, config):
        self.addParameter(QgsProcessingParameterRasterLayer(self.INPUT, self.tr('Input raster')))
        self.addParameter(QgsProcessingParameterRasterDestination(self.OUTPUT, self.tr('Resulting raster')))

    def processAlgorithm(self, parameters, context, feedback):
        inp_rast = self.parameterAsRasterLayer(parameters, self.INPUT, context)
        grib_filename = self.parameterAsOutputLayer(
            parameters,
            self.OUTPUT,
            context
        )

        idp = inp_rast.dataProvider()
        map_settings = iface.mapCanvas().mapSettings()
        crs = map_settings.destinationCrs()
        outputFormat = QgsRasterFileWriter.driverForExtension('.tif')

        height = inp_rast.height()
        width = inp_rast.width()
        inp_block = idp.block(1, idp.extent(), width, height)

        rfw = QgsRasterFileWriter(grib_filename + '.tif')
        rfw.setOutputProviderKey('gdal')
        rfw.setOutputFormat(outputFormat)
        rdp = rfw.createMultiBandRaster(
            Qgis.Float32,
            width,
            height,
            idp.extent(),
            crs,
            2
        )

        rdp.setEditable(True)
        x_block = QgsRasterBlock(Qgis.Float32, width, height)
        y_block = QgsRasterBlock(Qgis.Float32, width, height)
        diag = 1. / sqrt(2)
        dir_map = {
            0: (0, 1),
            1: (diag, diag),
            2: (1, 0),
            3: (diag, -diag),
            4: (0, -1),
            5: (-diag, -diag),
            6: (-1, 0),
            7: (-diag, diag),
            255: (0, 0)
        }
        for row in range(height):
            for col in range(width):
                dir_ind = inp_block.value(row, col)
                try:
                    x_val, y_val = dir_map.get(dir_ind, 255)
                except TypeError:
                    x_val, y_val = (0, 0)
                x_block.setValue(row, col, x_val)
                y_block.setValue(row, col, y_val)

        rdp.writeBlock(x_block, 1)
        rdp.writeBlock(y_block, 2)
        rdp.setNoDataValue(1, inp_block.noDataValue())
        rdp.setNoDataValue(2, inp_block.noDataValue())
        rdp.setEditable(False)

        # rewrite the resulting raster as GRIB using GDAL for setting metadata
        res_tif = gdal.Open(grib_filename + '.tif')
        grib_driver = gdal.GetDriverByName('GRIB')
        grib = grib_driver.CreateCopy(grib_filename, res_tif)
        band_names = ('x-flow', 'y-flow')
        for i in range(2):
            band_nr = i + 1
            band_name = band_names[i]
            grib_band = grib.GetRasterBand(band_nr)
            grib_band.SetMetadataItem('grib_comment', band_name)
            grib_band.SetNoDataValue(255)
            grib_band.SetDescription(band_name)
            res_tif_band_array = res_tif.GetRasterBand(band_nr).ReadAsArray()
            grib_band.WriteArray(res_tif_band_array)
            feedback.setProgress(band_nr * 50)
        grib = None
        return {self.OUTPUT: grib_filename}
