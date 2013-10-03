// Define the SIP wrapper to the crayfishviewer library.

%Module crayfishviewer

%Import QtGui/QtGuimod.sip

class CrayfishViewer {

%TypeHeaderCode
#include <crayfish_viewer.h>
%End

public:

    CrayfishViewer(QString);
    ~CrayfishViewer();
    QImage* draw();
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
    double valueAtCoord(int, int, double, double);


    // new stuff - rendering options

    void setCanvasSize(const QSize& size);
    QSize canvasSize() const;

    void setExtent(double llX, double llY, double pixelSize);
    QRectF extent() const;

    void setMeshRenderingEnabled(bool enabled);
    bool isMeshRenderingEnabled() const;

    void setCurrentDataSetIndex(int index);
    int currentDataSetIndex() const;
    const DataSet* dataSet(int dataSetIndex) const;
    const DataSet* currentDataSet() const;
};


enum VectorLengthMethod{
    MinMax,  //!< minimal and maximal length
    Scaled,  //!< length is scaled proportionally to the magnitude
    Fixed    //!< length is fixed to a certain value
};

struct DataSet
{
%TypeHeaderCode
#include <crayfish_viewer_global.h>
%End

  DataSet();
  ~DataSet();

    void setCurrentOutputTime(int outputTime);
    int currentOutputTime() const;
    //const Output* output(int outputTime) const;
    //const Output* currentOutput() const;

    // -- contour rendering --

    void setContourRenderingEnabled(bool enabled);
    bool isContourRenderingEnabled() const;

    void setContourAutoRange(bool enabled);
    bool contourAutoRange() const;

    void setContourCustomRange(float vMin, float vMax);
    float contourCustomRangeMin() const;
    float contourCustomRangeMax() const;

    // -- vector rendering --

    void setVectorRenderingEnabled(bool enabled);
    bool isVectorRenderingEnabled() const;

    void setVectorShaftLengthMethod(VectorLengthMethod method);
    VectorLengthMethod vectorShaftLengthMethod() const;

    void setVectorShaftLengthMinMax(float minLen, float maxLen);
    float vectorShaftLengthMin() const;
    float vectorShaftLengthMax() const;

    void setVectorShaftLengthScaleFactor(float scaleFactor);
    float vectorShaftLengthScaleFactor() const;

    void setVectorShaftLengthFixed(float fixedLen);
    float vectorShaftLengthFixed() const;

    void setVectorPenWidth(int width);
    int vectorPenWidth() const;

    void setVectorHeadSize(float widthPerc, float lengthPerc);
    float vectorHeadWidth() const;
    float vectorHeadLength() const;
};



%UnitCode
#include <version.h>
%End

QString version();
