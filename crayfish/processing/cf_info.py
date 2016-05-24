
import sys
sys.path.append('..')
import crayfish

if len(sys.argv) == 1:
  print "Syntax: %s <2dm file>" % sys.argv[0]
  sys.exit(1)

try:
  m = crayfish.Mesh(sys.argv[1])
except ValueError:
  print "Failed to load mesh in %s" % sys.argv[1]
  sys.exit(1)


print "Nodes:    %7d" % m.node_count()
print "Elements: %7d" % m.element_count()
