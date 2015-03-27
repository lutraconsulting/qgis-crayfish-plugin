# -*- coding: utf-8 -*-

# Crayfish - A collection of tools for TUFLOW and other hydraulic modelling packages
# Copyright (C) 2015 Lutra Consulting

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

this_dir = os.path.dirname(__file__)
libname = "crayfish.dll" if platform.system() == "Windows" else "libcrayfish.so.1"
lib=ctypes.cdll.LoadLibrary(os.path.join(this_dir, libname))

Err_None, Err_NotEnoughMemory, \
  Err_FileNotFound, Err_UnknownFormat, \
  Err_IncompatibleMesh = range(5)
Warn_None, Warn_UnsupportedElement, \
  Warn_InvalidElements, Warn_ElementWithInvalidNode, \
  Warn_ElementNotUnique, Warn_NodeNotUnique = range(6)

DS_Bed, DS_Scalar, DS_Vector = range(3)

class Node(ctypes.Structure):
  _fields_ = [("id", ctypes.c_int), ("x", ctypes.c_double), ("y", ctypes.c_double)]

  def __repr__(self):
    return "<Node ID %d (%f,%f)>" % (self.id, self.x, self.y)

class Element(ctypes.Structure):
  _fields_ = [("id", ctypes.c_int), ("type", ctypes.c_int), ("p", ctypes.c_int * 4)]

  def __repr__(self):
    return "<Element ID %d type: %d  pts: %s>" % (self.id, self.type, str(list(self.p)))

lib.CF_Mesh_nodeAt.restype = ctypes.POINTER(Node)
lib.CF_Mesh_elementAt.restype = ctypes.POINTER(Element)
lib.CF_LoadMesh.restype = ctypes.c_void_p
lib.CF_LoadMesh.argtypes = [ctypes.c_char_p]
lib.CF_Mesh_loadDataSet.restype = ctypes.c_bool
lib.CF_Mesh_loadDataSet.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
lib.CF_Mesh_dataSetAt.restype = ctypes.c_void_p
lib.CF_DS_name.restype = ctypes.c_char_p
lib.CF_DS_fileName.restype = ctypes.c_char_p
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

class Mesh:

  # keeps dictionary of handles to known Mesh instances (as weak references)
  handles = {}

  @staticmethod
  def from_handle(handle):
      return Mesh.handles[handle]()

  def __init__(self, path):
    self.lib = lib
    handle = self.lib.CF_LoadMesh(path)
    if handle is None:
      raise ValueError, last_load_status() #, path)
    assert handle not in Mesh.handles
    Mesh.handles[handle] = weakref.ref(self)
    self.handle = ctypes.c_void_p(handle)

  def node_count(self):
    return self.lib.CF_Mesh_nodeCount(self.handle)

  def node(self, index):
    return self.lib.CF_Mesh_nodeAt(self.handle, index).contents

  def nodes(self):
    for index in xrange(self.node_count()):
      yield self.node(index)

  def element_count(self):
    return self.lib.CF_Mesh_elementCount(self.handle)

  def element(self, index):
    return self.lib.CF_Mesh_elementAt(self.handle, index).contents

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
      raise ValueError, last_load_status()

  def extent(self):
    xmin,ymin = ctypes.c_double(), ctypes.c_double()
    xmax,ymax = ctypes.c_double(), ctypes.c_double()
    self.lib.CF_Mesh_extent(self.handle, ctypes.byref(xmin), ctypes.byref(ymin), ctypes.byref(xmax), ctypes.byref(ymax))
    return (xmin.value,ymin.value,xmax.value,ymax.value)

  def value(self, output, x, y):
    return self.lib.CF_Mesh_valueAt(self.handle, output.handle, x, y)

  def set_projection(self, src_proj4, dest_proj4):
    return self.lib.CF_Mesh_setProjection(self.handle, ctypes.c_char_p(src_proj4), ctypes.c_char_p(dest_proj4))

  def set_no_projection(self):
    self.set_projection(None, None)


class DataSet(object):

  handles = {}

  @staticmethod
  def from_handle(handle):
    if handle not in DataSet.handles:
      return DataSet(handle)
    return DataSet.handles[handle]()

  def __init__(self, handle):
    self.lib = lib
    if handle is None:
      raise ValueError, handle
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

  def time_varying(self):
    return self.output_count() > 1

  def __repr__(self):
    return "<DataSet type:%d name:%s outputs:%d>" % (self.type(), self.name(), self.output_count())


class Output(object):

  handles = {}

  @staticmethod
  def from_handle(handle):
    if handle not in Output.handles:
      return Output(handle)
    return Output.handles[handle]()

  def __init__(self, handle):
    self.lib = lib
    if handle is None:
      raise ValueError, handle
    assert handle not in Output.handles
    Output.handles[handle] = weakref.ref(self)
    self.handle = ctypes.c_void_p(handle)
    self.ds = self.dataset()  # keep ref to dataset so the output does not get invalid

  def __del__(self):
    if hasattr(self, 'handle'):  # only if initialized to a valid output
      del Output.handles[self.handle.value]

  def time(self):
    return self.lib.CF_O_time(self.handle)

  def value(self, index):
    return self.lib.CF_O_valueAt(self.handle, index)

  def value_vector(self, index):
    x,y = ctypes.c_float(), ctypes.c_float()
    self.lib.CF_O_valueVectorAt(self.handle, index, ctypes.byref(x), ctypes.byref(y))
    return x.value,y.value

  def values(self):
    node_count = self.dataset().mesh().node_count()
    for index in xrange(node_count):
      yield self.value(index)

  def values_vector(self):
    node_count = self.dataset().mesh().node_count()
    for index in xrange(node_count):
      yield self.value_vector(index)

  def status(self, index):
    return self.lib.CF_O_statusAt(self.handle, index)

  def dataset(self):
    return DataSet.from_handle(self.lib.CF_O_dataSet(self.handle))

  def export_grid(self, mupp, outFilename, proj4wkt):
    return self.lib.CF_ExportGrid(self.handle, ctypes.c_double(mupp), ctypes.c_char_p(outFilename), ctypes.c_char_p(proj4wkt))

  def __repr__(self):
    return "<Output time:%f>" % self.time()


class Value(object):

  def __init__(self, value=None):
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
      raise ValueError, "unknown type of value"

  def value(self):
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
      raise ValueError, "unknown type in value"

  def __del__(self):
    self.lib.CF_V_destroy(self.handle)


class RendererConfig(object):

  def __init__(self, mesh=None, size=None, ll=None, mupp=None):
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

  def __init__(self, config, img):
    self.lib = lib
    import sip
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
  from PyQt4.QtGui import QColor
  return QColor(val[0],val[1],val[2],val[3])

def qcolor2rgb(c):
  """ QColor -> (r,g,b,a) """
  return (c.red(),c.green(),c.blue(),c.alpha())


class ColorMap(object):

  class Item(object):
    def __init__(self, cm, index):
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
      raise KeyError, "invalid index"
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
    from PyQt4.QtGui import QPixmap, QPainter, QColor
    from PyQt4.QtCore import Qt
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
  return lib.CF_LastLoadError(), lib.CF_LastLoadWarning()

def version():
  return lib.CF_Version()
