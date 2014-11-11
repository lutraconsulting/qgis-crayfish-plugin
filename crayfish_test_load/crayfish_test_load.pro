#-------------------------------------------------
#
# Project created by QtCreator 2014-11-11T14:55:22
#
#-------------------------------------------------

QT       += testlib

TARGET = testcrayfish_load
CONFIG   += console
CONFIG   -= app_bundle

TEMPLATE = app

CONFIG(debug, debug|release) {
    BUILDTYPE = debug
} else {
    BUILDTYPE = release
}

INCLUDEPATH +=  ../crayfish_viewer
LIBS +=  -L$${PWD}/../crayfish_viewer/build/$${BUILDTYPE}  -lcrayfishViewer
DEPENDPATH += . $${PWD}/../crayfish_viewer/build/$${BUILDTYPE}


SOURCES += testcrayfish_load.cpp
DEFINES += SRCDIR=\\\"$$PWD/\\\"
