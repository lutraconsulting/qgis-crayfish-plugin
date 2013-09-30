from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *

from crayfish_viewer_render_settings import *
from crayfishviewer import CrayfishViewer

import os


class CrayfishViewerPluginLayer(QgsPluginLayer):

    LAYER_TYPE="crayfish_viewer"

    def __init__(self, meshFileName=None):
        QgsPluginLayer.__init__(self, CrayfishViewerPluginLayer.LAYER_TYPE, "Crayfish Viewer plugin layer")
        self.meshLoaded = False
        self.datFileNames = []
        if meshFileName is not None:
            self.loadMesh(meshFileName)
        
    
    def loadMesh(self, meshFileName):
        self.provider = CrayfishViewer(meshFileName)
        if self.provider.loadedOk():
            self.setValid(True)
        else:
            self.setValid(False)
        self.dock = None
        self.twoDMFileName = ''
        self.dataSetIdx = 0
        self.timeIdx = 0
        self.rs = CrayfishViewerRenderSettings()
        self.meshLoaded = True
        
        # Properly set the extents
        e = self.provider.getExtents()
        r = QgsRectangle(   QgsPoint( e.bottomLeft().x(), e.bottomLeft().y() ),
                            QgsPoint( e.topRight().x(), e.topRight().y() ) )
        self.setExtent(r)
        
        self.set2DMFileName(meshFileName) # Set the 2dm file name
        
        head, tail = os.path.split(meshFileName)
        layerName, ext = os.path.splitext(tail)
        self.setLayerName(layerName)
        
        
    def readXml(self, node):
        twoDmFile = str( node.toElement().attribute('meshfile') )
        self.loadMesh(twoDmFile)
        datNodes = node.toElement().elementsByTagName("dat")
        for i in xrange(datNodes.length()):
            datNode = datNodes.item(i)
            datFilePath = datNode.toElement().attribute('path')
            if not self.provider.loadDataSet(datFilePath):
                return False
            self.addDatFileName(datFilePath)
        return True


    def writeXml(self, node, doc):
        element = node.toElement();
        # write plugin layer type to project (essential to be read from project)
        element.setAttribute("type", "plugin")
        element.setAttribute("name", CrayfishViewerPluginLayer.LAYER_TYPE)
        element.setAttribute("meshfile", self.twoDMFileName)
        for datFile in self.datFileNames:
            ch = doc.createElement("dat")
            ch.setAttribute("path", datFile);
            element.appendChild(ch)
        return True
            

    def set2DMFileName(self, fName):
        self.twoDMFileName = fName
    
    def addDatFileName(self, fName):
        self.datFileNames.append(fName)
    
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
        
    def identify(self, pt):
        """
            Returns a QString representing the value of the layer at 
            the given QgsPoint, pt
            
            This function calls valueAtCoord in the C++ provider
            
            double valueAtCoord(int dataSetIdx, 
                                int timeIndex, 
                                double xCoord, 
                                double yCoord);
        """
        
        x = pt.x()
        y = pt.y()
        
        # Determine what scalar data is currently being displayed
        dataSetIdx = self.dock.listWidget.currentRow()
        timeIndex = self.dock.listWidget_2.currentRow()
        
        value = self.provider.valueAtCoord( dataSetIdx, 
                                            timeIndex, 
                                            x, y)
        v = None
        if value == -9999.0:
            # Outide extent
            v = QString('out of extent')
        else:
            v = QString(str(value))
            
        d = dict()
        d[ QString('Band 1') ] = v
        
        return (True, d)
        
    def bandCount(self):
        return 1
        
    def rasterUnitsPerPixel(self):
        # Only required so far for the profile tool
        # There's probably a better way of doing this
        return float(0.5)
