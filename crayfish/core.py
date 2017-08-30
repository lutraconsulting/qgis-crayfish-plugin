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

import ctypes
import os
import platform
import weakref
import datetime

import sip
from PyQt4.QtGui import QColor
from PyQt4.QtGui import QPixmap, QPainter, QColor
from PyQt4.QtCore import Qt

from buildinfo import plugin_version_str, crayfish_libname

# keep in sync with DATETIME_FMT in crayfish_capi.cpp
DATETIME_FMT = "%Y-%m-%dT%H:%M:%S.%fZ"

lib = None  # initialized on demand

libname = crayfish_libname()
libpath = os.path.join(os.path.dirname(os.path.realpath(__file__)), libname)

class Err(object):
    NoError, NotEnoughMemory, \
    FileNotFound, UnknownFormat, \
    IncompatibleMesh, InvalidData, \
    MissingDriver = range(7)

class Warn(object):
    NoWarning, UnsupportedElement, \
    InvalidElements, ElementWithInvalidNode, \
    ElementNotUnique, NodeNotUnique = range(6)

DS_Bed, DS_Scalar, DS_Vector = range(3)

class VersionError(Exception):
    """ Exception to be thrown on mismatch of C++/Python code versions """
    def __init__(self, library_ver, plugin_ver):
        self.library_ver = library_ver
        self.plugin_ver = plugin_ver

def load_library():
    """ Load the supporting Crayfish C++ library.
    Does nothing if the library has been loaded already.
    Raises an exception if loading fails. """

    global lib, libpath

    if lib is not None:
        return  # already loaded

    lib = ctypes.cdll.LoadLibrary(libpath)

    library_ver = library_version()
    plugin_ver = plugin_version()
    if library_ver != plugin_ver:
        lib = None
        raise VersionError(library_ver, plugin_ver)

    lib.CF_Mesh_nodeAt.restype = ctypes.c_void_p
    lib.CF_Mesh_elementAt.restype = ctypes.c_void_p
    lib.CF_LoadMesh.restype = ctypes.c_void_p
    lib.CF_LoadMesh.argtypes = [ctypes.c_char_p]
    lib.CF_Mesh_loadDataSet.restype = ctypes.c_bool
    lib.CF_Mesh_loadDataSet.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
    lib.CF_Mesh_dataSetAt.restype = ctypes.c_void_p
    lib.CF_Mesh_sourceCrs.restype = ctypes.c_char_p
    lib.CF_Mesh_destinationCrs.restype = ctypes.c_char_p
    lib.CF_DS_name.restype = ctypes.c_char_p
    lib.CF_DS_fileName.restype = ctypes.c_char_p
    lib.CF_DS_refTime.restype = ctypes.c_char_p
    lib.CF_DS_outputAt.restype = ctypes.c_void_p
    lib.CF_DS_mesh.restype = ctypes.c_void_p
    lib.CF_O_dataSet.restype = ctypes.c_void_p
    lib.CF_O_time.restype = ctypes.c_float
    lib.CF_O_valueAt.restype = ctypes.c_float
    lib.CF_O_statusAt.restype = ctypes.c_char
    lib.CF_CM_create.restype = ctypes.c_void_p
    lib.CF_CM_createDefault.restype = ctypes.c_void_p
    lib.CF_CM_itemValue.restype = ctypes.c_double
    lib.CF_CM_itemLabel.restype = ctypes.c_char_p
    lib.CF_CM_value.argtypes = [ctypes.c_void_p, ctypes.c_double]
    lib.CF_CM_value.restype = ctypes.c_uint
    lib.CF_CM_itemColor.restype = ctypes.c_uint
    lib.CF_Mesh_valueAt.restype = ctypes.c_double
    lib.CF_Mesh_valueAt.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_double, ctypes.c_double]
    lib.CF_R_create.restype = ctypes.c_void_p
    lib.CF_R_create.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
    lib.CF_R_destroy.argtypes = [ ctypes.c_void_p ]
    lib.CF_R_draw.argtypes = [ ctypes.c_void_p ]
    lib.CF_RC_create.restype = ctypes.c_void_p
    lib.CF_RC_destroy.argtypes = [ ctypes.c_void_p ]
    lib.CF_RC_setView.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_double, ctypes.c_double, ctypes.c_double]
    lib.CF_RC_setOutputMesh.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
    lib.CF_RC_setOutputContour.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
    lib.CF_RC_setOutputVector.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
    lib.CF_RC_setParam.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_void_p]
    lib.CF_RC_getParam.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_void_p]
    lib.CF_V_create.restype = ctypes.c_void_p
    lib.CF_V_toDouble.restype = ctypes.c_double
    lib.CF_N_x.restype = ctypes.c_double
    lib.CF_N_y.restype = ctypes.c_double

class Node:
  handles = {}

  @staticmethod
  def from_handle(handle):
    if handle not in Node.handles:
      return Node(handle)
    return Node.handles[handle]()

  def __init__(self, handle):
    load_library()  # make sure the library is loaded
    self.lib = lib
    if handle is None:
      raise ValueError(handle)
    assert handle not in Node.handles
    Node.handles[handle] = weakref.ref(self)
    self.handle = ctypes.c_void_p(handle)

  def __del__(self):
    if hasattr(self, 'handle'):  # only if initialized to a valid Node
      del Node.handles[self.handle.value]

  def x(self):
    return self.lib.CF_N_x(self.handle)

  def y(self):
    return self.lib.CF_N_y(self.handle)

  def n_id(self):
    return self.lib.CF_N_id(self.handle)

  def __repr__(self):
    return "<Node ID %d (%f,%f)>" % (self.n_id(), self.x(), self.y())


class Element:
  handles = {}

  @staticmethod
  def from_handle(handle):
    if handle not in Element.handles:
      return Element(handle)
    return Element.handles[handle]()

  def __init__(self, handle):
    load_library()  # make sure the library is loaded
    self.lib = lib
    if handle is None:
      raise ValueError(handle)
    assert handle not in Element.handles
    Element.handles[handle] = weakref.ref(self)
    self.handle = ctypes.c_void_p(handle)

  def __del__(self):
    if hasattr(self, 'handle'):  # only if initialized to a valid Element
      del Element.handles[self.handle.value]

  Undefined, ENP, E4Q, E3T, E2L = range(5)  # element types, return of e_type()
  ETYPE_NAME = { Undefined: "Unknown", ENP: "ENP", E4Q: "E4Q", E3T: "E3T", E2L: "E2L"}

  def __repr__(self):
    return "<Element ID %d type: %s  pts: %s>" % (self.e_id(), self.e_type_name(), str(list(self.node_indexes())))

  def node_count(self):
    return self.lib.CF_E_nodeCount(self.handle)

  def node_index(self, index):
    return self.lib.CF_E_nodeIndexAt(self.handle, index)

  def node_indexes(self):
    for index in xrange(self.node_count()):
      yield self.node_index(index)

  def e_id(self):
    return self.lib.CF_E_id(self.handle)

  def e_type(self):
    return self.lib.CF_E_type(self.handle)

  def e_type_name(self):
      etype = self.e_type()
      return self.ETYPE_NAME.get(etype)

  def is_valid(self):
    return self.e_type() != Element.Undefined

class Mesh:
  """ Mesh class is the central data structure in Crayfish. It defines
  structure of the mesh (nodes and elements) and it keeps track of any associated
  data with the mesh (organized into datasets). """

  # keeps dictionary of handles to known Mesh instances (as weak references)
  handles = {}

  @staticmethod
  def from_handle(handle):
      return Mesh.handles[handle]()

  def __init__(self, path):
    load_library()  # make sure the library is loaded
    self.lib = lib
    handle = self.lib.CF_LoadMesh(path)
    if handle is None:
      raise ValueError(last_load_status()) #, path)
    assert handle not in Mesh.handles
    Mesh.handles[handle] = weakref.ref(self)
    self.handle = ctypes.c_void_p(handle)

  def node_count(self):
    return self.lib.CF_Mesh_nodeCount(self.handle)

  def node(self, index):
    return Node.from_handle(self.lib.CF_Mesh_nodeAt(self.handle, index))

  def nodes(self):
    for index in xrange(self.node_count()):
      yield self.node(index)

  def element_count(self):
    return self.lib.CF_Mesh_elementCount(self.handle)

  def element_per_type_count(self):
    res = {t: 0 for t in Element.ETYPE_NAME.keys()}
    for e in self.elements():
      res[e.e_type()] += 1
    return res

  def element(self, index):
    return Element.from_handle(self.lib.CF_Mesh_elementAt(self.handle, index))

  def elements(self):
    for index in xrange(self.element_count()):
      yield self.element(index)

  def dataset_count(self):
    return self.lib.CF_Mesh_dataSetCount(self.handle)

  def dataset(self, index):
    return DataSet.from_handle(self.lib.CF_Mesh_dataSetAt(self.handle, index))

  def datasets(self):
    for index in xrange(self.dataset_count()):
      yield self.dataset(index)

  def dataset_from_name(self, name):
      for d in self.datasets():
          if d.name() == name:
              return d
      return None

  def __repr__(self):
    return "<Mesh nodes:%d elements:%d datasets:%d>" % (self.node_count(), self.element_count(), self.dataset_count())

  def __del__(self):
    if hasattr(self, 'handle'):  # only if initialized to a valid mesh
      del Mesh.handles[self.handle.value]
      self.lib.CF_CloseMesh(self.handle)

  def load_data(self, path):
    if not self.lib.CF_Mesh_loadDataSet(self.handle, path):
      raise ValueError(last_load_status())

  def extent(self):
    xmin,ymin = ctypes.c_double(), ctypes.c_double()
    xmax,ymax = ctypes.c_double(), ctypes.c_double()
    self.lib.CF_Mesh_extent(self.handle, ctypes.byref(xmin), ctypes.byref(ymin), ctypes.byref(xmax), ctypes.byref(ymax))
    return (xmin.value,ymin.value,xmax.value,ymax.value)

  def value(self, output, x, y):
    return self.lib.CF_Mesh_valueAt(self.handle, output.handle, x, y)

  def source_crs(self):
    return self.lib.CF_Mesh_sourceCrs(self.handle)

  def destination_crs(self):
    return self.lib.CF_Mesh_destinationCrs(self.handle)

  def set_source_crs(self, src_proj4):
    self.lib.CF_Mesh_setSourceCrs(self.handle, ctypes.c_char_p(src_proj4))

  def set_destination_crs(self, dest_proj4):
    self.lib.CF_Mesh_setDestinationCrs(self.handle, ctypes.c_char_p(dest_proj4))

  def parse_mesh_calc_string(self, expression):
    error_string = None
    return "TODO", error_string # return pointer to CrayfishMeshCalcNode



class DataSet(object):
  """ Datasets store data associated with mesh. One dataset represents
  one quantity that might be either constant or varying in time. Data
  are organized into 'outputs' - each dataset contains one or more of those,
  each output represents the quantity at a particular timestep. """

  handles = {}

  @staticmethod
  def from_handle(handle):
    if handle not in DataSet.handles:
      return DataSet(handle)
    return DataSet.handles[handle]()

  def __init__(self, handle):
    load_library()  # make sure the library is loaded
    self.lib = lib
    if handle is None:
      raise ValueError(handle)
    assert handle not in DataSet.handles
    DataSet.handles[handle] = weakref.ref(self)
    self.handle = ctypes.c_void_p(handle)
    self.m = self.mesh()  # keep ref to the mesh so the dataset does not get invalid

  def __del__(self):
    if hasattr(self, 'handle'):  # only if initialized to a valid dataset
      del DataSet.handles[self.handle.value]

  Bed, Scalar, Vector = range(3)

  def type(self):
    return self.lib.CF_DS_type(self.handle)

  def name(self):
    return self.lib.CF_DS_name(self.handle)

  def filename(self):
    return self.lib.CF_DS_fileName(self.handle)

  def ref_time(self):
    refTime = self.lib.CF_DS_refTime(self.handle)
    if refTime:
      return datetime.datetime.strptime(refTime, DATETIME_FMT)
    else:
      return datetime.datetime.now()

  def output_count(self):
    return self.lib.CF_DS_outputCount(self.handle)

  def output(self, index):
    return Output.from_handle(self.lib.CF_DS_outputAt(self.handle, index))

  def outputs(self):
    for index in xrange(self.output_count()):
      yield self.output(index)

  def output_time_index(self, t):
    """ return output index for given time value (None if not found) """
    for index,o in enumerate(self.outputs()):
      # leave a bit of room for errors from string-float conversions (1e-6 is less than 10ms)
      if t == o.time() or abs(t-o.time()) < 1e-6:
        return index
    return None

  def mesh(self):
    return Mesh.from_handle(self.lib.CF_DS_mesh(self.handle))

  def value_range(self):
    vmin,vmax = ctypes.c_float(), ctypes.c_float()
    self.lib.CF_DS_valueRange(self.handle, ctypes.byref(vmin), ctypes.byref(vmax))
    return (vmin.value, vmax.value)

  def time_range(self):
    # returns (float, float)
    start = self.output(0)
    end = self.output(self.output_count() - 1)
    return start.time(), end.time()

  def time_varying(self):
    return self.output_count() > 1

  def __repr__(self):
    return "<DataSet type:%d name:%s outputs:%d>" % (self.type(), self.name(), self.output_count())


class Output(object):
  """ Output class represents data of a quantity at one timestep. There
  are two kinds of outputs based on which part of mesh they refer to:
  Node outputs have one value for each node, while element outputs have
  one value for each element. For one dataset, all outputs are of the same
  type, most commonly they are node outputs.

  Additionally, outputs may carry information about status of elements,
  whether they are active or not in the timestep they represent. Inactive
  elements are not rendered.
  """

  handles = {}

  TypeNode, TypeElement = range(2)  # return values for output_type()

  @staticmethod
  def from_handle(handle):
    if handle not in Output.handles:
      return Output(handle)
    return Output.handles[handle]()

  def __init__(self, handle):
    load_library()  # make sure the library is loaded
    self.lib = lib
    if handle is None:
      raise ValueError(handle)
    assert handle not in Output.handles
    Output.handles[handle] = weakref.ref(self)
    self.handle = ctypes.c_void_p(handle)
    self.ds = self.dataset()  # keep ref to dataset so the output does not get invalid

  def __del__(self):
    if hasattr(self, 'handle'):  # only if initialized to a valid output
      del Output.handles[self.handle.value]

  def output_type(self):
    return self.lib.CF_O_type(self.handle)

  def time(self):
    return self.lib.CF_O_time(self.handle)

  def value(self, index):
    return self.lib.CF_O_valueAt(self.handle, index)

  def z_range(self):
    zMin, zMax = ctypes.c_float(), ctypes.c_float()
    self.lib.CF_O_range(self.handle, ctypes.byref(zMin), ctypes.byref(zMax))
    return zMin.value, zMax.value

  def value_vector(self, index):
    x,y = ctypes.c_float(), ctypes.c_float()
    self.lib.CF_O_valueVectorAt(self.handle, index, ctypes.byref(x), ctypes.byref(y))
    return x.value,y.value

  def values(self):
    if self.output_type() == Output.TypeNode:
      count = self.dataset().mesh().node_count()
    else:
      count = self.dataset().mesh().element_count()

    for index in xrange(count):
      yield self.value(index)

  def values_vector(self):
    if self.output_type() == Output.TypeNode:
      count = self.dataset().mesh().node_count()
    else:
      count = self.dataset().mesh().element_count()

    for index in xrange(count):
      yield self.value_vector(index)

  def status(self, index):
    return self.lib.CF_O_statusAt(self.handle, index)

  def dataset(self):
    return DataSet.from_handle(self.lib.CF_O_dataSet(self.handle))

  def export_grid(self, mupp, outFilename, proj4wkt):
    return self.lib.CF_ExportGrid(self.handle, ctypes.c_double(mupp), ctypes.c_char_p(outFilename), ctypes.c_char_p(proj4wkt))

  def export_contours(self, mupp, interval, outFilename, proj4wkt, useLines, colorMap):
    if colorMap != None:
        cm_h = colorMap.handle
        int_h = ctypes.c_double(-1.0)
    elif interval != None:
        cm_h = 0
        int_h = ctypes.c_double(interval)
    else:
        # should never happen
        assert(False)

    return self.lib.CF_ExportContours(self.handle,
                                      ctypes.c_double(mupp),
                                      int_h,
                                      ctypes.c_char_p(outFilename),
                                      ctypes.c_char_p(proj4wkt),
                                      ctypes.c_bool(useLines),
                                      cm_h)

  def __repr__(self):
    return "<Output time:%f>" % self.time()


class Value(object):
  """ Value class represents a variant value and is used internally
  for communication with the underlying Crayfish library.

  Supported object types: int, float, RGB tuple, RGBA tuple, ColorMap, None."""

  def __init__(self, value=None):
    """ Create an instance from given Python object """
    load_library()  # make sure the library is loaded
    self.lib = lib
    self.handle = ctypes.c_void_p( self.lib.CF_V_create() )
    if isinstance(value, int):
      self.lib.CF_V_fromInt(self.handle, value)
    elif isinstance(value, float):
      self.lib.CF_V_fromDouble(self.handle, ctypes.c_double(value))
    elif isinstance(value, tuple) and (len(value) == 4 or len(value) == 3):
      alpha = 255 if len(value) == 3 else value[3]
      self.lib.CF_V_fromColor(self.handle, value[0], value[1], value[2], alpha)
    elif isinstance(value, ColorMap):
      self.lib.CF_V_fromColorMap(self.handle, value.handle)
    elif value is None:
      pass # do nothing
    else:
      raise ValueError("unknown type of value")

  def value(self):
    """ retrieve value as a native Python object """
    t = self.lib.CF_V_type(self.handle)
    if t == 0:
      return None
    elif t == 1:
      return self.lib.CF_V_toInt(self.handle)
    elif t == 2:
      return self.lib.CF_V_toDouble(self.handle)
    elif t == 3:
      r,g,b,a = ctypes.c_int(), ctypes.c_int(), ctypes.c_int(), ctypes.c_int()
      self.lib.CF_V_toColor(self.handle, ctypes.byref(r), ctypes.byref(g), ctypes.byref(b), ctypes.byref(a))
      return (r.value,g.value,b.value,a.value)
    elif t == 4:
      cm = ColorMap()
      self.lib.CF_V_toColorMap(self.handle, cm.handle)
      return cm
    else:
      raise ValueError("unknown type in value")

  def __del__(self):
    self.lib.CF_V_destroy(self.handle)


class RendererConfig(object):
  """ Configuration for rendering of data on a mesh. The key pieces of configuration
  are the view definition (image size in pixels and map extent), reference to mesh
  and reference to outputs that should be drawn as contours and/or vectors.

  Further configuration options are specified as parameters (keys are strings,
  values are of various types, see Value class). """

  def __init__(self, mesh=None, size=None, ll=None, mupp=None):
    load_library()  # make sure the library is loaded
    self.lib = lib
    self.handle = ctypes.c_void_p(self.lib.CF_RC_create())
    if mesh:
      self.set_output_mesh(mesh)
    if size and ll and mupp:
      self.set_view(size, ll, mupp)

  def set_view(self, size, ll, mupp):
    self.lib.CF_RC_setView(self.handle, size[0], size[1], ll[0], ll[1], mupp)

  def set_output_mesh(self, mesh):
    self.lib.CF_RC_setOutputMesh(self.handle, mesh.handle)

  def set_output_contour(self, output):
    self.lib.CF_RC_setOutputContour(self.handle, output.handle)

  def set_output_vector(self, output):
    self.lib.CF_RC_setOutputVector(self.handle, output.handle)

  def __del__(self):
    self.lib.CF_RC_destroy(self.handle)

  def set_param(self, key, value):
    vv = Value(value)
    self.lib.CF_RC_setParam(self.handle, key, vv.handle)

  def get_param(self, key):
    vv = Value()
    self.lib.CF_RC_getParam(self.handle, key, vv.handle)
    return vv.value()

  def __setitem__(self, key, value):
    self.set_param(key, value)

  def __getitem__(self, key):
    return self.get_param(key)


class Renderer(object):
  """ The renderer object that draws the resulting map image
  to the passed QImage according to the renderer configuration. """

  def __init__(self, config, img):
    load_library()  # make sure the library is loaded
    self.lib = lib
    self.handle = ctypes.c_void_p(self.lib.CF_R_create(config.handle, sip.unwrapinstance(img)))

  def __del__(self):
    self.lib.CF_R_destroy(self.handle)

  def draw(self):
    self.lib.CF_R_draw(self.handle)


def uint2rgb(val):
  """ 0xAARRGGBB -> (r,g,b,a) """
  a = int((val >> 24) & 0xff)
  r = int((val >> 16) & 0xff)
  g = int((val >>  8) & 0xff)
  b = int((val >>  0) & 0xff)
  return (r,g,b,a)

def rgb2uint(val):
  """ (r,g,b,a) -> 0xAARRGGBB """
  a = 255 if len(val) == 3 else val[3]
  return (a << 24) | (val[0] << 16) | (val[1] << 8) | (val[2])

def rgb2qcolor(val):
  """ (r,g,b,a) -> QColor """
  return QColor(val[0],val[1],val[2],val[3])

def qcolor2rgb(c):
  """ QColor -> (r,g,b,a) """
  return (c.red(),c.green(),c.blue(),c.alpha())


class ColorMap(object):
  """ This object keeps track of a color map consisting of multiple colors
  assigned to specific numeric values and labels. """

  class Item(object):
    def __init__(self, cm, index):
      load_library()  # make sure the library is loaded
      self.lib = lib
      self.cm = cm
      self.index = index

    def get_value(self): return self.lib.CF_CM_itemValue(self.cm, self.index)
    def set_value(self, v): self.lib.CF_CM_setItemValue(self.cm, self.index, ctypes.c_double(v))

    def get_color(self): return uint2rgb(ctypes.c_uint(self.lib.CF_CM_itemColor(self.cm, self.index)).value)
    def set_color(self, c): self.lib.CF_CM_setItemColor(self.cm, self.index, rgb2uint(c))

    def get_label(self): return self.lib.CF_CM_itemLabel(self.cm, self.index)
    def set_label(self, l): self.lib.CF_CM_setItemLabel(self.cm, self.index, ctypes.c_char_p(l))

    value = property(get_value, set_value)
    color = property(get_color, set_color)
    label = property(get_label, set_label)

    def __repr__(self):
      return "Item(%f, %s, '%s')" % (self.value, str(self.color), self.label)

  def __init__(self, vmin=None, vmax=None):
    load_library()  # make sure the library is loaded
    self.lib = lib
    if vmin is not None and vmax is not None:
      h = self.lib.CF_CM_createDefault(ctypes.c_double(vmin), ctypes.c_double(vmax))
    else:
      h = self.lib.CF_CM_create()
    self.handle = ctypes.c_void_p(h)

  def item_count(self):
    return self.lib.CF_CM_itemCount(self.handle)

  def item(self, index):
    if index < 0 or index >= self.item_count():
      raise KeyError("invalid index")
    return ColorMap.Item(self.handle, index)

  def __getitem__(self, index):
    return self.item(index)

  def items(self):
    for i in xrange(self.item_count()):
      yield self.item(i)

  def set_item_count(self, count):
    self.lib.CF_CM_setItemCount(self.handle, count)

  def set_item(self, index, v, c, l):
    item = self.item(index)
    item.value = v
    item.color = c
    item.label = l

  def set_items(self, items):
    self.set_item_count(len(items))
    for i,item in enumerate(items):
      self.set_item(i, item[0], item[1], item[2])

  def add_item(self, v, c, l):
    cnt = self.item_count()
    self.set_item_count(cnt+1)
    self.set_item(cnt, v, c, l)

  def remove_item(self, index):
    for i in xrange(index+1,self.item_count()):
      it = self.item(i)
      self.set_item(i-1, it.value, it.color, it.label)
    self.set_item_count(self.item_count()-1)

  def sort_items(self):
    items = [ (i.value, i.color, i.label) for i in self.items() ]
    items = sorted(items, key=lambda x: x[0])
    self.set_items(items)

  alpha = property(lambda self:   self.lib.CF_CM_alpha(self.handle),
                   lambda self,v: self.lib.CF_CM_setAlpha(self.handle, v))

  def get_clip(self):
    c_low,c_high = ctypes.c_int(), ctypes.c_int()
    self.lib.CF_CM_clip(self.handle, ctypes.byref(c_low), ctypes.byref(c_high))
    return c_low.value, c_high.value

  def set_clip(self, c):
    self.lib.CF_CM_setClip(self.handle, c[0], c[1])

  clip = property(get_clip, set_clip)

  Linear, Discrete = range(2)

  method = property(lambda self:   self.lib.CF_CM_method(self.handle),
                    lambda self,m: self.lib.CF_CM_setMethod(self.handle, m))

  def __del__(self):
    self.lib.CF_CM_destroy(self.handle)

  def value(self, v):
    return uint2rgb(self.lib.CF_CM_value(self.handle, v))

  def previewPixmap(self, size, vMin, vMax):
    pix = QPixmap(size)
    pix.fill(Qt.white)
    p = QPainter(pix)

    if self.item_count() == 0:
      p.drawLine(0,0,size.width()-1,size.height()-1)
      p.drawLine(0,size.height()-1,size.width()-1,0)
    else:
      for i in xrange(size.width()):
        v = vMin + (vMax-vMin) *  i / (size.width()-1)
        p.setPen(rgb2qcolor(self.value(v)))
        p.drawLine(i,0,i,size.height()-1)
    p.end()
    return pix


def last_load_status():
  """ Return extended status of a recent loading operation:
  a tuple (error, warning) that refer to values in Err and Warn classes """
  load_library()  # make sure the library is loaded
  return lib.CF_LastLoadError(), lib.CF_LastLoadWarning()

def library_version():
  """ Return version of the underlying C++ library as a number.
  It should be the same as what plugin_version() returns.
  Format: 0xXYZ for version X.Y.Z """
  if lib is None:
      return None
  return lib.CF_Version()

def plugin_version():
    """ Return version of Python plugin from metadata as a number.
    It should be the same as what library_version() returns.
    Format: 0xXYZ for version X.Y.Z """
    ver_lst = plugin_version_str().split('.')
    ver = 0
    if len(ver_lst) >= 1:
        ver_major = int(ver_lst[0])
        ver |= ver_major << 16
    if len(ver_lst) >= 2:
        ver_minor = int(ver_lst[1])
        ver |= ver_minor << 8
    if len(ver_lst) == 3:
        ver_bugfix = int(ver_lst[2])
        ver |= ver_bugfix
    return ver
