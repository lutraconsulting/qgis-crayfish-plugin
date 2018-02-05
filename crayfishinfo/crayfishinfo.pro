TEMPLATE = app
TARGET = crayfishinfo

SOURCES += main.cpp

INCLUDEPATH += $$PWD/../corelib
LIBS += -L$$PWD/../crayfish -lcrayfish
