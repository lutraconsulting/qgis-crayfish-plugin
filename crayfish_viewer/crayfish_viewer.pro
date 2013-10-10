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
    QGIS_PATH = c:/osgeo4w64/apps/qgis
  } else {
    QGIS_PATH = c:/osgeo4w/apps/qgis
  }
}

unix {
  QGIS_PATH = /home/martin/qgis/inst-master
}

# QtXml needed just for some #includes within QGIS headers
QT       += xml

TARGET = crayfishViewer
TEMPLATE = lib

DEFINES += CRAYFISHVIEWER_LIBRARY

SOURCES += crayfish_viewer.cpp\
        version.cpp \
        crayfish_e4q.cpp

HEADERS += crayfish_viewer.h\
        crayfish_viewer_global.h\
        version.h \
        crayfish_e4q.h

DEFINES += CORE_EXPORT=""
win32 {
INCLUDEPATH += $${QGIS_PATH}/include
}
unix {
INCLUDEPATH += $${QGIS_PATH}/include/qgis
}
LIBS += -L$${QGIS_PATH}/lib -lqgis_core

CONFIG(debug, debug|release) {
    DESTDIR = $$PWD/build/debug
} else {
    DESTDIR = $$PWD/build/release
}
