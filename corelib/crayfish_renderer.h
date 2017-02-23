/*
Crayfish - A collection of tools for TUFLOW and other hydraulic modelling packages
Copyright (C) 2016 Lutra Consulting

info at lutraconsulting dot co dot uk
Lutra Consulting
23 Chestnut Close
Burgess Hill
West Sussex
RH15 8HN

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
*/

#ifndef CRAYFISH_RENDERER_H
#define CRAYFISH_RENDERER_H

#include "crayfish_dataset.h"
#include "crayfish_mesh.h"
#include <QImage>
#include <QSize>
#include <QPolygonF>

// TODO: use also directly for viewer rendering
class MapToPixel
{
public:
  MapToPixel(double llX, double llY, double mupp, int rows)
    : mLlX(llX), mLlY(llY), mMupp(mupp), mRows(rows) {}

  MapToPixel(const MapToPixel &obj)
  : mLlX(obj.mLlX), mLlY(obj.mLlY), mMupp(obj.mMupp), mRows(obj.mRows) {}

  QPointF realToPixel(double rx, double ry) const
  {
    double px = (rx - mLlX) / mMupp;
    double py = mRows - (ry - mLlY) / mMupp;
    return QPointF(px, py);
  }


  QPointF realToPixel(const QPointF& pt) const {
      return realToPixel(pt.x(), pt.y());
  }

  QPointF pixelToReal(double px, double py) const
  {
      double rx = mLlX + (px * mMupp);
      double ry = mLlY + mMupp * (mRows - py);
      return QPointF(rx,ry);
  }

  QPointF pixelToReal(const QPointF& pt) const {
      return pixelToReal(pt.x(), pt.y());
  }

private:
  double mLlX, mLlY;
  double mMupp; // map units per pixel
  double mRows; // (actually integer value)
};


struct Node;
struct BBox;
struct E4Qtmp;

struct ConfigMesh
{
  ConfigMesh():
      mRenderMesh(false),
      mMeshBorderColor(Qt::black),
      mMeshBorderWidth(1),
      mMeshFillColor(Qt::transparent),
      mMeshFillEnabled(false),
      mMeshElemLabel(false) {}

  bool mRenderMesh;   //!< whether to render the mesh as a wireframe/fill
  QColor mMeshBorderColor;  //!< color used for rendering of the wireframe
  int mMeshBorderWidth; //!< width of wireframe
  QColor mMeshFillColor;  //!< color used for rendering of the wireframe fill
  bool mMeshFillEnabled; //!< if to fill element with mMeshFillColor
  bool mMeshElemLabel;  //!< whether to render the element ids in a mesh element's center
};

struct ConfigDataSet
{
  ConfigDataSet()
    : mShaftLengthMethod(MinMax)
    , mMinShaftLength(3)
    , mMaxShaftLength(40)
    , mScaleFactor(10)
    , mFixedShaftLength(10)
    , mLineWidth(1)
    , mVectorHeadWidthPerc(15)
    , mVectorHeadLengthPerc(40)
    , mVectorUserGrid(false)
    , mVectorUserGridCellSize(10, 10)
    , mVectorFilterMin(-1)
    , mVectorFilterMax(-1)
    , mVectorColor(Qt::black)
  {}


  enum VectorLengthMethod
  {
    MinMax,  //!< minimal and maximal length
    Scaled,  //!< length is scaled proportionally to the magnitude
    Fixed    //!< length is fixed to a certain value
  };

  // contour rendering settings
  ColorMap mColorMap; //!< actual color map used for rendering

  // vector rendering settings
  VectorLengthMethod mShaftLengthMethod;
  float mMinShaftLength;    //!< valid if using "min/max" method
  float mMaxShaftLength;    //!< valid if using "min/max" method
  float mScaleFactor;       //!< valid if using "scaled" method
  float mFixedShaftLength;  //!< valid if using "fixed" method
  int mLineWidth;           //!< pen width for drawing of the vectors
  float mVectorHeadWidthPerc;   //!< arrow head's width  (in percent to shaft's length)
  float mVectorHeadLengthPerc;  //!< arrow head's length (in percent to shaft's length)
  bool mVectorUserGrid;         //!< whether to display vectors on a grid instead of nodes
  QSize mVectorUserGridCellSize;//!< size of user grid (in pixels) for vector arrows
  float mVectorFilterMin;   //!< minimum vector magnitude in order to be drawn. negative value == no filter for minimum
  float mVectorFilterMax;   //!< maximum vector magnitude in order to be drawn. negative value == no filter for maximum
  QColor mVectorColor;      //!< color of arrows
  bool mVectorTrace; //!< whether to render trace animation
  int mVectorTraceFPS; //!< fps (frames per second) of trace animation; if 0, we are showing steady streamlines (no animation)
  int mVectorTraceCalculationSteps; //! maximum number of calculation steps to in one streamline
  int mVectorTraceAnimationSteps; //! number of calculation steps to be animated by gradient from transparent color to mVectorColor
};

//! Master configuration for rendering
struct RendererConfig
{
  RendererConfig()
    : outputMesh(0)
    , outputContour(0)
    , outputVector(0)
    , llX(0)
    , llY(0)
    , pixelSize(0) {}

  // data
  const Mesh* outputMesh;
  const Output* outputContour;
  const Output* outputVector;

  // view
  QSize outputSize;
  double llX;
  double llY;
  double pixelSize;

  // appearance
  ConfigMesh mesh;
  ConfigDataSet ds;

};

bool calcVectorLineEnd(
        QPointF& lineEnd, float& vectorLength, double& cosAlpha, double& sinAlpha, //out
        const RendererConfig* mCfg, const Output* output, const QPointF& lineStart, float xVal, float yVal, float* V=0 //in
        );

class Renderer
{
friend class TraceRendererCache;
public:
  Renderer(const RendererConfig& cfg, QImage& img);

  void draw();

protected:
  void drawMeshFill();
  void drawMeshFrame();
  void drawMeshLabels();

  QPolygonF elementPolygonPixel(const Element& elem);
  void drawContourData(const Output* output);
  void drawVectorData(const Output* output);
  void drawVectorDataOnGrid(QPainter& p, const Output* output);
  void drawVectorDataOnNodes(QPainter& p, const NodeOutput* output);
  void drawVectorDataOnElements(QPainter& p, const ElementOutput* output);
  void drawVectorDataAsTrace(QPainter& p);
  void drawVectorDataStreamLines(QPainter& p);
  void drawVectorArrow(QPainter& p, const Output* output, const QPointF& lineStart, float xVal, float yVal, float* V=0);

  void validateCache();

  bool pointInsideView(double x, double y);
  bool nodeInsideView(uint nodeIndex);
  bool elemOutsideView(uint);
  void paintRow(uint, int, int, int, const Output* output);
  void paintLine(const Element& elem, const Output* output);
  void bbox2rect(const BBox& bbox, int& leftLim, int& rightLim, int& topLim, int& bottomLim);

  //! rendering configuration
  RendererConfig mCfg;

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

  const Output* mOutputContour; //!< data to be rendered
  const Output* mOutputVector;  //!< data to be rendered
  const Mesh* mMesh;
};

#endif // CRAYFISH_RENDERER_H
