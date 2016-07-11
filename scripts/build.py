import os
import platform
import sys

this_dir = os.path.dirname(os.path.realpath(__file__))
cr_dir = os.path.join(this_dir, os.pardir, "crayfish")
sys.path.insert(0, cr_dir)

import buildinfo

ver = buildinfo.plugin_version_str()
print "Building version " + ver

