import os
import platform
import sys
import argparse

this_dir = os.path.dirname(os.path.realpath(__file__))
cr_dir = os.path.join(this_dir, os.pardir, "crayfish")
sys.path.insert(0, cr_dir)

import buildinfo

ver = buildinfo.plugin_version_str()
plat = buildinfo.findPlatformVersion()

parser = argparse.ArgumentParser(description='Build Tool')
parser.add_argument('--dst', help='destination directory', action='store', required=True)
args = parser.parse_args()

print "Building version " + ver + " for " + plat
print "Destination directory " + args.dst
