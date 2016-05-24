from PyQt4.QtCore import QSettings
from qgis.core import QgsVectorFileWriter

from processing.core.GeoAlgorithm import GeoAlgorithm
from processing.core.parameters import ParameterFile, ParameterNumber
from processing.core.outputs import OutputVector
from processing.tools import dataobjects, vector

from ..core import Mesh

class InfoAlgorithm(GeoAlgorithm):
    CF_LAYER = 'CRAYFISH_INPUT_LAYER'
    OUTPUT_NELEM = "CRAYFISH_NELEMENTS"
    OUTPUT_NNODE = "CRAYFISH_NNODES"

    def defineCharacteristics(self):
        self.name, self.i18n_name = self.trAlgorithm('Get information about crayfish mesh')
        self.group, self.i18n_group = self.trAlgorithm('Mesh analysis')
        self.addParameter(ParameterFile(self.CF_LAYER, self.tr('Crayfish layer'), optional=False))
        self.addOutput(ParameterNumber(self.OUTPUT_NELEM, self.tr('Number of elements'), optional=False))
        self.addOutput(ParameterNumber(self.OUTPUT_NNODE, self.tr('Number of nodes'), optional=False))

    def processAlgorithm(self, progress):
        inputFilename = self.getParameterValue(self.CF_LAYER)
        nelem = self.getOutputValue(self.OUTPUT_NELEM)
        nnode = self.getOutputValue(self.OUTPUT_NNODE)

        # Input layers vales are always a string with its location.
        # That string can be converted into a QGIS object (a
        # QgsVectorLayer in this case) using the
        # processing.getObjectFromUri() method.
        # vectorLayer = dataobjects.getObjectFromUri(inputFilename)
        cf_mesh = Mesh(inputFilename)
        nelem = cf_mesh.element_count()
        nnode = cf_mesh.node_count()

        print nelem, nnode
        
