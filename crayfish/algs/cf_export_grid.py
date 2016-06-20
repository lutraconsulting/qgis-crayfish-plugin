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

from .cf_alg import CfGeoAlgorithm
from .cf_error import CrayfishProccessingAlgorithmError
from processing.core.outputs import OutputRaster
from processing.core.parameters import ParameterFile, ParameterNumber, ParameterCrs

class ExportMeshGridAlgorithm(CfGeoAlgorithm):
    IN_CF_MESH = 'CF_MESH'
    IN_CF_MUPP = 'CF_MUPP'
    IN_CF_CRS = 'CF_CRS'
    OUT_CF_TIF = "CF_TIF"

    def defineCharacteristics(self):
        self.name, self.i18n_name = self.trAlgorithm('Export grid')
        self.group, self.i18n_group = self.trAlgorithm('Mesh and Bed Elevation')
        self.addParameter(ParameterFile(self.IN_CF_MESH, self.tr('Crayfish Mesh'), optional=False))
        self.addParameter(ParameterNumber(self.IN_CF_MUPP, self.tr('Grid resolution'), default=1))
        self.addParameter(ParameterCrs(self.IN_CF_CRS, self.tr('CRS'), default=""))
        self.addOutput(OutputRaster(self.OUT_CF_TIF, self.tr('Mesh grid')))

    def processAlgorithm(self, progress):
        m = self.get_mesh(self.IN_CF_MESH)
        o = self.get_bed_elevation(m)

        outf = self.getOutputValue(self.OUT_CF_TIF)
        mupp = self.getParameterValue(self.IN_CF_MUPP)
        crs = self.getParameterValue(self.IN_CF_CRS)

        res = o.export_grid(mupp, outf, crs)
        if not res:
            raise CrayfishProccessingAlgorithmError("Unable to export grid")
