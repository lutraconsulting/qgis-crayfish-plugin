from __future__ import print_function
import os
import platform
import sys
import argparse

this_dir = os.path.dirname(os.path.realpath(__file__))
base_dir = os.path.join(this_dir, os.pardir)
cr_dir = os.path.join(base_dir, "crayfish")
sys.path.insert(0, base_dir)

from crayfish.buildinfo import plugin_version_str, findPlatformVersion, crayfish_zipfile
from install import make_and_install

parser = argparse.ArgumentParser(description="Build and Install Crayfish")
parser.add_argument('--pkg', help="Package?", action='store_true', default=False)
parser.add_argument('--dst', help="Destination folder", default=None)
parser.add_argument('--host', help="user@host", default=None)
args = parser.parse_args()

ver = plugin_version_str()
plat = findPlatformVersion()
libzip = crayfish_zipfile()

print("Building CRAYFISH " + ver + " for " + plat)
os.chdir(base_dir)
if args.pkg:
    extra_args = " -pkg=" + ver
else:
    extra_args = ""

make_and_install(extra_args)

src = os.path.join(base_dir, libzip)
if not os.path.exists(src):
    raise Exception("lib zip file not created!")

if args.dst and args.host:
    dst_dir = args.dst + "/" + plat
    dst = args.host + ":" + dst_dir + "/" + libzip

    cmd = "ssh " + args.host + " 'mkdir -p " + dst_dir + "'"
    print(cmd)
    os.system(cmd)

    cmd = "rsync -v -e ssh " + src + " " + dst
    print(cmd) 
    os.system(cmd)
