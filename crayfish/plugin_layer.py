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

import os
import glob
import datetime

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
from qgis.utils import iface

from .gui.utils import QgsMessageBar, qgis_message_bar, defaultColorRamp
from .layer_renderer import CrayfishPluginLayerRenderer
from .core import Err, last_load_status, Mesh, ColorMap, DataSet, DATETIME_FMT


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
    lst = s.split(",")
    if len(lst) == 3:
        r,g,b = lst
        a = "255"
    elif len(lst) == 4:
        r,g,b,a = lst
    else:
        raise ValueError, s
    return (int(r),int(g),int(b),int(a))


def qstring2datetime(s):
    try:
        return datetime.datetime.strptime(s, DATETIME_FMT)
    except Exception:
        return None

def qstring2string(s):
    return str(s)

def rgb2string(clr):
    if len(clr) == 3 or (len(clr) == 4 and clr[3] == 255):
        return "%d,%d,%d" % (clr[0], clr[1], clr[2])
    elif len(clr) == 4:
        return "%d,%d,%d,%d" % (clr[0], clr[1], clr[2], clr[3])
    else:
        raise ValueError, clr

def gradientColorRampStop(ramp, i):
    stops = ramp.stops()
    if isinstance(stops, dict):  # QGIS 1.8 returns map "value -> color"
      keys = sorted(stops.keys())
      key = keys[i]
      return (key, stops[key])
    else:  # QGIS 2.0 returns list of structures
      return (stops[i].offset, stops[i].color)

class CrayfishPluginLayer(QgsPluginLayer):

    LAYER_TYPE="crayfish_viewer"

    currentDataSetChanged = pyqtSignal()
    currentOutputTimeChanged = pyqtSignal()

    def __init__(self, meshFileName=None):
        QgsPluginLayer.__init__(self, CrayfishPluginLayer.LAYER_TYPE, "Crayfish plugin layer")

        self.config = {
          'mesh'  : False,
          'm_border_color' : (0,0,0,128),  # black with 50% transparency
          'm_fill_color' : (221,236,240,125),  # blue-ish with 50% transparency
          'm_fill_enabled' : False,
          'm_label_elem' : False,
          'm_border_width': 1 # 1px
        }

        self.lockCurrent = True

        self.renderer = None

        # cache dataset objects - we associate further properties to them
        # so we don't want the object to be deleted while this layer is alive
        self.cached_ds = set()

        # map of renamed dataset names
        # key = dataset index, value = user's dataset name
        self.ds_user_names = {}

        if meshFileName is not None:
            self.loadMesh(meshFileName)

    def setCrs(self, crs):
        """ overload of QgsPluginLayer.setCrs() that also sets source CRS of mesh """
        # call original method
        QgsPluginLayer.setCrs(self, crs)
        # store the final CRS in the mesh (it may have changed during validation)
        self.mesh.set_source_crs(crs.toProj4())

    def setupCRS(self):
        crs = QgsCoordinateReferenceSystem()

        # try to load from mesh projection if set (GDAL)
        srcProj = self.mesh.source_crs()
        if len(srcProj) != 0:
            crs.createFromProj4(srcProj)
        else:
            # try to load .prj file from the same directory
            meshDir = os.path.dirname(self.twoDMFileName)
            prjFiles = glob.glob(meshDir + os.path.sep + '*.prj')
            if len(prjFiles) == 1:
                wkt = open(prjFiles[0]).read()
                crs.createFromWkt(wkt)

        crs.validate()  # if CRS is not valid, validate it using user's preference (prompt / use project's CRS / use default CRS)
        self.setCrs(crs)

    def loadMesh(self, meshFileName):
        meshFileName = unicode(meshFileName)
        try:
            self.mesh = Mesh(meshFileName)
            self.setValid(True)
        except ValueError:
            self.setValid(False)
            return
        self.twoDMFileName = ''

        # Properly set the extents
        e = self.mesh.extent()
        r = QgsRectangle( QgsPoint( e[0], e[1] ),
                          QgsPoint( e[2], e[3] ) )
        self.setExtent(r)

        self.set2DMFileName(meshFileName) # Set the 2dm file name
        if hasattr(self, 'setSource'):  # supported from QGIS 2.16
            self.setSource(meshFileName)

        head, tail = os.path.split(meshFileName)
        layerName, ext = os.path.splitext(tail)
        self.setLayerName(layerName)

        self.setupCRS()

        for i in xrange(self.mesh.dataset_count()):
            self.initCustomValues(self.mesh.dataset(i))

        self.current_ds_index = 0
        self.current_output_time = 0
        self.contour_ds_index = 0
        self.vector_ds_index = -1


    def showMeshLoadError(self, twoDMFileName):
        e = last_load_status()[0]
        if e == Err.NotEnoughMemory:
          qgis_message_bar.pushMessage("Crayfish", "Not enough memory to open the mesh file (" + twoDMFileName + ").", level=QgsMessageBar.CRITICAL)
        elif e == Err.FileNotFound:
          qgis_message_bar.pushMessage("Crayfish", "Failed to open the mesh file (" + twoDMFileName + ").", level=QgsMessageBar.CRITICAL)
        elif e == Err.UnknownFormat:
          qgis_message_bar.pushMessage("Crayfish", "Mesh file format not recognized (" + twoDMFileName + ").", level=QgsMessageBar.CRITICAL)
        elif e == Err.IncompatibleMesh:
          qgis_message_bar.pushMessage("Crayfish", "Incompatible mesh (" + twoDMFileName + ").", level=QgsMessageBar.CRITICAL)
        elif e == Err.InvalidData:
          qgis_message_bar.pushMessage("Crayfish", "Invalid or missing data (" + twoDMFileName + ").", level=QgsMessageBar.CRITICAL)
        elif e == Err.MissingDriver:
          qgis_message_bar.pushMessage("Crayfish", "Missing driver (" + twoDMFileName + ").", level=QgsMessageBar.CRITICAL)

    def currentDataSet(self):
        return self.mesh.dataset(self.current_ds_index)

    def currentOutput(self):
        ds = self.currentDataSet()
        return self.currentOutputForDataset(ds)

    def currentOutputForDataset(self, ds):
        if ds.time_varying():
            index = ds.output_time_index(self.current_output_time)
            if index is None:   # TODO: some warning?
                index = 0
        else:
            index = 0
        return ds.output(index)


    def currentContourDataSet(self):
      if self.contour_ds_index < 0:
          return None
      return self.mesh.dataset(self.contour_ds_index)

    def currentContourOutput(self):
      ds = self.currentContourDataSet()
      if not ds:
          return None
      return self.currentOutputForDataset(ds)

    def currentVectorDataSet(self):
      if self.vector_ds_index < 0:
          return None
      return self.mesh.dataset(self.vector_ds_index)

    def currentVectorOutput(self):
      ds = self.currentVectorDataSet()
      if not ds:
          return None
      return self.currentOutputForDataset(ds)

    def parentDataSet(self, ds):
        ds_name_parts = ds.name().split("/")
        if len(ds_name_parts) == 2:
            for d in self.mesh.datasets():
                if ds_name_parts[0] == d.name():
                    return d


    def initCustomValues(self, ds):
        """ set defaults for data source """
        self.cached_ds.add(ds)

        # make child datasets (maximums) share the configuration with parent
        parent_ds = self.parentDataSet(ds)
        if parent_ds:
            ds.config = parent_ds.config
            ds.custom = parent_ds.custom
            ds.timeConfig = parent_ds.timeConfig
            # maybe also increase range?
            return

        minZ, maxZ = ds.value_range()
        ds.config = {
          "c_colormap" : None,  # will be assigned in updateColorMap() call
          "v_shaft_length_method" : 0, # MinMax
          "v_shaft_length_min" : 3,
          "v_shaft_length_max" : 40,
          "v_shaft_length_scale" : 10,
          "v_shaft_length_fixed" : 10,
          "v_pen_width" : 1,
          "v_head_width" : 15,
          "v_head_length" : 40,
          "v_grid" : False,
          "v_grid_x" : 10,
          "v_grid_y" : 10,
          "v_filter_min": -1,
          "v_filter_max": -1,
          "v_color": (0, 0, 0, 255)   # black
        }
        ds.custom = {
          "c_basic" : True,
          "c_basicCustomRange" : False,
          "c_basicCustomRangeMin" : minZ,
          "c_basicCustomRangeMax" : maxZ,
          "c_basicName" : "[default]",
          "c_basicRamp" : defaultColorRamp(),
          "c_alpha" : 255,
          "c_advancedColorMap" : ColorMap(minZ, maxZ)
        }
        ds.timeConfig = {
            "dt_offset_hours": 0,
            "dt_use_absolute_time": False,
            "dt_reference_time": ds.ref_time(),
            "dt_time_format": "%H:%M:%S",
            "dt_datetime_format": "%d.%m.%Y %H:%M"
        }
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
          ds = self.mesh.dataset(0)
          self.readDataSetXml(ds, bedElem)

        # load data files
        datNodes = element.elementsByTagName("dat")
        for i in xrange(datNodes.length()):
            datElem = datNodes.item(i).toElement()
            datFilePath = prj.readPath( datElem.attribute('path') )
            try:
                if not self.isDataSetLoaded(datFilePath):
                    self.mesh.load_data(datFilePath)
            except ValueError:
                qgis_message_bar.pushMessage("Crayfish", "Unable to load dataset " + datFilePath, level=QgsMessageBar.WARNING)
                continue
            dsName = datElem.attribute("name")
            if len(dsName) != 0:
                # dat files can contain multiple datasets - name identifies which one
                ds = self.mesh.dataset_from_name(dsName)
            else:
                # project file before names started to be used - assuming just one dataset per file
                ds = self.mesh.dataset(self.mesh.dataset_count()-1)

            if ds is None:
                continue  # skip this one

            self.readDataSetXml(ds, datElem)

            dsUserName = datElem.attribute("user-name")
            if len(dsUserName) != 0:
                ds_index = list(self.mesh.datasets()).index(ds)
                self.ds_user_names[ds_index] = dsUserName


        # load settings
        currentDataSetIndex = qstring2int(element.attribute("current-dataset"))
        if currentDataSetIndex is not None:
            self.current_ds_index = currentDataSetIndex

        currentOutputTime = qstring2float(element.attribute("current-output-time"))
        if currentOutputTime is not None:
            self.current_output_time = currentOutputTime

        lockCurrent = qstring2bool(element.attribute("lock-current"))
        if lockCurrent is not None:
            self.lockCurrent = lockCurrent

        contour_ds_index = qstring2int(element.attribute("display-contour"))
        if contour_ds_index is not None:
            self.contour_ds_index = contour_ds_index

        vector_ds_index = qstring2int(element.attribute("display-vector"))
        if vector_ds_index is not None:
            self.vector_ds_index = vector_ds_index

        # mesh rendering
        meshElem = element.firstChildElement("render-mesh")
        if not meshElem.isNull():
            meshRendering = qstring2bool(meshElem.attribute("enabled"))
            if meshRendering is not None:
                self.config["mesh"] = meshRendering

            if meshElem.hasAttribute("border-color"):
                meshBorderColor = qstring2rgb(meshElem.attribute("border-color"))
                if meshBorderColor is not None:
                    self.config["m_border_color"] = meshBorderColor

            if meshElem.hasAttribute("border-width"):
                meshBorderWidth = qstring2int(meshElem.attribute("border-width"))
                if meshBorderWidth is not None:
                    self.config["m_border_width"] = meshBorderWidth

            if meshElem.hasAttribute("fill-color"):
                meshFillColor = qstring2rgb(meshElem.attribute("fill-color"))
                if meshFillColor is not None:
                    self.config["m_fill_color"] = meshFillColor

            if meshElem.hasAttribute("label-elements-enabled"):
                meshElemLabel = qstring2bool(meshElem.attribute("label-elements-enabled"))
                if meshElemLabel is not None:
                    self.config["m_label_elem"] = meshElemLabel

            if meshElem.hasAttribute("fill-enabled"):
                meshFillEnabled = qstring2bool(meshElem.attribute("fill-enabled"))
                if meshFillEnabled is not None:
                    self.config["m_fill_enabled"] = meshFillEnabled

        return True


    def writeXml(self, node, doc):
        prj = QgsProject.instance()
        element = node.toElement();
        # write plugin layer type to project (essential to be read from project)
        element.setAttribute("type", "plugin")
        element.setAttribute("name", CrayfishPluginLayer.LAYER_TYPE)
        element.setAttribute("meshfile", prj.writePath(self.twoDMFileName))
        element.setAttribute("current-dataset", self.current_ds_index)
        element.setAttribute("current-output-time", str(self.current_output_time))
        element.setAttribute("lock-current", "1" if self.lockCurrent else "0")
        element.setAttribute("display-contour", str(self.contour_ds_index))
        element.setAttribute("display-vector", str(self.vector_ds_index))
        meshElem = doc.createElement("render-mesh")
        meshElem.setAttribute("enabled", "1" if self.config["mesh"] else "0")
        meshElem.setAttribute("border-color", rgb2string(self.config["m_border_color"]))
        meshElem.setAttribute("border-width", str(self.config["m_border_width"]))
        meshElem.setAttribute("fill-color", rgb2string(self.config["m_fill_color"]))
        meshElem.setAttribute("label-elements-enabled", "1" if self.config["m_label_elem"] else "0")
        meshElem.setAttribute("fill-enabled", "1" if self.config["m_fill_enabled"] else "0")
        element.appendChild(meshElem)

        for i in range(self.mesh.dataset_count()):
            ds = self.mesh.dataset(i)
            if ds.type() == DataSet.Bed:
                dsElem = doc.createElement("bed")
            else:
                dsElem = doc.createElement("dat")
                dsElem.setAttribute("path", prj.writePath(ds.filename()))
                dsElem.setAttribute("name", ds.name())
            if i in self.ds_user_names:
                dsElem.setAttribute("user-name", self.ds_user_names[i])
            self.writeDataSetXml(ds, dsElem, doc)
            element.appendChild(dsElem)

        return True

    def readDataSetXml(self, ds, elem):

        self.initCustomValues(ds)

        # datetime options
        dtElem = elem.firstChildElement("datetime-display")
        if not dtElem.isNull():
            useAbsTime = qstring2bool(dtElem.attribute("use-absolute-time"))
            if useAbsTime is not None:
                ds.timeConfig["dt_use_absolute_time"] = useAbsTime

            offset_hours = qstring2float(dtElem.attribute("offset-hours"))
            if offset_hours is not None:
                ds.timeConfig["dt_offset_hours"] = offset_hours
            timeFormat = qstring2string(dtElem.attribute("time-format"))
            if timeFormat is not None:
                ds.custom["dt_time_format"] = timeFormat

            refTime = qstring2datetime(dtElem.attribute("reference-time"))
            if refTime is not None:
                ds.custom["dt_reference_time"] = refTime
            dateTimeFormat = qstring2string(dtElem.attribute("datetime-format"))
            if dateTimeFormat is not None:
                ds.custom["dt_datetime_format"] = dateTimeFormat

        # contour options
        contElem = elem.firstChildElement("render-contour")
        if not contElem.isNull():
            alpha = qstring2int(contElem.attribute("alpha"))
            if alpha is not None:
                ds.custom["c_alpha"] = alpha
            isBasic = qstring2bool(contElem.attribute("basic"))
            if isBasic is not None:
                ds.custom["c_basic"] = isBasic
            autoRange = qstring2bool(contElem.attribute("auto-range"))
            if autoRange is not None:
                ds.custom["c_basicCustomRange"] = not autoRange
            rangeMin = qstring2float(contElem.attribute("range-min"))
            rangeMax = qstring2float(contElem.attribute("range-max"))
            if rangeMin is not None and rangeMax is not None:
                ds.custom["c_basicCustomRangeMin"] = rangeMin
                ds.custom["c_basicCustomRangeMax"] = rangeMax

            # read color ramp (basic)
            rampElem = contElem.firstChildElement("colorramp")
            if not rampElem.isNull():
                ramp = QgsSymbolLayerV2Utils.loadColorRamp(rampElem)
                ds.custom["c_basicRamp"] = ramp
                rampName = rampElem.attribute("name")
                ds.custom["c_basicName"] = rampName

            # read color map (advanced)
            advElem = contElem.firstChildElement("advanced")
            if not advElem.isNull():
                cm = self.readColorMapXml(advElem)
                if cm:
                    ds.custom["c_advancedColorMap"] = cm

            self.updateColorMap(ds)

        # vector options (if applicable)
        if ds.type() == DataSet.Vector:
            vectElem = elem.firstChildElement("render-vector")
            method = qstring2int(vectElem.attribute("method"))
            if method is not None:
                ds.config["v_shaft_length_method"] = method
            shaftLengthMin = qstring2float(vectElem.attribute("shaft-length-min"))
            shaftLengthMax = qstring2float(vectElem.attribute("shaft-length-max"))
            if shaftLengthMin is not None and shaftLengthMax is not None:
                ds.config["v_shaft_length_min"] = shaftLengthMin
                ds.config["v_shaft_length_max"] = shaftLengthMax
            shaftLengthScale = qstring2float(vectElem.attribute("shaft-length-scale"))
            if shaftLengthScale is not None:
                ds.config["v_shaft_length_scale"] = shaftLengthScale
            shaftLengthFixed = qstring2float(vectElem.attribute("shaft-length-fixed"))
            if shaftLengthFixed is not None:
                ds.config["v_shaft_length_fixed"] = shaftLengthFixed
            penWidth = qstring2float(vectElem.attribute("pen-width"))
            if penWidth is not None:
                ds.config["v_pen_width"] = penWidth
            headWidth = qstring2float(vectElem.attribute("head-width"))
            headLength = qstring2float(vectElem.attribute("head-length"))
            if headWidth is not None and headLength is not None:
                ds.config["v_head_width"] = headWidth
                ds.config["v_head_length"] = headLength
            grid = qstring2bool(vectElem.attribute("user-grid"))
            if grid is not None:
                ds.config["v_grid"] = grid
            gridX = qstring2int(vectElem.attribute("user-grid-x"))
            gridY = qstring2int(vectElem.attribute("user-grid-y"))
            if gridX is not None and gridY is not None:
                ds.config["v_grid_x"] = gridX
                ds.config["v_grid_y"] = gridY
            filterMin = qstring2float(vectElem.attribute("filter-min"))
            filterMax = qstring2float(vectElem.attribute("filter-max"))
            if filterMin is not None:
                ds.config["v_filter_min"] = filterMin
            if filterMax is not None:
                ds.config["v_filter_max"] = filterMax
            try:
                ds.config["v_color"] = qstring2rgb(vectElem.attribute("color"))
            except ValueError:
                pass


    def writeDataSetXml(self, ds, elem, doc):
        # datetime options
        dtElem = doc.createElement("datetime-display")
        dtElem.setAttribute("use-absolute-time", "1" if ds.timeConfig["dt_use_absolute_time"] else "0")
        dtElem.setAttribute("offset-hours", ds.timeConfig["dt_offset_hours"])
        dtElem.setAttribute("time-format", ds.timeConfig["dt_time_format"])
        dtElem.setAttribute("reference-time", ds.timeConfig["dt_reference_time"].strftime(DATETIME_FMT))
        dtElem.setAttribute("datetime-format", ds.timeConfig["dt_datetime_format"])

        # contour options
        contElem = doc.createElement("render-contour")
        contElem.setAttribute("alpha", ds.custom["c_alpha"])
        contElem.setAttribute("basic", "1" if ds.custom["c_basic"] else "0")
        contElem.setAttribute("auto-range", "1" if not ds.custom["c_basicCustomRange"] else "0")
        contElem.setAttribute("range-min", str(ds.custom["c_basicCustomRangeMin"]))
        contElem.setAttribute("range-max", str(ds.custom["c_basicCustomRangeMax"]))

        rampName = ds.custom["c_basicName"]
        ramp = ds.custom["c_basicRamp"]
        if ramp:
            rampElem = QgsSymbolLayerV2Utils.saveColorRamp(rampName, ramp, doc)
            contElem.appendChild(rampElem)
        elem.appendChild(contElem)

        advElem = doc.createElement("advanced")
        self.writeColorMapXml(ds.custom["c_advancedColorMap"], advElem, doc)
        contElem.appendChild(advElem)

        # vector options (if applicable)
        if ds.type() == DataSet.Vector:
          vectElem = doc.createElement("render-vector")
          vectElem.setAttribute("method", ds.config["v_shaft_length_method"])
          vectElem.setAttribute("shaft-length-min", str(ds.config["v_shaft_length_min"]))
          vectElem.setAttribute("shaft-length-max", str(ds.config["v_shaft_length_max"]))
          vectElem.setAttribute("shaft-length-scale", str(ds.config["v_shaft_length_scale"]))
          vectElem.setAttribute("shaft-length-fixed", str(ds.config["v_shaft_length_fixed"]))
          vectElem.setAttribute("pen-width", str(ds.config["v_pen_width"]))
          vectElem.setAttribute("head-width", str(ds.config["v_head_width"]))
          vectElem.setAttribute("head-length", str(ds.config["v_head_length"]))
          vectElem.setAttribute("user-grid", "1" if ds.config["v_grid"] else "0")
          vectElem.setAttribute("user-grid-x", str(ds.config["v_grid_x"]))
          vectElem.setAttribute("user-grid-y", str(ds.config["v_grid_y"]))
          vectElem.setAttribute("filter-min", str(ds.config["v_filter_min"]))
          vectElem.setAttribute("filter-max", str(ds.config["v_filter_max"]))
          vectElem.setAttribute("color", rgb2string(ds.config["v_color"]))
          elem.appendChild(vectElem)


    def readColorMapXml(self, elem):

        cmElem = elem.firstChildElement("colormap")
        if cmElem.isNull():
            return
        cm = ColorMap()
        cm.method = ColorMap.Discrete if cmElem.attribute("method") == "discrete" else ColorMap.Linear
        cm.clip = (cmElem.attribute("clip-low")  == "1", cmElem.attribute("clip-high") == "1")
        itemElems = cmElem.elementsByTagName("item")
        items = []
        for i in range(itemElems.length()):
            itemElem = itemElems.item(i).toElement()
            value = qstring2float(itemElem.attribute("value"))
            color = qstring2rgb(itemElem.attribute("color"))
            label = itemElem.attribute("label") if itemElem.hasAttribute("label") else "%.3f" % value
            items.append( (value, color, label) )
        cm.set_items(items)
        return cm


    def writeColorMapXml(self, cm, parentElem, doc):

        elem = doc.createElement("colormap")
        elem.setAttribute("method", "discrete" if cm.method == ColorMap.Discrete else "linear")
        elem.setAttribute("clip-low",  "1" if cm.clip[0] else "0")
        elem.setAttribute("clip-high", "1" if cm.clip[1] else "0")
        for item in cm.items():
            itemElem = doc.createElement("item")
            itemElem.setAttribute("value", str(item.value))
            itemElem.setAttribute("color", rgb2string(item.color))
            itemElem.setAttribute("label", item.label)
            elem.appendChild(itemElem)
        parentElem.appendChild(elem)


    # the support for styles is not implemented yet
    # we keep the methods here just so that they are not abstract and thus python error
    # is not thrown if they are called for some reason
    def readSymbology(self, node, err):
        return False
    def writeSymbology(self, node, doc, err):
        return False


    def set2DMFileName(self, fName):
        self.twoDMFileName = fName


    def updateColorMap(self, ds):
        """ update color map of the current data set given the settings """

        if not ds.custom["c_basic"]:
            cm = ds.custom["c_advancedColorMap"]
        else:
            cm = self._colorMapBasic(ds)

        if not cm:
            return

        cm.alpha = ds.custom["c_alpha"]
        ds.config["c_colormap"] = cm

        iface.legendInterface().refreshLayerSymbology(self)

    def colorMap(self, ds=None):
        #TODO not sure if it belongs to this class
        if not ds:
            ds = self.currentDataSet()
        return ds.config["c_colormap"]
    

    def _colorMapBasic(self, ds):

        # contour colormap
        if ds.custom["c_basicCustomRange"]:
            zMin = ds.custom["c_basicCustomRangeMin"]
            zMax = ds.custom["c_basicCustomRangeMax"]
        else:
            zMin,zMax = ds.value_range()

        qcm = ds.custom["c_basicRamp"]
        if not qcm:
            return   # something went wrong (e.g. user selected "new color ramp...")

        # if the color ramp is a gradient, we will use the defined stops
        # otherwise (unknown type of color ramp) we will just take few samples

        isGradient = isinstance(qcm, QgsVectorGradientColorRampV2)

        items = []
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
          items.append( (vv,[c.red(),c.green(),c.blue()], '%.3f' % vv) )

        cm = ColorMap()
        cm.set_items(items)

        return cm

    def createMapRenderer(self, rendererContext):
        self.renderer = CrayfishPluginLayerRenderer(self, rendererContext)
        return self.renderer

    def identify(self, pt):
        """
            Returns a QString representing the value of the layer at
            the given QgsPoint, pt
        """

        x = pt.x()
        y = pt.y()

        value = self.mesh.value(self.currentOutput(), x, y)

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


    def dataSetName(self, ds_index):
        if ds_index in self.ds_user_names:
            return self.ds_user_names[ds_index]
        else:
            return self.mesh.dataset(ds_index).name()


    def legendSymbologyItems(self, iconSize):
        """ implementation of method from QgsPluginLayer to show legend entries (in QGIS >= 2.1) """

        dsC = self.currentContourDataSet()
        dsV = self.currentVectorDataSet()
        if dsC is None and dsV is None:
          return []

        if dsC is not None and dsV is not None and dsC != dsV:
          name = "%s / %s" % (self.dataSetName(self.contour_ds_index), self.dataSetName(self.vector_ds_index))
        elif dsC is not None:
          name = self.dataSetName(self.contour_ds_index)
        else:
          name = self.dataSetName(self.vector_ds_index)
        lst = [ (name, QPixmap()) ]
        if not dsC:
            return lst

        cm = dsC.config["c_colormap"]
        for item in cm.items():
            pix = QPixmap(iconSize)
            r,g,b,a = item.color
            pix.fill(QColor(r,g,b))
            lst.append( (item.label, pix) )  # "%.3f" % item.value
        return lst

    def print_handles(self):
        print "------" #, self.mesh, self.currentDataSet()
        print Mesh.handles
        print DataSet.handles

    def isDataSetLoaded(self, filename):
        for d in self.mesh.datasets():
            if d.filename() == filename:
                return True
        return False
