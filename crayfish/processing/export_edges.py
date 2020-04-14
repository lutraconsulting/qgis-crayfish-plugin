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

from qgis.core import (QgsMeshDatasetGroupMetadata,
                       QgsWkbTypes,
                       QgsGeometry,
                       QgsPolygon,
                       QgsLineString)

from .mesh_export import CfMeshExportAlgorithm


class ExportEdgesAlgorithm(CfMeshExportAlgorithm):

    def name(self):
        return 'CrayfishExportMeshEdges'

    def displayName(self):
        return 'Export mesh edges'

    def filter_dataset(self, meta):
        return meta.dataType() == QgsMeshDatasetGroupMetadata.DataOnEdges

    def export_geometry_type(self):
        return QgsWkbTypes.LineString

    def export_objects_count(self, mesh):
        return mesh.edgeCount()

    def get_mesh_geometry(self, mesh, index):
        edge = mesh.edge(index)
        start_point = mesh.vertex(edge.first)
        end_point = mesh.vertex(edge.second)
        line = QgsLineString(start_point, end_point)
        return QgsGeometry(line)
