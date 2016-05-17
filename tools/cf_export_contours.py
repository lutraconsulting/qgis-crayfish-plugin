
import sys
sys.path.append('..')
import crayfish

if len(sys.argv) != 3:
  print "Syntax: %s <2dm file> <output SHP>" % sys.argv[0]
  sys.exit(1)

try:
  m = crayfish.Mesh(sys.argv[1])
except ValueError:
  print "Failed to load mesh in %s" % sys.argv[1]
  sys.exit(1)

print "Exporting..."
resolution = 10
interval = 3
wkt = ""
m.dataset(0).output(0).export_contours(resolution, interval, sys.argv[2], wkt)
print "done."
