// Define the SIP wrapper to the crayfishviewer library.

%Module crayfishviewer

%Import QtGui/QtGuimod.sip

class CrayfishViewer {

%TypeHeaderCode
#include <crayfish_viewer.h>
%End

public:
    enum VectorLengthMethod{
        DefineMinAndMax,
        Scaled,
        Fixed
    };
    CrayfishViewer(QString);
    ~CrayfishViewer();
    QImage* draw(bool,
                 bool,
                 int,
                 int,
                 double,
                 double,
                 double,
                 int,
                 int,

                 bool,
                 float,
                 float,

                 VectorLengthMethod,
                 float,
                 float,
                 float,
                 float,
                 int,
                 float,
                 float);
    bool loadedOk();
    bool warningsEncountered();
    int getLastWarning();
    QRectF getExtents();
    bool loadDataSet(QString);
    int dataSetCount();
    QString* dataSetName(int);
    int dataSetOutputCount(int);
    float dataSetOutputTime(int, int);
    bool timeVarying(int);
    int getLastRenderIndex(int);
    bool layerContouredAutomatically(int);
    float minValue(int);
    float maxValue(int);
    float lastMinContourValue(int);
    float lastMaxContourValue(int);
    bool isBed(int);
    bool isVector(int);
    bool displayContours(int);
    bool displayVectors(int);
    bool displayMesh();
    void setDisplayMesh(bool display);
    double valueAtCoord(int, int, double, double);
};

%UnitCode
#include <version.h>
%End

QString version();
