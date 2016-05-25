from PyQt4.QtCore import QSettings, QVariant
from qgis.core import QgsVectorFileWriter, QgsField

from qgis.core import QgsApplication, QgsVectorLayer, QgsPoint, QgsGeometry, QgsFeature, QGis

from processing.core.GeoAlgorithm import GeoAlgorithm
from processing.core.parameters import ParameterFile, ParameterVector
from processing.core.outputs import OutputVector
from processing.tools import dataobjects, vector

from ..core import Mesh
from .cf_error import CrayfishProccessingAlgorithmError

def n2pt(node_index, mesh):
  n = mesh.node(node_index)
  return QgsPoint(n.x, n.y)

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


        fields = [QgsField("elem_id", QVariant.Int)]
        geomType = QGis.WKBPolygon
        writer = self.getOutputFromName(self.OUT_CF_SHP).getVectorWriter(fields, geomType, None)


        for elem in m.elements():
            print elem.id
            ring = []
            ring.append(n2pt(elem.p[0], m))
            ring.append(n2pt(elem.p[1], m))
            ring.append(n2pt(elem.p[2], m))
            if elem.type != 2:
                ring.append(n2pt(elem.p[3], m))
            ring.append(n2pt(elem.p[0], m))
            f = QgsFeature()
            f.setFields(fields)
            f.setGeometry(QgsGeometry.fromPolygon([ring]))
            f[0] = elem.id
            writer.addFeature(f)
