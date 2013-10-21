#include <QtCore/QCoreApplication>
#include <QLibrary>
#include "crayfish_viewer.h"
#include "crayfish_e4q.h"

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


int main(int argc, char *argv[])
{

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

#if 0
    QCoreApplication a(argc, argv);

    QString meshName = "/home/pete/dev/qgis-crayfish-plugin/crayfish_viewer_test/Test Data/triangles.2dm";
    QString datName = "C:\\Users\\pete\\Documents\\tmp\\Crayfish Bugs\\tutorial_run_number_03_d.dat";
    CrayfishViewer* s = new CrayfishViewer(meshName);
    if(! s->loadedOk()){
        return 1;
    }

    /*if(! s->loadDataSet(datName) ){
        return 1;
    }

    if( ! s->loadedOk() )
        return 1;*/

    float minVal = s->minValue(0);
    float maxVal = s->maxValue(0);

    QRectF extent = s->getExtents();

    int w = 1000;
    int h = 600;

    /*QImage* img = s->draw(  true,     // Render scalar
                            true,     // Render vector
                            w,        // Image width
                            h,        // Image height
                            extent.left(),   // Image llX
                            extent.bottom(),   // Image llY,
                            (extent.width() / double(w)),
                            // 0.025,
                            1, // Dataset (0=2dm, rest=dat)
                            20, // Output time
                            true, // auto render
                            0.0, // render min
                            0.0); // render max*/

    /*
    QImage* draw(bool,
                 bool,
                 int,
                 int,
                 double,
                 double,
                 double,
                 int dataSetIdx,
                 int outputTime,

                 bool autoContour,
                 float minContour,
                 float maxContour,

                 VectorLengthMethod shaftLengthCalculationMethod,
                 float minShaftLength,
                 float maxShaftLength,
                 float scaleFactor,
                 float fixedShaftLength,
                 int lineWidth, float vectorHeadWidthPerc, float vectorHeadLengthPerc);
    */

    QImage* img = s->draw(  true,
                            true,
                            1070,
                            582,
                            99000.0, // llx
                            99000.0, // lly
                            2.0, // px size
                            0, // ds
                            0, // time

                            true,
                            0.0,
                            0.0,

                            CrayfishViewer::Scaled,
                            3.0,
                            50.0,
                            5.0,
                            10.0,
                            1,
                            15.0,
                            40.0);

    img->save("/tmp/output.png");

    // Try to interpolate a value:
    // double val = s->valueAtCoord(0, 0, 394798.247423, 173689.113402);
    return 0;

    // return a.exec();
#endif
}
