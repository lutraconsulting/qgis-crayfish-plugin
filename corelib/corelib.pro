# Crayfish - A collection of tools for TUFLOW and other hydraulic modelling packages
# Copyright (C) 2012 Peter Wells for Lutra Consulting

# peter dot wells at lutraconsulting dot co dot uk
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


############################################################################
# Setup path to QGIS

win32 {
  contains(QMAKE_HOST.arch, x86_64) {
    OSGEO_PATH = c:/osgeo4w64
  } else {
    OSGEO_PATH = c:/osgeo4w
  }

  INCLUDEPATH += $${OSGEO_PATH}/include
  LIBS += -L$${OSGEO_PATH}/lib -lproj_i -lgdal_i -lhdf5 -lnetcdf

  # use delayed loading of GDAL. If the requested library version is not available
  # (e.g. due to older QGIS installation), the loading of Crayfish library will not fail,
  # only export to grid will not be available
  LIBS += DelayImp.lib
  QMAKE_LFLAGS += /DELAYLOAD:gdal200.dll
}

unix:!macx {
  INCLUDEPATH += /usr/include/gdal
  LIBS += -lproj -lgdal -lnetcdf

  contains(QMAKE_HOST.arch, x86_64) {
    ARCH = x86_64
  } else {
    ARCH = i386
  }

  # HDF5 1.8.11 (ubuntu trusty)
  exists( /usr/lib/$${ARCH}-linux-gnu/libhdf5.so ) {
    LIBS += -lhdf5
  }
  # HDF5 1.8.13 (debian jessie / ubuntu vivid)
  exists( /usr/lib/$${ARCH}-linux-gnu/libhdf5_serial.so ) {
    LIBS += -lhdf5_serial
    INCLUDEPATH += /usr/include/hdf5/serial
  }
}

macx {
  LIBS += -lproj -lgdal -lnetcdf
  LIBS += -lhdf5
}

TARGET = crayfish
TEMPLATE = lib

DEFINES += CRAYFISH_LIBRARY

SOURCES += crayfish.cpp \
    crayfish_colormap.cpp \
    crayfish_dataset.cpp \
    crayfish_mesh.cpp \
    crayfish_capi.cpp \
    crayfish_renderer.cpp \
    crayfish_export_grid.cpp \
    crayfish_element.cpp \
    elem/crayfish_eNp.cpp \
    elem/crayfish_e3t.cpp \
    elem/crayfish_e2l.cpp \
    frmts/crayfish_gdal.cpp \
    frmts/crayfish_dataset_dat.cpp \
    frmts/crayfish_dataset_xdmf.cpp \
    frmts/crayfish_dataset_xmdf.cpp \
    frmts/crayfish_grib.cpp \
    frmts/crayfish_hec2d.cpp \
    frmts/crayfish_sww.cpp \
    frmts/crayfish_ugrid.cpp \
    frmts/crayfish_serafin.cpp \
    frmts/crayfish_netcdf.cpp \
    frmts/crayfish_mesh_2dm.cpp \
    frmts/crayfish_flo2d.cpp \
    contrib/tinyxml2.cpp \
    crayfish_trace.cpp \
    frmts/crayfish_tifs.cpp \
    calc/bison_crayfish_mesh_calculator_parser.cpp \
    calc/crayfish_mesh_calculator.cpp \
    calc/crayfish_mesh_calculator_node.cpp \
    calc/flex_crayfish_mesh_calculator_lexer.cpp \
    calc/crayfish_dataset_utils.cpp

HEADERS += crayfish.h \
    crayfish_colormap.h \
    crayfish_dataset.h \
    crayfish_output.h \
    crayfish_mesh.h \
    crayfish_gdal.h \
    crayfish_capi.h \
    crayfish_renderer.h \
    crayfish_element.h\
    elem/crayfish_eNp.h \
    elem/crayfish_e3t.h \
    elem/crayfish_e2l.h \
    frmts/crayfish_mesh_2dm.h \
    frmts/crayfish_hdf5.h \
    contrib/tinyxml2.h \
    frmts/crayfish_netcdf.h \
    crayfish_trace.h \
    crayfish_utils.h \
    calc/bison_crayfish_mesh_calculator_parser.hpp \
    calc/crayfish_mesh_calculator.h \
    calc/crayfish_mesh_calculator_node.h \
    calc/crayfish_dataset_utils.h

INCLUDEPATH += $$PWD

DESTDIR = $$PWD/../crayfish

unix {
  QMAKE_CXXFLAGS += -Wall -Wextra # -Wconversion
  QMAKE_CXXFLAGS += -fvisibility=hidden
  QMAKE_CXXFLAGS += -std=c++0x
}
