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
from PyQt4.QtCore import QVariant
from processing.core.outputs import OutputVector
from processing.core.parameters import ParameterFile
from qgis.core import QgsField, QgsFields
from qgis.core import QgsPoint, QgsGeometry, QgsFeature, QGis

def n2pt(node_index, mesh):
  n = mesh.node(node_index)
  return QgsPoint(n.x(), n.y())

def geom(elem, mesh):
    ring = []
    for ni in elem.node_indexes():
        ring.append(n2pt(ni, mesh))
    ring.append(n2pt(elem.node_index(0), mesh))
    geometry = QgsGeometry.fromPolygon([ring])
    return geometry

class ExportMeshElemsAlgorithm(CfGeoAlgorithm):
    IN_CF_MESH = 'CF_MESH'
    OUT_CF_SHP = "CF_SHP"

    def defineCharacteristics(self):
        self.name, self.i18n_name = self.trAlgorithm('Export mesh elements')
        self.group, self.i18n_group = self.trAlgorithm('Mesh and Bed Elevation')
        self.addParameter(ParameterFile(self.IN_CF_MESH, self.tr('Crayfish Mesh'), optional=False))
        self.addOutput(OutputVector(self.OUT_CF_SHP, self.tr('Shapefile of elements')))

    def processAlgorithm(self, progress):
        m = self.get_mesh(self.IN_CF_MESH)

        fld = QgsField("elem_id", QVariant.Int)
        fields = QgsFields()
        fields.append(fld)
        geomType = QGis.WKBPolygon
        writer = self.getOutputFromName(self.OUT_CF_SHP).getVectorWriter(fields.toList(), geomType, None)

        for elem in m.elements():
            if elem.is_valid():    # at least 2 nodes
                f = QgsFeature()
                f.setFields(fields)
                f.setGeometry(geom(elem, m))
                f[0] = elem.e_id()
                writer.addFeature(f)
