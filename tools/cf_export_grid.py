
import sys
sys.path.append('../plugin')
import crayfish

if len(sys.argv) != 3:
  print "Syntax: %s <2dm file> <output TIF>" % sys.argv[0]
  sys.exit(1)

try:
  m = crayfish.Mesh(sys.argv[1])
except ValueError:
  print "Failed to load mesh in %s" % sys.argv[1]
  sys.exit(1)

print "Exporting..."
m.dataset(0).output(0).export_grid(1, sys.argv[2], "")
print "done."