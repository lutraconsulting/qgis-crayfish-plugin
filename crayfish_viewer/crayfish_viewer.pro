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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.from PyQt4.QtCore import *

#-------------------------------------------------
#
# Project created by QtCreator 2012-08-24T11:25:24
#
#-------------------------------------------------

# QT       -= gui

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

CONFIG(debug, debug|release) {
    DESTDIR = $$PWD/build/debug
} else {
    DESTDIR = $$PWD/build/release
}


#Release:DESTDIR = "$$PWD/build/release"
#Release:OBJECTS_DIR = "$$PWD/build/release/.obj"
#Release:MOC_DIR = "$$PWD/build/release/.moc"
#Release:RCC_DIR = "$$PWD/build/release/.rcc"
#Release:UI_DIR = "$$PWD/build/release/.ui"

#Debug:DESTDIR = "$$PWD/build/debug"
#Debug:OBJECTS_DIR = "$$PWD/build/debug/.obj"
#Debug:MOC_DIR = "$$PWD/build/debug/.moc"
#Debug:RCC_DIR = "$$PWD/build/debug/.rcc"
#Debug:UI_DIR = "$$PWD/build/debug/.ui"

symbian {
    MMP_RULES += EXPORTUNFROZEN
    TARGET.UID3 = 0xE75114E6
    TARGET.CAPABILITY = 
    TARGET.EPOCALLOWDLLDATA = 1
    addFiles.sources = crayfishViewer.dll
    addFiles.path = !:/sys/bin
    DEPLOYMENT += addFiles
}

unix:!symbian {
    maemo5 {
        target.path = /opt/usr/lib
    } else {
        target.path = /usr/lib
    }
    INSTALLS += target
}
