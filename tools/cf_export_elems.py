
import sys
sys.path.append('../plugin')
import crayfish

if len(sys.argv) != 3:
  print "Syntax: %s <2dm file> <output SHP>" % sys.argv[0]
  sys.exit(1)

shp_filename = sys.argv[2]

try:
  m = crayfish.Mesh(sys.argv[1])
except ValueError:
  print "Failed to load mesh in %s" % sys.argv[1]
  sys.exit(1)


from qgis.core import QgsApplication, QgsVectorLayer, QgsVectorFileWriter, QgsPoint, QgsGeometry, QgsFeature
a = QgsApplication([], True)
a.initQgis()

def n2pt(node_index, mesh):
  n = mesh.node(node_index)
  return QgsPoint(n.x, n.y)

vl = QgsVectorLayer("Polygon?field=elem_id:integer", "elements", "memory")
flds = vl.pendingFields()

lst = []
for elem in m.elements():
  ring = []
  ring.append(n2pt(elem.p[0], m))
  ring.append(n2pt(elem.p[1], m))
  ring.append(n2pt(elem.p[2], m))
  if elem.type != 2:
    ring.append(n2pt(elem.p[3], m))
  ring.append(n2pt(elem.p[0], m))
  f = QgsFeature()
  f.setFields(flds)
  f.setGeometry(QgsGeometry.fromPolygon([ring]))
  f[0] = elem.id
  lst.append(f)

vl.dataProvider().addFeatures(lst)

QgsVectorFileWriter.writeAsVectorFormat(vl, shp_filename, '', None)

del vl
