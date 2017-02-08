TEMPLATE = subdirs
CONFIG += ordered
SUBDIRS = crayfish \
          crayfishinfo

crayfishinfo.depends = crayfish

crayfish.subdir = crayfish
crayfishinfo.subdir = crayfishinfo
