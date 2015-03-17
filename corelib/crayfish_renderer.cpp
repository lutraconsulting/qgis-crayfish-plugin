#include "crayfish_renderer.h"

#include "crayfish_dataset.h"
#include "crayfish_e4q.h"
#include "crayfish_mesh.h"
#include "crayfish_output.h"

#include <QImage>
#include <QPainter>
#include <QVector2D>

Renderer::Renderer(const Config& cfg, QImage& img)
  : mCfg(cfg)
  , mtp(cfg.llX, cfg.llY, cfg.pixelSize, cfg.outputSize.height())
  , mImage(img)
{
  mLlX = cfg.llX;
  mLlY = cfg.llY;
  mPixelSize = cfg.pixelSize;
  mOutputSize = cfg.outputSize;

  mUrX = mLlX + (mOutputSize.width()*mPixelSize);
  mUrY = mLlY + (mOutputSize.height()*mPixelSize);

  mOutput = cfg.output;
  mDataSet = mOutput ? mOutput->dataSet : 0;
  mMesh = mDataSet ? mDataSet->mesh() : 0;

  // use a default color map if none specified
  if (mCfg.ds.mRenderContours && mCfg.ds.mColorMap.items.count() == 0 && mDataSet)
  {
    double vMin = mDataSet->minZValue(), vMax = mDataSet->maxZValue();
    mCfg.ds.mColorMap = ColorMap::defaultColorMap(vMin, vMax);
  }
}



void Renderer::draw()
{
  if (!mOutput || !mDataSet || !mMesh)
    return; // nothing to do

  //mImage = QImage(mOutputSize, QImage::Format_ARGB32);
  //mImage.fill( qRgba(255,255,255,0) );

  if (mCfg.ds.mRenderContours)
    drawContourData(mOutput);

  if (mCfg.mesh.mRenderMesh)
    drawMesh();

  if (mCfg.ds.mRenderVectors && mDataSet->type() == DataSet::Vector)
    drawVectorData(mOutput);
}


void Renderer::drawMesh()
{
  // render mesh as a wireframe

  QPainter p(&mImage);
  p.setPen(mCfg.mesh.mMeshColor);
  QPoint pts[5];
  const Mesh::Elements& elems = mMesh->elements();
  for (int i=0; i < elems.count(); ++i)
  {
    const Element& elem = elems[i];
    if( elem.isDummy() )
        continue;

    // If the element is outside the view of the canvas, skip it
    if( elemOutsideView(i) )
        continue;

    if (elem.eType == Element::E4Q)
    {
      pts[0] = pts[4] = realToPixel( elem.p[0] ); // first and last point
      pts[1] = realToPixel( elem.p[1] );
      pts[2] = realToPixel( elem.p[2] );
      pts[3] = realToPixel( elem.p[3] );
      p.drawPolyline(pts, 5);
    }
    else if (elem.eType == Element::E3T)
    {
      pts[0] = pts[3] = realToPixel( elem.p[0] ); // first and last point
      pts[1] = realToPixel( elem.p[1] );
      pts[2] = realToPixel( elem.p[2] );
      p.drawPolyline(pts, 4);
    }
  }
}




void Renderer::drawContourData(const Output* output)
{
  // Render E4Q before E3T
  QVector<Element::Type> typesToRender;
  typesToRender.append(Element::E4Q);
  typesToRender.append(Element::E3T);
  QVectorIterator<Element::Type> it(typesToRender);
  while(it.hasNext())
  {
    Element::Type elemTypeToRender = it.next();

    const Mesh::Elements& elems = mMesh->elements();
    for(int i = 0; i < elems.count(); i++){

      const Element& elem = elems[i];
      if( elem.eType != elemTypeToRender )
          continue;

      if( elem.isDummy() )
          continue;

      // For each element

      // If the element's activity flag is off, ignore it
      if( ! output->active[i] ){
          continue;
      }

      // If the element is outside the view of the canvas, skip it
      if( elemOutsideView(i) ){
          continue;
      }

      const BBox& bbox = mMesh->projectedBBox(i);

      // Get the BBox of the element in pixels
      QPoint ll = mtp.realToPixel(bbox.minX, bbox.minY).toPoint();
      QPoint ur = mtp.realToPixel(bbox.maxX, bbox.maxY).toPoint();
      int topLim = std::max( ur.y(), 0 );
      int bottomLim = std::min( ll.y(), mOutputSize.height()-1 );
      int leftLim = std::max( ll.x(), 0 );
      int rightLim = std::min( ur.x(), mOutputSize.width()-1 );

      for(int j=topLim; j<=bottomLim; j++)
      {
          paintRow(i, j, leftLim, rightLim, output);
      }
    } // for all elements

  } // for element types
}


inline float mag(float input)
{
    if(input < 0.0){
        return -1.0;
    }
    return 1.0;
}

void Renderer::drawVectorData(const Output* output)
{
  Config::DataSet::VectorLengthMethod shaftLengthCalculationMethod = mCfg.ds.mShaftLengthMethod;
  float minShaftLength   = mCfg.ds.mMinShaftLength;
  float maxShaftLength   = mCfg.ds.mMaxShaftLength;
  float scaleFactor      = mCfg.ds.mScaleFactor;
  float fixedShaftLength = mCfg.ds.mFixedShaftLength;
  int lineWidth          = mCfg.ds.mLineWidth;
  float vectorHeadWidthPerc  = mCfg.ds.mVectorHeadWidthPerc;
  float vectorHeadLengthPerc = mCfg.ds.mVectorHeadLengthPerc;

  /*
    Here is where we render vector data

    Vectors will either be rendered at nodes or on a grid spacing specified by the user.
    In the latter case, the X and Y components will need to be interpolated

    In the case of rendering vectors at nodes:
      Loop through all nodes:
          If node is within the current screen extent:
              Render it:
                  Get the X and Y components
                  Turn those compnents into pixel distances
                  Render an arrow from the node
  */

  // Set up the render configuration options

  // Determine the min and max magnitudes in this layer
  float minVal = output->dataSet->minZValue();
  float maxVal = output->dataSet->maxZValue();

  // Get a list of nodes that are within the current render extent
  std::vector<int> candidateNodes;

  const Mesh::Nodes& nodes = mMesh->nodes();
  for(int i = 0; i < nodes.count(); i++)
  {
    if (nodeInsideView(i))
      candidateNodes.push_back( i );
  }


  QPainter p(&mImage);
  p.setRenderHint(QPainter::Antialiasing);
  p.setBrush( Qt::SolidPattern );
  QPen pen = p.pen();
  pen.setCapStyle(Qt::FlatCap);
  pen.setJoinStyle(Qt::MiterJoin);
  pen.setWidth( lineWidth );
  p.setPen(pen);

  // Make a set of vector head coordinates that we will place at the end of each vector,
  // scale, translate and rotate.
  QPointF vectorHeadPoints[3];
  QPointF finalVectorHeadPoints[3];

  // First head point:  top of ->
  vectorHeadPoints[0].setX( -1.0 * vectorHeadLengthPerc * 0.01 );
  vectorHeadPoints[0].setY( vectorHeadWidthPerc * 0.5 * 0.01 );

  // Second head point:  right of ->
  vectorHeadPoints[1].setX(0.0);
  vectorHeadPoints[1].setY(0.0);

  // Third head point:  bottom of ->
  vectorHeadPoints[2].setX( -1.0 * vectorHeadLengthPerc * 0.01 );
  vectorHeadPoints[2].setY( -1.0 * vectorHeadWidthPerc * 0.5 * 0.01 );

  for(uint i=0; i<candidateNodes.size(); i++)
  {
    // Get the value
    uint nodeIndex = candidateNodes.at(i);

    float xVal = output->valuesV[nodeIndex].x;
    float yVal = output->valuesV[nodeIndex].y;
    float V = output->values[nodeIndex];  // pre-calculated magnitude

    if(xVal == 0.0 && yVal == 0.0){
      continue;
    }

    // Now determine the X and Y distances of the end of the line from the start

    float xDist = 0.0;
    float yDist = 0.0;

    // Determine the angle of the vector, counter-clockwise, from east
    // (and associated trigs)
    double vectorAngle = -1.0 * atan( (-1.0 * yVal) / xVal );
    double cosAlpha = cos( vectorAngle ) * mag(xVal);
    double sinAlpha = sin( vectorAngle ) * mag(xVal);

    if(shaftLengthCalculationMethod == Config::DataSet::MinMax){
      double k = (V - minVal) / (maxVal - minVal);
      double L = minShaftLength + k * (maxShaftLength - minShaftLength);
      xDist = cosAlpha * L;
      yDist = sinAlpha * L;
    }else if(shaftLengthCalculationMethod == Config::DataSet::Scaled){
      xDist = scaleFactor * xVal;
      yDist = scaleFactor * yVal;
    }else{
      // We must be using a fixed length
      xDist = cosAlpha * fixedShaftLength;
      yDist = sinAlpha * fixedShaftLength;
    }

    // Flip the Y axis (pixel vs real-world axis)
    yDist *= -1.0;

    if(qAbs(xDist) < 1 && qAbs(yDist) < 1){
      continue;
    }

    // Determine the line coords
    QPointF lineStart = realToPixelF( nodeIndex );
    QPointF lineEnd = QPointF( lineStart.x() + xDist,
                               lineStart.y() + yDist);

    float vectorLength = sqrt( pow(lineEnd.x() - lineStart.x(), 2) + pow(lineEnd.y() - lineStart.y(), 2) );

    // Check to see if any of the coords are outside the QImage area, if so, skip the whole vector
    if( lineStart.x() < 0 ||
      lineStart.x() > mOutputSize.width() ||
      lineStart.y() < 0 ||
      lineStart.y() > mOutputSize.height() ||
      lineEnd.x() < 0 ||
      lineEnd.x() > mOutputSize.width() ||
      lineEnd.y() < 0 ||
      lineEnd.y() > mOutputSize.height() ){

      continue;
    }

    // Determine the arrow head coords
    for(int j=0; j<3; j++){

      finalVectorHeadPoints[j].setX(   lineEnd.x()
                                     + ( vectorHeadPoints[j].x() * cosAlpha * vectorLength )
                                     - ( vectorHeadPoints[j].y() * sinAlpha * vectorLength )
                                   );

      finalVectorHeadPoints[j].setY(   lineEnd.y()
                                     - ( vectorHeadPoints[j].x() * sinAlpha * vectorLength )
                                     - ( vectorHeadPoints[j].y() * cosAlpha * vectorLength )
                                   );
    }

    // Now actually draw the vector
    p.drawLine(lineStart, lineEnd);
    p.drawPolygon( (const QPointF*)&finalVectorHeadPoints, 3);
    bool debug = false;
    if(debug){
      // Write the ID of the node next to the vector...
      QPointF tp;
      tp.setX( lineEnd.x() + 10.0 );
      tp.setY( lineEnd.y() - 10.0 );
      QString nodeText;
      nodeText.setNum(nodeIndex);
      p.drawText( tp, nodeText );
    }

  }
  p.end();
}


void Renderer::paintRow(uint elementIdx, int rowIdx, int leftLim, int rightLim, const Output* output)
{
  /*
    Grab the pointer to the row if we do not have it already
    */
  QRgb* line = (QRgb*) mImage.scanLine(rowIdx);

  for(int j=leftLim; j<=rightLim; j++)
  {
    // Determine real-world coords
    // Interpolate a value from the element
    // Set the value in the QImage
    QPointF p = mtp.pixelToReal(j, rowIdx);

    double val;
    if( mMesh->valueAt(elementIdx, p.x(), p.y(), &val, output) )
    {
        // The supplied point was inside the element
        line[j] = mCfg.ds.mColorMap.value(val);
    }
  }
}


bool Renderer::nodeInsideView(uint nodeIndex)
{
  const Node& n = mMesh->projectedNode(nodeIndex);
  return n.x > mLlX && n.x < mUrX && n.y > mLlY && n.y < mUrY;
}

bool Renderer::elemOutsideView(uint i)
{
  const BBox& bbox = mMesh->projectedBBox(i);
  // Determine if this element is visible within the view
  return bbox.maxX < mLlX || bbox.minX > mUrX || bbox.minY > mUrY || bbox.maxY < mLlY;
}


QPoint Renderer::realToPixel(int nodeIndex)
{
  return realToPixelF(nodeIndex).toPoint();
}

QPointF Renderer::realToPixelF(int nodeIndex)
{
  const Node& n = mMesh->projectedNode(nodeIndex);
  return mtp.realToPixel(n.x, n.y);
}
