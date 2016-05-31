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


from PyQt4.QtCore import QSettings, QVariant
from qgis.core import QgsVectorFileWriter, QgsField, QgsFields

from qgis.core import QgsApplication, QgsVectorLayer, QgsPoint, QgsGeometry, QgsFeature, QGis


from processing.core.parameters import ParameterFile, ParameterVector
from processing.core.outputs import OutputVector
from processing.tools import dataobjects, vector

from .cf_alg import CfGeoAlgorithm

class ExportMeshNodesAlgorithm(CfGeoAlgorithm):
    IN_CF_MESH = 'CF_MESH'
    OUT_CF_SHP = "CF_SHP"

    def defineCharacteristics(self):
        self.name, self.i18n_name = self.trAlgorithm('Export mesh nodes')
        self.group, self.i18n_group = self.trAlgorithm('Mesh and Bed Elevation')
        self.addParameter(ParameterFile(self.IN_CF_MESH, self.tr('Crayfish Mesh'), optional=False))
        self.addOutput(OutputVector(self.OUT_CF_SHP, self.tr('Shapefile of node points')))

    def processAlgorithm(self, progress):
        m = self.get_mesh(self.IN_CF_MESH)
        o = self.get_bed_elevation(m)

        fldId = QgsField("node_id", QVariant.Int)
        fldVal = QgsField("value", QVariant.Double)
        fields = QgsFields()
        fields.append(fldId)
        fields.append(fldVal)
        geomType = QGis.WKBPoint
        writer = self.getOutputFromName(self.OUT_CF_SHP).getVectorWriter(fields.toList(), geomType, None)

        for index, n in enumerate(m.nodes()):
            f = QgsFeature()
            f.setFields(fields)
            f.setGeometry(QgsGeometry.fromPoint(QgsPoint(n.x(), n.y())))
            f[0] = n.n_id()
            f[1] = o.value(index)
            writer.addFeature(f)
