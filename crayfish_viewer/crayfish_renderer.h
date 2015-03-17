#ifndef CRAYFISH_RENDERER_H
#define CRAYFISH_RENDERER_H

#include "crayfish_dataset.h"

#include <QImage>
#include <QSize>


// TODO: use also directly for viewer rendering
class MapToPixel
{
public:
  MapToPixel(double llX, double llY, double mupp, int rows)
    : mLlX(llX), mLlY(llY), mMupp(mupp), mRows(rows) {}

  QPointF realToPixel(double rx, double ry) const
  {
    double px = (rx - mLlX) / mMupp;
    double py = mRows - (ry - mLlY) / mMupp;
    return QPointF(px, py);
  }

  QPointF pixelToReal(double px, double py) const
  {
      double rx = mLlX + (px * mMupp);
      double ry = mLlY + mMupp * (mRows - py);
      return QPointF(rx,ry);
  }

private:
  double mLlX, mLlY;
  double mMupp; // map units per pixel
  double mRows; // (actually integer value)
};


struct Node;
struct BBox;
struct E4Qtmp;


class Renderer
{
public:
  struct Config
  {
    Config() : output(0), llX(0), llY(0), pixelSize(0) {}

    // data
    const Output* output;

    // view
    QSize outputSize;
    double llX;
    double llY;
    double pixelSize;

    // appearance

    struct Mesh
    {
      Mesh() : mRenderMesh(false), mMeshColor(Qt::black) {}

      bool mRenderMesh;   //!< whether to render the mesh as a wireframe
      QColor mMeshColor;  //!< color used for rendering of the wireframe
    };


    struct DataSet
    {
      DataSet()
        : mRenderContours(true)
        , mRenderVectors(true)
        , mShaftLengthMethod(MinMax)
        , mMinShaftLength(3)
        , mMaxShaftLength(40)
        , mScaleFactor(10)
        , mFixedShaftLength(10)
        , mLineWidth(1)
        , mVectorHeadWidthPerc(15)
        , mVectorHeadLengthPerc(40)
      {}

      enum VectorLengthMethod
      {
        MinMax,  //!< minimal and maximal length
        Scaled,  //!< length is scaled proportionally to the magnitude
        Fixed    //!< length is fixed to a certain value
      };

      // contour rendering settings
      bool mRenderContours; //!< whether to render contours
      ColorMap mColorMap; //!< actual color map used for rendering

      // vector rendering settings
      bool mRenderVectors;  //!< whether to render vectors (only valid for vector data)
      VectorLengthMethod mShaftLengthMethod;
      float mMinShaftLength;    //!< valid if using "min/max" method
      float mMaxShaftLength;    //!< valid if using "min/max" method
      float mScaleFactor;       //!< valid if using "scaled" method
      float mFixedShaftLength;  //!< valid if using "fixed" method
      int mLineWidth;           //!< pen width for drawing of the vectors
      float mVectorHeadWidthPerc;   //!< arrow head's width  (in percent to shaft's length)
      float mVectorHeadLengthPerc;  //!< arrow head's length (in percent to shaft's length)
    };


    Mesh mesh;
    DataSet ds;
  };


  Renderer(const Config& cfg, QImage& img);

  void draw();

protected:

  void drawMesh();
  void drawContourData(const Output* output);
  void drawVectorData(const Output* output);

  bool nodeInsideView(uint nodeIndex);
  bool elemOutsideView(uint);
  void paintRow(uint, int, int, int, const Output* output);

  //! rendering configuration
  Config mCfg;

  QSize mOutputSize;  //!< width+height of the current view (pixels)
  double mLlX;        //!< X of current view's lower-left point (mesh coords)
  double mLlY;        //!< Y of current view's lower-left point (mesh coords)
  double mUrX;        //!< X of current view's upper-right point (mesh coords)
  double mUrY;        //!< Y of current view's upper-right point (mesh coords)
  double mPixelSize;  //!< units (in mesh) per pixel (on screen)
  MapToPixel mtp;

  QPoint realToPixel(int nodeIndex);
  QPointF realToPixelF(int nodeIndex);

  QImage& mImage;

  const Output* mOutput; //!< data to be rendered
  const DataSet* mDataSet;
  const Mesh* mMesh;

};

#endif // CRAYFISH_RENDERER_H
