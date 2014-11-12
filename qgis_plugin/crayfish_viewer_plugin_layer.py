# -*- coding: utf-8 -*-

# Crayfish - A collection of tools for TUFLOW and other hydraulic modelling packages
# Copyright (C) 2014 Lutra Consulting

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

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
from crayfish_gui_utils import QgsMessageBar, qgis_message_bar, qv2pyObj, qv2float, qv2int, qv2bool, qv2string, defaultColorRamp
from qgis.utils import iface

from crayfishviewer import CrayfishViewer, DataSetType, ColorMap

import os
import glob



def qstring2int(s):
    """ return an integer from a string or None on error. Should work with SIP API either 1 or 2 """
    if isinstance(s, unicode):
        try:
            return int(s)
        except ValueError:
            return None
    else:   # QString (API v1)
        res = s.toInt()
        return res[0] if res[1] else None

def qstring2bool(s):
    i = qstring2int(s)
    if i is not None:
        i = bool(i)
    return i

def qstring2float(s):
    if isinstance(s, unicode):
        try:
            return float(s)
        except ValueError:
            return None
    else:  # QString (API v2)
        res = s.toDouble()
        return res[0] if res[1] else None

def qstring2rgb(s):
    r,g,b = s.split(",")
    return qRgb(int(r),int(g),int(b))


def gradientColorRampStop(ramp, i):
    stops = ramp.stops()
    if isinstance(stops, dict):  # QGIS 1.8 returns map "value -> color"
      keys = sorted(stops.keys())
      key = keys[i]
      return (key, stops[key])
    else:  # QGIS 2.0 returns list of structures
      return (stops[i].offset, stops[i].color)



class CrayfishViewerPluginLayer(QgsPluginLayer):

    LAYER_TYPE="crayfish_viewer"

    def __init__(self, meshFileName=None):
        QgsPluginLayer.__init__(self, CrayfishViewerPluginLayer.LAYER_TYPE, "Crayfish Viewer plugin layer")
        self.meshLoaded = False
        if meshFileName is not None:
            self.loadMesh(meshFileName)


    def loadMesh(self, meshFileName):
        meshFileName = unicode(meshFileName)
        self.provider = CrayfishViewer(meshFileName)
        if self.provider.loadedOk():
            self.setValid(True)
        else:
            self.setValid(False)
            return
        self.twoDMFileName = ''
        self.meshLoaded = True
        
        # Properly set the extents
        e = self.provider.meshExtent()
        r = QgsRectangle(   QgsPoint( e.left(), e.top() ),
                            QgsPoint( e.right(), e.bottom() ) )
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

        self.initCustomValues(self.provider.dataSet(0)) # bed


    def showMeshLoadError(self, twoDMFileName):
        e = self.provider.getLastError()
        if e == CrayfishViewer.Err_NotEnoughMemory:
          qgis_message_bar.pushMessage("Crayfish", "Not enough memory to open the mesh file (" + twoDMFileName + ").", level=QgsMessageBar.CRITICAL)
        elif e == CrayfishViewer.Err_FileNotFound:
          qgis_message_bar.pushMessage("Crayfish", "Failed to open the mesh file (" + twoDMFileName + ").", level=QgsMessageBar.CRITICAL)
        elif e == CrayfishViewer.Err_UnknownFormat:
          qgis_message_bar.pushMessage("Crayfish", "Mesh file format not recognized (" + twoDMFileName + ").", level=QgsMessageBar.CRITICAL)


    def initCustomValues(self, ds):
        """ set defaults for data source """
        ds.setCustomValue("c_basic", True)
        ds.setCustomValue("c_basicCustomRange", False)
        ds.setCustomValue("c_basicCustomRangeMin", ds.minZValue())
        ds.setCustomValue("c_basicCustomRangeMax", ds.maxZValue())
        ds.setCustomValue("c_basicName", "[default]")
        ds.setCustomValue("c_basicRamp", defaultColorRamp())
        ds.setCustomValue("c_alpha", 255)
        ds.setCustomValue("c_advancedColorMap", ColorMap.defaultColorMap(ds.minZValue(), ds.maxZValue()))
        self.updateColorMap(ds)  # make sure to apply the settings to form a color map

        
    def readXml(self, node):
        element = node.toElement()
        prj = QgsProject.instance()

        # load mesh
        twoDmFile = prj.readPath( element.attribute('meshfile') )
        self.loadMesh(twoDmFile)

        if not self.isValid():
            self.showMeshLoadError(twoDmFile)
            return False

        # load bed settings
        bedElem = element.firstChildElement("bed")
        if not bedElem.isNull():
          ds = self.provider.dataSet(0)
          self.readDataSetXml(ds, bedElem)

        # load data files
        datNodes = element.elementsByTagName("dat")
        for i in xrange(datNodes.length()):
            datElem = datNodes.item(i).toElement()
            datFilePath = prj.readPath( datElem.attribute('path') )
            if not self.provider.loadDataSet(datFilePath):
                qgis_message_bar.pushMessage("Crayfish", "Unable to load dataset " + datFilePath, level=QgsMessageBar.WARNING)
                continue
            ds = self.provider.dataSet(self.provider.dataSetCount()-1)
            self.readDataSetXml(ds, datElem)

            currentOutput = qstring2int(datElem.attribute("current-output"))
            if currentOutput is not None:
                ds.setCurrentOutputTime(currentOutput)


        # load settings
        currentDataSetIndex = qstring2int(element.attribute("current-dataset"))
        if currentDataSetIndex is not None:
            self.provider.setCurrentDataSetIndex(currentDataSetIndex)

        # mesh rendering
        meshElem = element.firstChildElement("render-mesh")
        if not meshElem.isNull():
            meshRendering = qstring2bool(meshElem.attribute("enabled"))
            if meshRendering is not None:
                self.provider.setMeshRenderingEnabled(meshRendering)
            meshColor = qstring2rgb(meshElem.attribute("color"))
            if meshColor is not None:
                self.provider.setMeshColor(QColor(meshColor))

        return True


    def writeXml(self, node, doc):
        prj = QgsProject.instance()
        element = node.toElement();
        # write plugin layer type to project (essential to be read from project)
        element.setAttribute("type", "plugin")
        element.setAttribute("name", CrayfishViewerPluginLayer.LAYER_TYPE)
        element.setAttribute("meshfile", prj.writePath(self.twoDMFileName))
        element.setAttribute("current-dataset", self.provider.currentDataSetIndex())
        meshElem = doc.createElement("render-mesh")
        meshElem.setAttribute("enabled", "1" if self.provider.isMeshRenderingEnabled() else "0")
        clr = self.provider.meshColor()
        meshElem.setAttribute("color", "%d,%d,%d" % (clr.red(), clr.green(), clr.blue()))
        element.appendChild(meshElem)

        for i in range(self.provider.dataSetCount()):
            ds = self.provider.dataSet(i)
            if ds.type() == DataSetType.Bed:
                dsElem = doc.createElement("bed")
            else:
                dsElem = doc.createElement("dat")
                dsElem.setAttribute("path", prj.writePath(ds.fileName()))
                dsElem.setAttribute("current-output", ds.currentOutputTime())
            self.writeDataSetXml(ds, dsElem, doc)
            element.appendChild(dsElem)

        return True

    def readDataSetXml(self, ds, elem):

        self.initCustomValues(ds)

        # contour options
        contElem = elem.firstChildElement("render-contour")
        if not contElem.isNull():
            enabled = qstring2bool(contElem.attribute("enabled"))
            if enabled is not None:
                ds.setContourRenderingEnabled(enabled)
            alpha = qstring2int(contElem.attribute("alpha"))
            if alpha is not None:
                ds.setCustomValue("c_alpha", alpha)
            isBasic = qstring2bool(contElem.attribute("basic"))
            if isBasic is not None:
                ds.setCustomValue("c_basic", isBasic)
            autoRange = qstring2bool(contElem.attribute("auto-range"))
            if autoRange is not None:
                ds.setCustomValue("c_basicCustomRange", not autoRange)
            rangeMin = qstring2float(contElem.attribute("range-min"))
            rangeMax = qstring2float(contElem.attribute("range-max"))
            if rangeMin is not None and rangeMax is not None:
                ds.setCustomValue("c_basicCustomRangeMin", rangeMin)
                ds.setCustomValue("c_basicCustomRangeMax", rangeMax)

            # read color ramp (basic)
            rampElem = contElem.firstChildElement("colorramp")
            if not rampElem.isNull():
                ramp = QgsSymbolLayerV2Utils.loadColorRamp(rampElem)
                ds.setCustomValue("c_basicRamp", ramp)
                rampName = rampElem.attribute("name")
                ds.setCustomValue("c_basicName", rampName)

            # read color map (advanced)
            advElem = contElem.firstChildElement("advanced")
            if not advElem.isNull():
                cm = self.readColorMapXml(advElem)
                if cm:
                    ds.setCustomValue("c_advancedColorMap", cm)

            self.updateColorMap(ds)

        # vector options (if applicable)
        if ds.type() == DataSetType.Vector:
            vectElem = elem.firstChildElement("render-vector")
            enabled = qstring2bool(vectElem.attribute("enabled"))
            if enabled is not None:
                ds.setVectorRenderingEnabled(enabled)
            method = qstring2int(vectElem.attribute("method"))
            if method is not None:
                ds.setVectorShaftLengthMethod(method)
            shaftLengthMin = qstring2float(vectElem.attribute("shaft-length-min"))
            shaftLengthMax = qstring2float(vectElem.attribute("shaft-length-max"))
            if shaftLengthMin is not None and shaftLengthMax is not None:
                ds.setVectorShaftLengthMinMax(shaftLengthMin, shaftLengthMax)
            shaftLengthScale = qstring2float(vectElem.attribute("shaft-length-scale"))
            if shaftLengthScale is not None:
                ds.setVectorShaftLengthScaleFactor(shaftLengthScale)
            shaftLengthFixed = qstring2float(vectElem.attribute("shaft-length-fixed"))
            if shaftLengthFixed is not None:
                ds.setVectorShaftLengthFixed(shaftLengthFixed)
            penWidth = qstring2float(vectElem.attribute("pen-width"))
            if penWidth is not None:
                ds.setVectorPenWidth(penWidth)
            headWidth = qstring2float(vectElem.attribute("head-width"))
            headLength = qstring2float(vectElem.attribute("head-length"))
            if headWidth is not None and headLength is not None:
                ds.setVectorHeadSize(headWidth, headLength)

    def writeDataSetXml(self, ds, elem, doc):

        # contour options
        contElem = doc.createElement("render-contour")
        contElem.setAttribute("enabled", "1" if ds.isContourRenderingEnabled() else "0")
        contElem.setAttribute("alpha", qv2int(ds.customValue("c_alpha")))
        contElem.setAttribute("basic", "1" if qv2bool(ds.customValue("c_basic")) else "0")
        contElem.setAttribute("auto-range", "1" if not qv2bool(ds.customValue("c_basicCustomRange")) else "0")
        contElem.setAttribute("range-min", str(qv2float(ds.customValue("c_basicCustomRangeMin"))))
        contElem.setAttribute("range-max", str(qv2float(ds.customValue("c_basicCustomRangeMax"))))

        rampName = qv2string(ds.customValue("c_basicName"))
        ramp = qv2pyObj(ds.customValue("c_basicRamp"))
        if ramp:
            rampElem = QgsSymbolLayerV2Utils.saveColorRamp(rampName, ramp, doc)
            contElem.appendChild(rampElem)
        elem.appendChild(contElem)

        advElem = doc.createElement("advanced")
        self.writeColorMapXml(qv2pyObj(ds.customValue("c_advancedColorMap")), advElem, doc)
        contElem.appendChild(advElem)

        # vector options (if applicable)
        if ds.type() == DataSetType.Vector:
          vectElem = doc.createElement("render-vector")
          vectElem.setAttribute("enabled", "1" if ds.isVectorRenderingEnabled() else "0")
          vectElem.setAttribute("method", ds.vectorShaftLengthMethod())
          vectElem.setAttribute("shaft-length-min", str(ds.vectorShaftLengthMin()))
          vectElem.setAttribute("shaft-length-max", str(ds.vectorShaftLengthMax()))
          vectElem.setAttribute("shaft-length-scale", str(ds.vectorShaftLengthScaleFactor()))
          vectElem.setAttribute("shaft-length-fixed", str(ds.vectorShaftLengthFixed()))
          vectElem.setAttribute("pen-width", str(ds.vectorPenWidth()))
          vectElem.setAttribute("head-width", str(ds.vectorHeadWidth()))
          vectElem.setAttribute("head-length", str(ds.vectorHeadLength()))
          elem.appendChild(vectElem)


    def readColorMapXml(self, elem):

        cmElem = elem.firstChildElement("colormap")
        if cmElem.isNull():
            return
        cm = ColorMap()
        cm.method = ColorMap.Discrete if cmElem.attribute("method") == "discrete" else ColorMap.Linear
        cm.clipLow  = cmElem.attribute("clip-low")  == "1"
        cm.clipHigh = cmElem.attribute("clip-high") == "1"
        itemElems = cmElem.elementsByTagName("item")
        for i in range(itemElems.length()):
            itemElem = itemElems.item(i).toElement()
            value = qstring2float(itemElem.attribute("value"))
            color = qstring2rgb(itemElem.attribute("color"))
            cm.addItem(ColorMap.Item(value, color))
        return cm


    def writeColorMapXml(self, cm, parentElem, doc):

        elem = doc.createElement("colormap")
        elem.setAttribute("method", "discrete" if cm.method == ColorMap.Discrete else "linear")
        elem.setAttribute("clip-low",  "1" if cm.clipLow  else "0")
        elem.setAttribute("clip-high", "1" if cm.clipHigh else "0")
        for item in cm.items:
            itemElem = doc.createElement("item")
            itemElem.setAttribute("value", str(item.value))
            c = QColor(item.color)
            itemElem.setAttribute("color", "%d,%d,%d" % (c.red(), c.green(), c.blue()))
            elem.appendChild(itemElem)
        parentElem.appendChild(elem)


    def set2DMFileName(self, fName):
        self.twoDMFileName = fName


    def updateColorMap(self, ds):
        """ update color map of the current data set given the settings """

        if not qv2bool(ds.customValue("c_basic")):
            cm = qv2pyObj(ds.customValue("c_advancedColorMap"))
        else:
            cm = self._colorMapBasic(ds)

        if not cm:
            return

        cm.alpha = qv2int(ds.customValue("c_alpha"))
        ds.setContourColorMap(cm)

        iface.legendInterface().refreshLayerSymbology(self)


    def _colorMapBasic(self, ds):

        # contour colormap
        if qv2bool(ds.customValue("c_basicCustomRange")):
            zMin = qv2float(ds.customValue("c_basicCustomRangeMin"))
            zMax = qv2float(ds.customValue("c_basicCustomRangeMax"))
        else:
            zMin = ds.minZValue()
            zMax = ds.maxZValue()

        qcm = qv2pyObj(ds.customValue("c_basicRamp"))
        if not qcm:
            return   # something went wrong (e.g. user selected "new color ramp...")

        # if the color ramp is a gradient, we will use the defined stops
        # otherwise (unknown type of color ramp) we will just take few samples

        isGradient = isinstance(qcm, QgsVectorGradientColorRampV2)

        cm = ColorMap()
        count = qcm.count() if isGradient else 5
        for i in range(count):
          if isGradient:
            if i == 0: v,c = 0.0, qcm.color1()
            elif i == count-1: v,c = 1.0, qcm.color2()
            else: v,c = gradientColorRampStop(qcm, i-1)
          else:
            v = i/float(count-1)
            c = qcm.color(v)
          vv = zMin + v*(zMax-zMin)
          cm.addItem(ColorMap.Item(vv,c.rgb()))

        return cm

    
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
            
        self.provider.setCanvasSize(QSize(int(width), int(height)))
        self.provider.setExtent(extent.xMinimum(), extent.yMinimum(), pixelSize)

        mr = iface.mapCanvas().mapRenderer()
        projEnabled = mr.hasCrsTransformEnabled()
        if projEnabled:
          res = self.provider.setProjection(self.crs().toProj4(), mr.destinationCrs().toProj4())
          if not res:
            qgis_message_bar.pushMessage("Crayfish", "Failed to reproject the mesh!", level=QgsMessageBar.WARNING)
        else:
          self.provider.setNoProjection()

        ds = self.provider.currentDataSet()
        if not ds:
            return False

        img = self.provider.draw()
        if not img:
            return False

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
            
            double valueAtCoord(const Output* output,
                                double xCoord, 
                                double yCoord);
        """
        
        x = pt.x()
        y = pt.y()
        
        outputOfInterest = self.provider.currentDataSet().currentOutput()
        value = self.provider.valueAtCoord( outputOfInterest, x, y)
        
        v = None
        if value == -9999.0:
            # Outide extent
            try:
                v = QString('out of extent')
            except:
                v = 'out of extent'
        else:
            try:
                v = QString(str(value))
            except:
                v = str(value)
            
        d = dict()
        try:
            d[ QString('Band 1') ] = v
        except:
            d[ 'Band 1' ] = v
        
        return (True, d)
        
    def bandCount(self):
        return 1
        
    def rasterUnitsPerPixel(self):
        # Only required so far for the profile tool
        # There's probably a better way of doing this
        return float(0.5)
    
    def rasterUnitsPerPixelX(self):
        # Only required so far for the profile tool
        return self.rasterUnitsPerPixel()
    
    def rasterUnitsPerPixelY(self):
        # Only required so far for the profile tool
        return self.rasterUnitsPerPixel()


    def legendSymbologyItems(self, iconSize):
        """ implementation of method from QgsPluginLayer to show legend entries (in QGIS >= 2.1) """
        ds = self.provider.currentDataSet()
        lst = [ (ds.name(), QPixmap()) ]
        if not ds.isContourRenderingEnabled():
            return lst

        cm = ds.contourColorMap()
        for item in cm.items:
            pix = QPixmap(iconSize)
            pix.fill(QColor(item.color))
            lst.append( ("%.3f" % item.value, pix) )
        return lst
