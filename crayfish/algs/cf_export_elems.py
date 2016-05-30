from PyQt4.QtCore import QSettings, QVariant
from qgis.core import QgsVectorFileWriter, QgsField, QgsFields

from qgis.core import QgsApplication, QgsVectorLayer, QgsPoint, QgsGeometry, QgsFeature, QGis

from processing.core.GeoAlgorithm import GeoAlgorithm
from processing.core.parameters import ParameterFile, ParameterVector
from processing.core.outputs import OutputVector
from processing.tools import dataobjects, vector

from ..core import Mesh
from .cf_error import CrayfishProccessingAlgorithmError

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

class ExportMeshElemsAlgorithm(GeoAlgorithm):
    IN_CF_MESH = 'CF_MESH'
    OUT_CF_SHP = "CF_SHP"

    def defineCharacteristics(self):
        self.name, self.i18n_name = self.trAlgorithm('Export mesh elements')
        self.group, self.i18n_group = self.trAlgorithm('Mesh analysis')
        self.addParameter(ParameterFile(self.IN_CF_MESH, self.tr('Crayfish Mesh'), optional=False))
        self.addOutput(OutputVector(self.OUT_CF_SHP, self.tr('Shapefile of elements')))

    def processAlgorithm(self, progress):
        inFile = self.getParameterValue(self.IN_CF_MESH)
        try:
            m = Mesh(inFile)
        except ValueError:
            raise CrayfishProccessingAlgorithmError("Unable to load mesh")

        fld = QgsField("elem_id", QVariant.Int)
        fields = QgsFields()
        fields.append(fld)
        geomType = QGis.WKBPolygon
        writer = self.getOutputFromName(self.OUT_CF_SHP).getVectorWriter(fields.toList(), geomType, None)

        for elem in m.elements():
            nelements = 0
            if elem.is_valid(): #at least 2 nodes
                f = QgsFeature()
                f.setFields(fields)
                f.setGeometry(geom(elem, m))
                f[0] = elem.e_id()
                writer.addFeature(f)
                nelements += 1

        print("{}/{} elements".format(nelements, m.element_count()))
