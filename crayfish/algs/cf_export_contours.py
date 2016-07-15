from .cf_alg import CfGeoAlgorithm
from processing.core.outputs import OutputVector
from processing.core.parameters import ParameterFile, ParameterNumber, ParameterCrs, ParameterBoolean

class ExportContoursAlgorithm(CfGeoAlgorithm):
    IN_CF_MESH = 'CF_MESH'
    IN_CF_MUPP = 'CF_MUPP'
    IN_CF_CRS = 'CF_CRS'
    IN_CF_INTERVAL = 'CF_INT'
    IN_CF_LINES = 'CF_USE_LINES'
    OUT_CF_SHP = "CF_SHP"

    def defineCharacteristics(self):
        self.name, self.i18n_name = self.trAlgorithm('Export contours')
        self.group, self.i18n_group = self.trAlgorithm('Mesh and Bed Elevation')

        self.addParameter(ParameterFile(self.IN_CF_MESH, self.tr('Crayfish Mesh'), optional=False))
        self.addParameter(ParameterNumber(self.IN_CF_MUPP, self.tr('Grid resolution'), default=5))
        self.addParameter(ParameterNumber(self.IN_CF_INTERVAL, self.tr('Contours interval'), default=1))
        self.addParameter(ParameterCrs(self.IN_CF_CRS, self.tr('CRS')))
        self.addParameter(ParameterBoolean(self.IN_CF_LINES, self.tr('Use lines'), default=True))
        self.addOutput(OutputVector(self.OUT_CF_SHP, self.tr('Contours shapefile')))

    def processAlgorithm(self, progress):
        m = self.get_mesh(self.IN_CF_MESH)
        o = self.get_bed_elevation(m)

        outf = self.getOutputValue(self.OUT_CF_SHP)
        mupp = self.getParameterValue(self.IN_CF_MUPP)
        use_lines = self.getParameterValue(self.IN_CF_LINES)
        interval = self.getParameterValue(self.IN_CF_INTERVAL)
        crs = self.getParameterValue(self.IN_CF_CRS)

        res = o.export_contours(mupp,
                                interval,
                                outf,
                                crs,
                                use_lines,
                                None)
        if not res:
            raise CrayfishProccessingAlgorithmError("Unable to export contours")
