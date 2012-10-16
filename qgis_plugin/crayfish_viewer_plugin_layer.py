from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *

from crayfish_viewer_render_settings import *
from crayfishviewer import CrayfishViewer


class CrayfishViewerPluginLayer(QgsPluginLayer):

    LAYER_TYPE="crayfish_viewer"

    def __init__(self, datFileName):
        QgsPluginLayer.__init__(self, CrayfishViewerPluginLayer.LAYER_TYPE, "Crayfish Viewer plugin layer")
        self.provider = CrayfishViewer(datFileName)
        if self.provider.loadedOk():
            self.setValid(True)
        else:
            self.setValid(False)
        self.dock = None
        self.twoDMFileName = ''
        self.dataSetIdx = 0
        self.timeIdx = 0
        self.rs = CrayfishViewerRenderSettings()
            

    def set2DMFileName(self, fName):
        self.twoDMFileName = fName
    
    def setDock(self, dock):
        self.dock = dock
        
    def setRenderSettings(self, dataSetIdx, timeIdx):
        self.dataSetIdx = dataSetIdx
        self.timeIdx = timeIdx
    
    def draw(self, rendererContext):
        
        """
            The provider (CrayfishViewer) provides the following draw function:
            
            QImage* draw(   int canvasWidth, 
                            int canvasHeight, 
                            double llX, 
                            double llY, 
                            double pixelSize)
        """
        
        debug = False
        
        mapToPixel = rendererContext.mapToPixel()
        pixelSize = mapToPixel.mapUnitsPerPixel()
        extent = rendererContext.extent()
        topleft = mapToPixel.transform(extent.xMinimum(), extent.yMaximum())
        bottomright = mapToPixel.transform(extent.xMaximum(), extent.yMinimum())
        width = (bottomright.x() - topleft.x())
        height = (bottomright.y() - topleft.y())
        
        if debug:
            print '\n'
            print 'About to render with the following parameters:'
            print '\tWidth:\t' + str(width) + '\n'
            print '\tHeight:\t' + str(height) + '\n'
            print '\tXMin:\t' + str(extent.xMinimum()) + '\n'
            print '\tYMin:\t' + str(extent.yMinimum()) + '\n'
            print '\tPixSz:\t' + str(pixelSize) + '\n'
            
        if self.dock is not None:
            timeIndex = self.dock.listWidget_2.currentRow()
        else:
            timeIndex = 0
            
        if self.dock is None:
            autoContour = True
            contMin = 0.0
            contMax = 0.0
        else:
            autoContour, contMin, contMax = self.dock.getRenderOptions()
            
        img = self.provider.draw(   self.rs.renderContours, # Whether to render contours
                                    self.rs.renderVectors,  # Whether to render vectors
                                    width,                  # The width of the QImage to return in px
                                    height,                 # The height of the QImage to return in px
                                    extent.xMinimum(),      # x coordinate of the XLL corner
                                    extent.yMinimum(),      # y coordinate of the XLL corner
                                    pixelSize,              # Size of pixels in map units
                                    self.dataSetIdx,        # Dataset index (0=2dm)
                                    self.timeIdx,           # Output index
                                    
                                                            # Contour options
                                    autoContour,            # Can't remember what this is
                                    contMin,                # Minimum contour value
                                    contMax,                # Maximum contour value
                                    
                                                                    # Vector options
                                    self.rs.shaftLength,            # Method used to scale the shaft (sounds rude doesn't it)
                                    self.rs.shaftLengthMin,         # Minimum shaft length
                                    self.rs.shaftLengthMax,         # Maximum shaft length
                                    self.rs.shaftLengthScale,       # Scale for scaling vector to magnitude
                                    self.rs.shaftLengthFixedLength, # Fixed vector length
                                    self.rs.lineWidth,              # Line width to use for rendering
                                    self.rs.headWidth,              # Vector head width (%)
                                    self.rs.headLength              # Vector head length (%)
                                    )
                                    
                                    
        # img now contains the render of the crayfish layer, merge it
        
        painter = rendererContext.painter()
        rasterScaleFactor = rendererContext.rasterScaleFactor()
        invRasterScaleFactor = 1.0/rasterScaleFactor
        painter.save()
        painter.scale(invRasterScaleFactor, invRasterScaleFactor)
        painter.drawImage(0, 0, img)
        painter.restore()
        return True

