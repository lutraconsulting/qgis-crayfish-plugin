from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
from qgis.utils import iface

from crayfish_viewer_render_settings import *
from crayfishviewer import CrayfishViewer

import os
import glob


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

        # try to load .prj file from the same directory
        crs = QgsCoordinateReferenceSystem()
        meshDir = os.path.dirname(meshFileName)
        prjFiles = glob.glob(meshDir + os.path.sep + '*.prj')
        if len(prjFiles) == 1:
            wkt = open(prjFiles[0]).read()
            crs.createFromWkt(wkt)

        crs.validate()  # if CRS is not valid, validate it using user's preference (prompt / use project's CRS / use default CRS)
        self.setCrs(crs)

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
        extent = iface.mapCanvas().mapRenderer().extent() # non-projected map extent # rendererContext.extent()
        topleft = mapToPixel.transform(extent.xMinimum(), extent.yMaximum())
        bottomright = mapToPixel.transform(extent.xMaximum(), extent.yMinimum())
        width = (bottomright.x() - topleft.x())
        height = (bottomright.y() - topleft.y())
        
        if debug:
            print '\n'
            print 'About to render with the following parameters:'
            print '\tExtent:\t%f,%f - %f,%f\n' % (extent.xMinimum(),extent.yMinimum(),extent.xMaximum(),extent.yMaximum())
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

        self.provider.setCanvasSize(QSize(int(width), int(height)))
        self.provider.setExtent(extent.xMinimum(), extent.yMinimum(), pixelSize)
        self.provider.setCurrentDataSetIndex(self.dataSetIdx)

        mr = iface.mapCanvas().mapRenderer()
        projEnabled = mr.hasCrsTransformEnabled()
        if projEnabled:
          self.provider.setProjection(self.crs().authid(), mr.destinationCrs().authid())
        else:
          self.provider.setProjection("", "")

        ds = self.provider.currentDataSet()
        ds.setCurrentOutputTime(self.timeIdx)

        # contour rendering settings
        ds.setContourAutoRange(autoContour)
        ds.setContourCustomRange(contMin, contMax)

        # vector rendering settings
        ds.setVectorShaftLengthMethod(self.rs.shaftLength)  # Method used to scale the shaft (sounds rude doesn't it)
        ds.setVectorShaftLengthMinMax(self.rs.shaftLengthMin, self.rs.shaftLengthMax)
        ds.setVectorShaftLengthScaleFactor(self.rs.shaftLengthScale)
        ds.setVectorShaftLengthFixed(self.rs.shaftLengthFixedLength)
        ds.setVectorPenWidth(self.rs.lineWidth)
        ds.setVectorHeadSize(self.rs.headWidth, self.rs.headLength)

        img = self.provider.draw()

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
