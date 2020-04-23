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

from PyQt5.QtGui import *
from qgis.core import QgsProcessingProvider

from .contours import MeshContoursAlgorithm

from .export_faces import ExportFacesAlgorithm
from .export_vertices import ExportVerticesAlgorithm
from .export_edges import ExportEdgesAlgorithm
from .calculator import MeshCalculatorAlgorithm
from .export_raster import MeshExportRasterAlgorithm
from .saga_flow_to_grib import SagaFlowToGribAlgorithm
from .export_2d_timeseries_plot import Export2dTimeseriesPlotAlgorithm
from .export_2d_crosssection_plot import Export2dCrossSectionPlotAlgorithm

class CrayfishProcessingProvider(QgsProcessingProvider):

    def __init__(self):
        QgsProcessingProvider.__init__(self)

        # Deactivate provider by default
        self.activate = False

    def id(self):
        return 'crayfish'

    def name(self):
        return 'Crayfish'

    def icon(self):
        return QIcon(":/plugins/crayfish/images/crayfish.png")

    def load(self):
        self.refreshAlgorithms()
        return True

    def unload(self):
        QgsProcessingProvider.unload(self)

    def loadAlgorithms(self):
        self.alglist = [ExportFacesAlgorithm(),
                        ExportVerticesAlgorithm(),
                        MeshCalculatorAlgorithm(),
                        MeshExportRasterAlgorithm(),
                        SagaFlowToGribAlgorithm(),
                        Export2dTimeseriesPlotAlgorithm(),
                        Export2dCrossSectionPlotAlgorithm()]

        self.alglist += [ExportEdgesAlgorithm()]
        self.alglist += [MeshContoursAlgorithm()]

        for alg in self.alglist:
            self.addAlgorithm(alg)
