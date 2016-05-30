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

from processing.core.GeoAlgorithm import GeoAlgorithm
from .cf_error import CrayfishProccessingAlgorithmError
from ..core import DataSet, Mesh


class CfGeoAlgorithm(GeoAlgorithm):
    def get_mesh(self, val):
        inFile = self.getParameterValue(val)
        try:
            m = Mesh(inFile)
        except ValueError:
            raise CrayfishProccessingAlgorithmError("Unable to load mesh")
        return m

    def get_bed_elevation(self, mesh):
        try:
             d = mesh.dataset(0)
             o = d.output(0)
        except IndexError:
            raise CrayfishProccessingAlgorithmError("Missing bed elevation")

        if d.type() != DataSet.Bed:
            raise CrayfishProccessingAlgorithmError("Dataset 0 is not bed elevation")

        return o
