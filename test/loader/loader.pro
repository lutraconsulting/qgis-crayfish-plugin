TEMPLATE = app
TARGET = crayfish

SOURCES += main.cpp

INCLUDEPATH += $$PWD/../../corelib
LIBS += -L$$PWD/../../crayfish -lcrayfish
