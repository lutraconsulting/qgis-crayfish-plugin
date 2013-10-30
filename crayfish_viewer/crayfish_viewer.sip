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
    int getLastError();
    bool loadDataSet(QString);
    bool isDataSetLoaded(QString fileName);

    double valueAtCoord(const Output *output, double xCoord, double yCoord);

    // mesh information

    uint nodeCount() const;
    uint elementCount() const;
    uint elementCount_E4Q() const;
    uint elementCount_E3T() const;
    QRectF meshExtent() const;

    // rendering options

    void setCanvasSize(const QSize& size);
    QSize canvasSize() const;

    void setExtent(double llX, double llY, double pixelSize);
    QRectF extent() const;
    double pixelSize() const;

    void setMeshRenderingEnabled(bool enabled);
    bool isMeshRenderingEnabled() const;

    void setMeshColor(const QColor& color);
    QColor meshColor() const;

    void setCurrentDataSetIndex(int index);
    int currentDataSetIndex() const;
    int dataSetCount() const;
    const DataSet* dataSet(int dataSetIndex) const;
    const DataSet* currentDataSet() const;

    void setNoProjection();
    bool setProjection(const QString& srcProj4, const QString& destProj4);
    bool hasProjection() const;
    QString sourceCrsProj4() const;
    QString destCrsProj4() const;

};


enum VectorLengthMethod{
    MinMax,  //!< minimal and maximal length
    Scaled,  //!< length is scaled proportionally to the magnitude
    Fixed    //!< length is fixed to a certain value
};


namespace DataSetType{
    enum Enum{
        Bed,
        Scalar,
        Vector
    };
};

struct DataSet
{
%TypeHeaderCode
#include <crayfish_dataset.h>
%End

    DataSet(const QString& fileName);
    ~DataSet();

    QString fileName() const;

    void setName(const QString& name);
    QString name() const;

    void setType(DataSetType::Enum t);
    DataSetType::Enum type() const;

    uint outputCount() const;

    //void addOutput(Output* output);

    void setCurrentOutputTime(int outputTime);
    int currentOutputTime() const;
    const Output* output(int outputTime) const;
    const Output* currentOutput() const;

    void updateZRange(int nodeCount);
    float minZValue() const;
    float maxZValue() const;

    void setIsTimeVarying(bool varying);
    bool isTimeVarying() const;

    // -- contour rendering --

    void setContourRenderingEnabled(bool enabled);
    bool isContourRenderingEnabled() const;

    void setContourColorMap(const ColorMap& cm);
    const ColorMap& contourColorMap() const;

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

    // -- custom (GUI-specific) settings --

    void setCustomValue(const QString& key, const QVariant& value);
    QVariant customValue(const QString& key) const;
    void clearCustomValue(const QString& key);
    QStringList customValues() const;
};


struct Output{
%TypeHeaderCode
#include <crayfish_output.h>
%End

    Output();
    ~Output();
    //void init(int nodeCount, int elemCount, bool isVector);

    float time;
    //char* statusFlags;   //!< array determining which elements are active and therefore if they should be rendered (size = element count)
    //float* values;       //!< array of values per node (size = node count)
    //float* values_x;     //!< in case of dataset with vector data - array of X coords - otherwise 0
    //float* values_y;     //!< in case of dataset with vector data - array of Y coords - otherwise 0
};



struct ColorMap
{
%TypeHeaderCode
#include <crayfish_colormap.h>
%End

  struct Item
  {
    Item(double v = 0, QRgb c = 0);

    double value;
    QRgb color;
    QString label;
  };

  enum Method { Linear, Discrete };
  Method method;

  QVector<ColorMap::Item> items;
  int alpha;

  void clearItems();
  void addItem(const ColorMap::Item& item);
  void removeItem(int index);
  void moveItem(int indexOld, int indexNew);
  ColorMap::Item& item(int index);

  void dump() const;

  QRgb value(double v) const;

  QPixmap previewPixmap(const QSize& size, double vMin, double vMax);

  /** default "cold-to-hot" color map */
  static ColorMap defaultColorMap(double vMin, double vMax);

};


%UnitCode
#include <version.h>
%End

QString version();
