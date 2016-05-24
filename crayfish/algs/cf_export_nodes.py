
import sys
sys.path.append('..')
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

vl = QgsVectorLayer("Point?field=node_id:integer&field=value:double", "nodes", "memory")
flds = vl.pendingFields()

o = m.dataset(0).output(0)

lst = []
for index, n in enumerate(m.nodes()):
  f = QgsFeature()
  f.setFields(flds)
  f.setGeometry(QgsGeometry.fromPoint(QgsPoint(n.x, n.y)))
  f[0] = n.id
  f[1] = o.value(index)
  lst.append(f)

vl.dataProvider().addFeatures(lst)

QgsVectorFileWriter.writeAsVectorFormat(vl, shp_filename, '', None)

del vl
