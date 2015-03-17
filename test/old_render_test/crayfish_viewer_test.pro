#-------------------------------------------------
#
# Project created by QtCreator 2012-08-24T18:22:28
#
#-------------------------------------------------

TARGET = crayfishViewerTest
CONFIG   += console
CONFIG   -= app_bundle

TEMPLATE = app

INCLUDEPATH +=  ../crayfish_viewer

CONFIG(debug, debug|release) {
    BUILDTYPE = debug
} else {
    BUILDTYPE = release
}

DESTDIR = $$PWD/build/$${BUILDTYPE}
LIBS +=  -L$${PWD}/../crayfish_viewer/build/$${BUILDTYPE}  -lcrayfishViewer
DEPENDPATH += . $${PWD}/../crayfish_viewer/build/$${BUILDTYPE}

SOURCES += main.cpp
