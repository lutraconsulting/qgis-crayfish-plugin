from PyQt4.QtCore import QSettings
from qgis.core import QgsVectorFileWriter

from processing.core.GeoAlgorithm import GeoAlgorithm
from processing.core.parameters import ParameterFile
from processing.core.outputs import OutputNumber
from processing.tools import dataobjects, vector

from ..core import Mesh
from .cf_error import CrayfishProccessingAlgorithmError

class InfoAlgorithm(GeoAlgorithm):
    CF_LAYER = 'CRAYFISH_INPUT_LAYER'
    OUTPUT_NELEM = "CRAYFISH_NELEMENTS"
    OUTPUT_NNODE = "CRAYFISH_NNODES"

    def defineCharacteristics(self):
        self.name, self.i18n_name = self.trAlgorithm('Get information about crayfish mesh')
        self.group, self.i18n_group = self.trAlgorithm('Mesh analysis')
        self.addParameter(ParameterFile(self.CF_LAYER, self.tr('Crayfish layer'), optional=False))
        self.addOutput(OutputNumber(self.OUTPUT_NELEM, self.tr('Number of elements')))
        self.addOutput(OutputNumber(self.OUTPUT_NNODE, self.tr('Number of nodes')))

    def processAlgorithm(self, progress):
        inputFilename = self.getParameterValue(self.CF_LAYER)
        try:
            cf_mesh = Mesh(inputFilename)
        except ValueError:
            raise CrayfishProccessingAlgorithmError("Unable to load mesh")

        nelem = self.getOutputValue(self.OUTPUT_NELEM)
        nnode = self.getOutputValue(self.OUTPUT_NNODE)
        nelem = cf_mesh.element_count()
        nnode = cf_mesh.node_count()


