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
  LIBS += -L$${OSGEO_PATH}/lib -lproj_i -lgdal_i
}

unix {
  INCLUDEPATH += /usr/include/gdal
  LIBS += -lproj -lgdal -lhdf5
}

TARGET = crayfish
TEMPLATE = lib

DEFINES += CRAYFISH_LIBRARY

SOURCES += crayfish.cpp \
    crayfish_e4q.cpp \
    crayfish_colormap.cpp \
    crayfish_dataset.cpp \
    crayfish_gdal.cpp \
    crayfish_mesh.cpp \
    crayfish_mesh_2dm.cpp \
    crayfish_capi.cpp \
    crayfish_dataset_dat.cpp \
    crayfish_dataset_xmdf.cpp \
    crayfish_renderer.cpp \
    crayfish_export_grid.cpp

HEADERS += crayfish.h \
    crayfish_e4q.h \
    crayfish_colormap.h \
    crayfish_dataset.h \
    crayfish_output.h \
    crayfish_mesh.h \
    crayfish_gdal.h \
    crayfish_mesh_2dm.h \
    crayfish_capi.h \
    crayfish_hdf5.h \
    crayfish_renderer.h

CONFIG(debug, debug|release) {
    DESTDIR = $$PWD/build/debug
} else {
    DESTDIR = $$PWD/build/release
}

unix {
  QMAKE_CXXFLAGS += -Wall -Wextra # -Wconversion
  QMAKE_CXXFLAGS += -fvisibility=hidden
}
