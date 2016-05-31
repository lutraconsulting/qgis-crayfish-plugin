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

from PyQt4.QtCore import QSettings
from qgis.core import QgsVectorFileWriter

from processing.core.parameters import ParameterFile
from processing.core.outputs import OutputNumber
from processing.tools import dataobjects, vector

from .cf_alg import CfGeoAlgorithm

class InfoAlgorithm(CfGeoAlgorithm):
    CF_LAYER = 'CRAYFISH_INPUT_LAYER'
    OUTPUT_NELEM = "CRAYFISH_NELEMENTS"
    OUTPUT_NNODE = "CRAYFISH_NNODES"

    def defineCharacteristics(self):
        self.name, self.i18n_name = self.trAlgorithm('Mesh statistics')
        self.group, self.i18n_group = self.trAlgorithm('Mesh and Bed Elevation')
        self.addParameter(ParameterFile(self.CF_LAYER, self.tr('Crayfish layer'), optional=False))
        self.addOutput(OutputNumber(self.OUTPUT_NELEM, self.tr('Number of elements')))
        self.addOutput(OutputNumber(self.OUTPUT_NNODE, self.tr('Number of nodes')))

    def processAlgorithm(self, progress):
        m = self.get_mesh(self.CF_LAYER)

        nelem = self.getOutputValue(self.OUTPUT_NELEM)
        nnode = self.getOutputValue(self.OUTPUT_NNODE)
        nelem = cf_mesh.element_count()
        nnode = cf_mesh.node_count()


