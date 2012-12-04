#include <QtCore/QCoreApplication>
#include <QLibrary>
#include "crayfish_viewer.h"

int main(int argc, char *argv[])
{
    QCoreApplication a(argc, argv);

    QString meshName = "C:\\Users\\pete\\Documents\\tmp\\Crayfish Bugs\\TUTORIAL Model Does Not Work\\M01_5m_001.2dm";
    QString datName = "C:\\Users\\pete\\Documents\\tmp\\Crayfish Bugs\\TUTORIAL Model Does Not Work\\M01_5m_001_d.dat";
    CrayfishViewer* s = new CrayfishViewer(meshName);
    if(! s->loadedOk()){
        return 1;
    }

    if(! s->loadDataSet(datName) ){
        return 1;
    }

    if( ! s->loadedOk() )
        return 1;

    float minVal = s->minValue(1);
    float maxVal = s->maxValue(1);

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
                            395335.669942,
                            173006.572809,
                            0.0823131443299,
                            1, // ds
                            3, // time

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

    img->save("/home/pete/dev/qgis/crayfishViewer/crayfish_viewer/test_data/output.png");

    // Try to interpolate a value:
    // double val = s->valueAtCoord(0, 0, 394798.247423, 173689.113402);
    return 0;

    // return a.exec();
}
