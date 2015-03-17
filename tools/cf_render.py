
import sys
from PyQt4.QtGui import QImage
sys.path.append('../plugin')
import crayfish

if len(sys.argv) != 5:
  print "Syntax: %s <2dm file> <image width> <image height> <output image filename>" % sys.argv[0]
  sys.exit(1)

size = (int(sys.argv[2]), int(sys.argv[3]))
output_filename = sys.argv[4]

try:
  m = crayfish.Mesh(sys.argv[1])
except ValueError:
  print "Failed to load mesh in %s" % sys.argv[1]
  sys.exit(1)

o = m.dataset(0).output(0)

extent = m.extent()
muppx = (extent[2]-extent[0])/size[0]
muppy = (extent[3]-extent[1])/size[1]
mupp = max(muppx,muppy)
cx = (extent[2]+extent[0])/2
cy = (extent[3]+extent[1])/2
ll = (cx - (size[0]/2)*mupp, cy - (size[1]/2)*mupp)

rconfig = crayfish.RendererConfig()
rconfig.set_view(size, ll, mupp)
rconfig.set_output(o)

img = QImage(size[0],size[1], QImage.Format_ARGB32)

r = crayfish.Renderer(rconfig, img)
r.draw()

img.save(output_filename)
