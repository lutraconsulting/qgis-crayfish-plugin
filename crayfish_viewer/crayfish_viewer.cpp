/*
Crayfish - A collection of tools for TUFLOW and other hydraulic modelling packages
Copyright (C) 2014 Lutra Consulting

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

#include "crayfish_viewer.h"

#include "crayfish_dataset.h"
#include "crayfish_e4q.h"
#include "crayfish_gdal.h"
#include "crayfish_mesh.h"
#include "crayfish_output.h"
#include "crayfish_renderer.h"
#include "crayfish.h"

#include <iostream>

#include <QFileInfo>



CrayfishViewer::~CrayfishViewer(){

    //std::cerr << "CF: terminating!" << std::endl;

    delete mMesh;
    mMesh = 0;

}

QImage CrayfishViewer::draw(const QSize& outputSize, double llX, double llY, double pixelSize)
{
  Renderer::Config cfg;
  cfg.output = currentDataSet()->currentOutput();
  cfg.outputSize = outputSize;
  cfg.llX = llX;
  cfg.llY = llY;
  cfg.pixelSize = pixelSize;

  cfg.mesh = mCfgMesh;
  cfg.ds = currentDataSet()->config();

  QImage image(outputSize, QImage::Format_ARGB32);

  Renderer renderer(cfg, image);
  renderer.draw();
  return image;
}

CrayfishViewer::CrayfishViewer( QString twoDMFileName )
  : mMesh(0)
  , mCurDataSetIdx(0)
{
  mMesh = Crayfish::loadMesh(twoDMFileName, &mLoadStatus);
  if (!mMesh)
    return;
}



bool CrayfishViewer::loadDataSet(QString fileName)
{
  Mesh::DataSets lst = Crayfish::loadDataSet(fileName, mMesh, &mLoadStatus);
  foreach (DataSet* ds, lst)
    mMesh->addDataSet(ds);
  return lst.count();
}


bool CrayfishViewer::isDataSetLoaded(QString fileName)
{
  for (int i = 0; i < mMesh->dataSets().count(); ++i)
  {
    if (dataSet(i)->fileName() == fileName)
      return true;
  }
  return false;
}



void CrayfishViewer::setMeshRenderingEnabled(bool enabled)
{
  mCfgMesh.mRenderMesh = enabled;
}

bool CrayfishViewer::isMeshRenderingEnabled() const
{
  return mCfgMesh.mRenderMesh;
}

void CrayfishViewer::setMeshColor(const QColor& color)
{
  mCfgMesh.mMeshColor = color;
}

QColor CrayfishViewer::meshColor() const
{
  return mCfgMesh.mMeshColor;
}

void CrayfishViewer::setCurrentDataSetIndex(int index)
{
  mCurDataSetIdx = index;
}

int CrayfishViewer::currentDataSetIndex() const
{
  return mCurDataSetIdx;
}

const DataSet* CrayfishViewer::dataSet(int dataSetIndex) const
{
  if (dataSetIndex < 0 || dataSetIndex >= mMesh->dataSets().count())
    return 0;

  return mMesh->dataSets().at(dataSetIndex);
}

const DataSet *CrayfishViewer::currentDataSet() const
{
  return dataSet(mCurDataSetIdx);
}



#if 0
QPoint CrayfishViewer::realToPixel(int nodeIndex){
  const Node& n = (mDat.mProjection ? mDat.mProjNodes[nodeIndex] : mMesh->nodes()[nodeIndex]);
  return realToPixel(n.x, n.y);
}

QPoint CrayfishViewer::realToPixel(double x, double y){
    int px = (x - mLlX) / mPixelSize;
    int py = mCanvasHeight - (y - mLlY) / mPixelSize;
    return QPoint(px, py);
}

QPointF CrayfishViewer::realToPixelF(int nodeIndex){
  const Node& n = (mDat.mProjection ? mDat.mProjNodes[nodeIndex] : mMesh->nodes()[nodeIndex]);
  return realToPixel(n.x, n.y);
}

QPointF CrayfishViewer::realToPixelF(double x, double y){
    int px = (x - mLlX) / mPixelSize;
    int py = float(mCanvasHeight) - (y - mLlY) / mPixelSize;
    return QPointF(px, py);
}



QPointF CrayfishViewer::pixelToReal(int i, int j){
    double x = mLlX + (i * mPixelSize);
    // double y = mCanvasHeight - (mLlY + (j * mPixelSize));
    // TODO: shouldn't this be without "-1" ???
    double y = mLlY + mPixelSize * (mCanvasHeight-1-j);
    return QPointF(x,y);
}
#endif



