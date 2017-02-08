TEMPLATE = subdirs
CONFIG += ordered
SUBDIRS = corelib \
          crayfishinfo

crayfishinfo.depends = corelib

corelib.subdir = corelib
crayfishinfo.subdir = crayfishinfo
