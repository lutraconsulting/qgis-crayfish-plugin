#-------------------------------------------------
#
# Project created by QtCreator 2012-08-24T18:22:28
#
#-------------------------------------------------

TARGET = crayfishViewerTest
CONFIG   += console
CONFIG   -= app_bundle

TEMPLATE = app

DEPENDPATH += . ../crayfish_viewer/build/debug
INCLUDEPATH +=  ../crayfish_viewer
LIBS +=  -L../crayfish_viewer/build/debug -lcrayfishViewer

CONFIG(debug, debug|release) {
    DESTDIR = $$PWD/build/debug
} else {
    DESTDIR = $$PWD/build/release
}

SOURCES += main.cpp
