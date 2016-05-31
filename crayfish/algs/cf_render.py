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

from ..core import RendererConfig, Renderer
from .cf_alg import CfGeoAlgorithm
from PyQt4.QtGui import QImage
from processing.core.outputs import OutputFile
from processing.core.parameters import ParameterFile, ParameterNumber

class RenderMeshBedElevationAlgorithm(CfGeoAlgorithm):
    IN_CF_MESH = 'CF_MESH'
    IN_CF_W = 'CF_W'
    IN_CF_H = 'CF_H'
    OUT_CF_IMG = "CF_IMG"

    def defineCharacteristics(self):
        self.name, self.i18n_name = self.trAlgorithm('Render Bed Elevation')
        self.group, self.i18n_group = self.trAlgorithm('Mesh and Bed Elevation')
        self.addParameter(ParameterFile(self.IN_CF_MESH, self.tr('Crayfish Mesh'), optional=False))
        self.addParameter(ParameterNumber(self.IN_CF_W, self.tr('Width'), default=800))
        self.addParameter(ParameterNumber(self.IN_CF_H, self.tr('Height'), default=600))
        self.addOutput(OutputFile(self.OUT_CF_IMG, self.tr('Rendered Image')))

    def processAlgorithm(self, progress):
        m = self.get_mesh(self.IN_CF_MESH)
        o = self.get_bed_elevation(m)

        output_filename = self.getOutputValue(self.OUT_CF_IMG)
        w = self.getParameterValue(self.IN_CF_W)
        h = self.getParameterValue(self.IN_CF_H)
        size = (w, h)

        extent = m.extent()
        muppx = (extent[2] - extent[0]) / size[0]
        muppy = (extent[3] - extent[1]) / size[1]
        mupp = max(muppx, muppy)
        cx = (extent[2] + extent[0]) / 2
        cy = (extent[3] + extent[1]) / 2
        ll = (cx - (size[0] / 2) * mupp, cy - (size[1] / 2) * mupp)

        rconfig = RendererConfig()
        rconfig.set_view(size, ll, mupp)
        rconfig.set_output_mesh(m)
        rconfig.set_output_contour(o)

        img = QImage(size[0], size[1], QImage.Format_ARGB32)

        r = Renderer(rconfig, img)
        r.draw()

        img.save(output_filename)
