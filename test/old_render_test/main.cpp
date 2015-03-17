#include <QtCore/QCoreApplication>
#include <QLibrary>
#include "crayfish_viewer.h"
#include "crayfish_e4q.h"
#include "crayfish_colormap.h"
#include "crayfish_dataset.h"

#if 0

void dumpL2P(double x, double y, const E4Qtmp& t)
{
  double Px, Py;
  E4Q_mapLogicalToPhysical(t, x, y, Px, Py);
  qDebug("[%f,%f] -> [%f,%f]", x, y, Px, Py);
}

void dumpP2L(double x, double y, const E4Qtmp& t)
{
  double Lx, Ly;
  E4Q_mapPhysicalToLogical(t, x, y, Lx, Ly);
  qDebug("[%f,%f] -> [%f,%f]", x, y, Lx, Ly);
}


  // create our E4Q
  Node nodes[] = {
    { -1, -1 },
    {  8,  3 },
    { 13, 11 },
    { -4,  8 }
  };

  // test with a square
  /*
  Node p2 = { 0,  2, -1 };
  Node p3 = { 0,  2,  2 };
  Node p4 = { 0, -1,  2 };
  */

  Element testElem;
  for (int i = 0; i < 4; ++i)
    testElem.p[i] = i;

  E4Qtmp testE4Q;

  E4Q_computeMapping(testElem, testE4Q, nodes);

  dumpL2P(0,0, testE4Q);
  dumpL2P(1,0, testE4Q);
  dumpL2P(0,1, testE4Q);
  dumpL2P(1,1, testE4Q);
  dumpL2P(0.5,0.5, testE4Q);

  qDebug("---");

  dumpP2L(-1,-1, testE4Q);
  dumpP2L( 8, 3, testE4Q);
  dumpP2L(13,11, testE4Q);
  dumpP2L(-4, 8, testE4Q);
  dumpP2L(2,2, testE4Q);

  qDebug("complex: %d", E4Q_isComplex(testElem, nodes));
#endif



int main(int argc, char *argv[])
{
    QCoreApplication a(argc, argv);

    if (argc != 3)
    {
      qWarning("Syntax: %s <2dm file> <output image>", argv[0]);
      return 1;
    }

    const char* meshName = argv[1];
    const char* imgName = argv[2];

    int datasetIdx = 0;
    int outputTime = 0;
    double mupp = 10;

#if 1
    meshName             = "/data/lutra/illuvis-export-test/ivs_001.2dm";
    const char* dataName = "/data/lutra/illuvis-export-test/ivs_001_d.dat";
    imgName              = "/data/lutra/illuvis-export-test/ivs_001_d_crayfish.tif";
    datasetIdx = 1;
    outputTime = 101;
    mupp = 2;
    QString wkt = "PROJCS[\"OSGB_1936_British_National_Grid\",GEOGCS[\"GCS_OSGB 1936\",DATUM[\"D_OSGB_1936\",SPHEROID[\"Airy_1830\",6377563.396,299.3249646]],PRIMEM[\"Greenwich\",0],UNIT[\"Degree\",0.017453292519943295]],PROJECTION[\"Transverse_Mercator\"],PARAMETER[\"latitude_of_origin\",49],PARAMETER[\"central_meridian\",-2],PARAMETER[\"scale_factor\",0.9996012717],PARAMETER[\"false_easting\",400000],PARAMETER[\"false_northing\",-100000],UNIT[\"Meter\",1]]";
#endif

    int imgWidth = 640; // height is computed from mesh's shape

    qDebug("Loading mesh (%s) ...", meshName);
    CrayfishViewer* s = new CrayfishViewer(meshName);
    if (!s->loadedOk())
    {
      qWarning("Failed to load the mesh! (%d)", s->getLastError());
      return 1;
    }
#if 1
    qDebug("Loading dataset (%s) ...", dataName);
    s->loadDataSet(dataName);
#endif

    qDebug("Exporting (%s) ...", imgName);
    s->exportRawDataToTIF(datasetIdx, outputTime, mupp, imgName, wkt);
    return 0;

    QRectF meshExtent = s->meshExtent();
    qDebug("mesh extent: min %f,%f  max %f,%f", meshExtent.left(), meshExtent.top(), meshExtent.right(), meshExtent.bottom());
    double pixelSize = meshExtent.width() / imgWidth;
    int imgHeight = meshExtent.height() / pixelSize;
    qDebug("img size: %d,%d", imgWidth, imgHeight);
    qDebug("pixel size: %f", pixelSize);

    s->setCanvasSize(QSize(imgWidth, imgHeight));
    s->setExtent(meshExtent.left(), meshExtent.top(), pixelSize);

    ColorMap cm;
    cm.items.append(ColorMap::Item(10, qRgb(255,0,0)));
    cm.items.append(ColorMap::Item(30, qRgb(255,255,0)));
    cm.items.append(ColorMap::Item(50, qRgb(0,0,255)));
    ((DataSet*)s->currentDataSet())->setContourColorMap(cm);

    qDebug("dataset: %d", s->currentDataSetIndex());
    if (!s->currentDataSet())
      return 2;

    qDebug("Drawing...");
    QImage* img = s->draw();
    if (!img)
    {
      qWarning("Failed to render image!");
      return 1;
    }

    qDebug("Saving (%s) ...", imgName);
    img->save(imgName);

    // Try to interpolate a value:
    // double val = s->valueAtCoord(0, 0, 394798.247423, 173689.113402);

    delete s;

    return 0;
}
