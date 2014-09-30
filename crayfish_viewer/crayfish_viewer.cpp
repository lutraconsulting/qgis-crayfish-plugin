/*
Crayfish - A collection of tools for TUFLOW and other hydraulic modelling packages
Copyright (C) 2012 Peter Wells for Lutra Consulting

peter dot wells at lutraconsulting dot co dot uk
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
#include "crayfish_mesh.h"
#include "crayfish_output.h"

#include <iostream>

#include <QFileInfo>
#include <QVector2D>

#include <proj_api.h>

#define DEG2RAD   (3.14159265358979323846 / 180)
#define RAD2DEG   (180 / 3.14159265358979323846)

CrayfishViewer::~CrayfishViewer(){

    //std::cerr << "CF: terminating!" << std::endl;

    if(mImage){
        delete mImage;
        mImage = 0;
    }
    if(mElems){
        delete[] mElems;
        mElems = 0;
    }
    if(mNodes){
        delete[] mNodes;
        mNodes = 0;
    }
    if (mE4Qtmp){
        delete[] mE4Qtmp;
        mE4Qtmp = 0;
    }

    for(size_t i=0; i<mDataSets.size(); i++)
        delete mDataSets.at(i);
    mDataSets.clear();

    if(mProjNodes){
        delete[] mProjNodes;
        mProjNodes = 0;
    }
    if(mProjBBoxes){
        delete[] mProjBBoxes;
        mProjBBoxes = 0;
    }
}

CrayfishViewer::CrayfishViewer( QString twoDMFileName )
  : mLoadedSuccessfully(true)
  , mWarningsEncountered(false)
  , mLastError(ViewerError::None)
  , mLastWarning(ViewerWarning::None)
  , mImage(new QImage(0, 0, QImage::Format_ARGB32))
  , mCanvasWidth(0)
  , mCanvasHeight(0)
  , mLlX(0.0), mLlY(0.0)
  , mUrX(0.0), mUrY(0.0)
  , mPixelSize(0.0)
  , mRenderMesh(0)
  , mMeshColor(Qt::black)
  , mCurDataSetIdx(0)
  , mElemCount(0)
  , mElems(0)
  , mNodeCount(0)
  , mNodes(0)
  , mE4Qtmp(0)
  , mE4Qcount(0)
  , mE3Tcount(0)
  , mProjection(false)
  , mProjNodes(0)
  , mProjBBoxes(0)
{

  //std::cerr << "CF: opening 2DM: " << twoDMFileName.toAscii().data() << std::endl;

    QFile file(twoDMFileName);
    if (!file.open(QIODevice::ReadOnly | QIODevice::Text)){
        mLoadedSuccessfully = false;
        mLastError = ViewerError::FileNotFound;
        //std::cerr << "CF: ERROR open" << std::endl;
        return;
    }

    // Find out how many nodes and elements are contained in the .2dm mesh file
    QTextStream in(&file);
    while (!in.atEnd()) {
        QString line = in.readLine();
        if( line.startsWith("E4Q") ){
            mE4Qcount += 1;
            mElemCount += 1;
        }
        else if( line.startsWith("E3T") ){
            mE3Tcount += 1;
            mElemCount += 1;
        }
        else if( line.startsWith("ND") ){
            mNodeCount += 1;
        }
        else if( line.startsWith("E2L") ||
                 line.startsWith("E3L") ||
                 line.startsWith("E6T") ||
                 line.startsWith("E8Q") ||
                 line.startsWith("E9Q")){
            mLastWarning = ViewerWarning::UnsupportedElement;
            mWarningsEncountered = true;
            mElemCount += 1; // We still count them as elements
        }
    }

    // Allocate memory
    DataSet* bedDs = 0;
    Output* o = 0;
    try{
        mElems = new Element[mElemCount];
        mNodes = new Node[mNodeCount];
        mE4Qtmp = new E4Qtmp[mE4Qcount];
        bedDs = new DataSet(twoDMFileName);
        o = new Output;
        o->init(mNodeCount, mElemCount, false);
    } catch (const std::bad_alloc &) {
        mLoadedSuccessfully = false;
        mLastError = ViewerError::NotEnoughMemory;
        //std::cerr << "CF: ERROR alloc" << std::endl;
        return;
    }

    // Create a dataset for the bed elevation
    bedDs->setType(DataSetType::Bed);
    bedDs->setName("Bed Elevation");
    bedDs->setIsTimeVarying(false);

    o->time = 0.0;
    memset(o->statusFlags, 1, mElemCount); // All cells active
    bedDs->addOutput(o);
    mDataSets.push_back(bedDs);

    in.seek(0);
    QStringList chunks = QStringList();

    uint elemIndex = 0;
    QMap<int, int> elemIDtoIndex;

    while (!in.atEnd()) {
        QString line = in.readLine();
        if( line.startsWith("E4Q") ){
            chunks = line.split(" ", QString::SkipEmptyParts);
            Q_ASSERT(elemIndex < mElemCount);

            uint elemID = chunks[1].toInt();
            Q_ASSERT(!elemIDtoIndex.contains(elemID));
            elemIDtoIndex[elemID] = elemIndex;

            Element& elem = mElems[elemIndex];
            elem.index = elemIndex;
            elem.eType = ElementType::E4Q;
            elem.nodeCount = 4;
            elem.isDummy = false;
            // Bear in mind that no check is done to ensure that the the p1-p4 pointers will point to a valid location
            for (int i = 0; i < 4; ++i)
              elem.p[i] = chunks[i+2].toInt()-1; // -1 (crayfish Dat is 1-based indexing)

            elemIndex++;
        }
        else if( line.startsWith("E3T") ){
            chunks = line.split(" ", QString::SkipEmptyParts);
            Q_ASSERT(elemIndex < mElemCount);

            uint elemID = chunks[1].toInt();
            Q_ASSERT(!elemIDtoIndex.contains(elemID));
            elemIDtoIndex[elemID] = elemIndex;

            Element& elem = mElems[elemIndex];
            elem.index = elemIndex;
            elem.eType = ElementType::E3T;
            elem.nodeCount = 3;
            elem.isDummy = false;
            // Bear in mind that no check is done to ensure that the the p1-p4 pointers will point to a valid location
            for (int i = 0; i < 3; ++i)
              elem.p[i] = chunks[i+2].toInt()-1; // -1 (crayfish Dat is 1-based indexing)
            elem.p[3] = -1; // only three points

            elemIndex++;
        }
        else if( line.startsWith("E2L") ||
                 line.startsWith("E3L") ||
                 line.startsWith("E6T") ||
                 line.startsWith("E8Q") ||
                 line.startsWith("E9Q")){
            // We do not yet support these elements
            chunks = line.split(" ", QString::SkipEmptyParts);
            Q_ASSERT(elemIndex < mElemCount);

            mElems[elemIndex].index = elemIndex;
            mElems[elemIndex].isDummy = true;

            elemIndex++;
        }
        else if( line.startsWith("ND") ){
            chunks = line.split(" ", QString::SkipEmptyParts);
            uint index = chunks[1].toInt()-1;
            Q_ASSERT(index < mNodeCount);

            //mNodes[index].index = index;
            mNodes[index].x = chunks[2].toDouble();
            mNodes[index].y = chunks[3].toDouble();
            bedDs->output(0)->values[index] = chunks[4].toFloat();
        }
    }

    // Determine stats
    computeMeshExtent(); // mXMin, mXMax, mYMin, mYMax

    bedDs->updateZRange(mNodeCount);

    int e4qIndex = 0;

    /*
      In order to keep things running quickly, we pre-compute many
      element properties to speed up drawing at the expenses of memory.

        Element bounding box (xmin, xmax and friends)
      */

    for(uint i=0; i<mElemCount; i++){

        if( mElems[i].isDummy )
            continue;

        Element& elem = mElems[i];

        updateBBox(elem.bbox, elem, mNodes);

        /*
          E4Q elements are re-ordered to ensure nodes are listed counter-clockwise from top-right
          */

        if(elem.eType == ElementType::E4Q){

            // cache some temporary data for faster rendering

            elem.indexTmp = e4qIndex;
            E4Qtmp& e4q = mE4Qtmp[e4qIndex];

            E4Q_computeMapping(elem, e4q, mNodes);

            e4qIndex++;

        }else if(elem.eType == ElementType::E3T){
            // Anything?

            // check validity of the triangle
            // for now just checking if we have three distinct nodes
          const Node& n1 = mNodes[elem.p[0]];
          const Node& n2 = mNodes[elem.p[1]];
          const Node& n3 = mNodes[elem.p[2]];
          if (n1 == n2 || n1 == n3 || n2 == n3)
          {
            elem.isDummy = true; // mark element as unusable

            mLastWarning = ViewerWarning::InvalidElements;
            mWarningsEncountered = true;
          }
        }

    }

}


void CrayfishViewer::computeMeshExtent()
{
    mXMin = mNodes[0].x;
    mXMax = mNodes[0].x;
    mYMin = mNodes[0].y;
    mYMax = mNodes[0].y;

    for(uint i=0; i<mNodeCount; i++){
        if(mNodes[i].x > mXMax)
            mXMax = mNodes[i].x;
        if(mNodes[i].x < mXMin)
            mXMin = mNodes[i].x;

        if(mNodes[i].y > mYMax)
            mYMax = mNodes[i].y;
        if(mNodes[i].y < mYMin)
            mYMin = mNodes[i].y;
    }
}


bool CrayfishViewer::loadDataSet(QString fileName)
{
  if (loadBinaryDataSet(fileName))
    return true;

  return loadAsciiDataSet(fileName);
}

bool CrayfishViewer::loadBinaryDataSet(QString datFileName)
{

    QFile file(datFileName);
    if (!file.open(QIODevice::ReadOnly)){
        // Couldn't open the file
        return false;
    }

    int card;
    int version;
    int objecttype;
    int sflt;
    int sflg;
    int vectype;
    int objid;
    uint numdata;
    uint numcells;
    char name[40];
    char istat;
    float time;

    QDataStream in(&file);

    card = 0;
    if( in.readRawData( (char*)&version, 4) != 4 ){
        return false;
    }
    if( version != 3000 ) // Version should be 3000
        return false;

    DataSet* ds = 0;
    ds = new DataSet(datFileName);
    ds->setIsTimeVarying(true);

    while( card != 210 ){
        if( in.readRawData( (char*)&card, 4) != 4 ){
            // We've reached the end of the file and there was no ends card
            break;
        }
        switch(card){

        case 100:

            // Object type
            if( in.readRawData( (char*)&objecttype, 4) != 4 ){
                delete ds;
                return false;
            }
            if(objecttype != 3){
                delete ds;
                return false;
            }
            break;

        case 110:

            // Float size
            if( in.readRawData( (char*)&sflt, 4) != 4 ){
                delete ds;
                return false;
            }
            if(sflt != 4){
                delete ds;
                return false;
            }
            break;

        case 120:

            // Flag size
            if( in.readRawData( (char*)&sflg, 4) != 4 ){
                delete ds;
                return false;
            }
            if(sflg != 1){
                delete ds;
                return false;
            }
            break;

        case 130:

            ds->setType(DataSetType::Scalar);
            break;

        case 140:

            ds->setType(DataSetType::Vector);
            break;

        case 150:

            // Vector type
            if( in.readRawData( (char*)&vectype, 4) != 4 ){
                delete ds;
                return false;
            }
            if(vectype != 0){
                delete ds;
                return false;
            }
            break;

        case 160:

            // Object id
            if( in.readRawData( (char*)&objid, 4) != 4 ){
                delete ds;
                return false;
            }
            break;

        case 170:

            // Num data
            if( in.readRawData( (char*)&numdata, 4) != 4 ){
                delete ds;
                return false;
            }
            if(numdata != mNodeCount){
                delete ds;
                return false;
            }
            break;

        case 180:

            // Num data
            if( in.readRawData( (char*)&numcells, 4) != 4 ){
                delete ds;
                return false;
            }
            if(numcells != mElemCount){
                delete ds;
                return false;
            }
            break;

        case 190:

            // Name
            if( in.readRawData( (char*)&name, 40) != 40 ){
                delete ds;
                return false;
            }
            if(name[39] != 0)
                name[39] = 0;
            ds->setName(QString(name).trimmed());
            break;

        case 200:

            // Time step!
            if( in.readRawData( (char*)&istat, 1) != 1 ){
                return false;
            }
            if( in.readRawData( (char*)&time, 4) != 4 ){
                return false;
            }

            Output* o = 0;
            try{
                o = new Output;
                o->init(mNodeCount, mElemCount, ds->type() == DataSetType::Vector);
            } catch (const std::bad_alloc &) {
                delete o;
                delete ds;
                return false;
            }

            o->time = time;


            if(istat){
                for(uint i=0; i<mElemCount; i++){
                    // Read status flags
                    if( in.readRawData( (char*)&o->statusFlags[i], 1) != 1 ){
                        delete o;
                        delete ds;
                        return false;
                    }
                }
            }

            for(uint i=0; i<mNodeCount; i++){
                // Read values flags
              if(ds->type() == DataSetType::Vector){
                    if( in.readRawData( (char*)&o->values_x[i], 4) != 4 ){
                        delete o;
                        delete ds;
                        return false;
                    }
                    if( in.readRawData( (char*)&o->values_y[i], 4) != 4 ){
                        delete o;
                        delete ds;
                        return false;
                    }
                    o->values[i] = sqrt( pow(o->values_x[i],2) + pow(o->values_y[i],2) ); // Determine the magnitude
                }else{
                    if( in.readRawData( (char*)&o->values[i], 4) != 4 ){
                        delete o;
                        delete ds;
                        return false;
                    }
                }
            }

            ds->addOutput(o);

            break;

        }
    }

    if(ds->outputCount() > 0){

        ds->updateZRange(mNodeCount);

        ds->setVectorRenderingEnabled(ds->type() == DataSetType::Vector);

        mDataSets.push_back(ds);
        return true;
    }

    delete ds;
    return false;
}

bool CrayfishViewer::loadAsciiDataSet(QString fileName)
{
  QFile file(fileName);
  if (!file.open(QIODevice::ReadOnly)){
      // Couldn't open the file
      return false;
  }

  QTextStream stream(&file);
  QString firstLine = stream.readLine();

  // http://www.xmswiki.com/xms/SMS:ASCII_Dataset_Files_*.dat
  // Apart from the format specified above, there is an older supported format used in BASEMENT (and SMS?)
  // which is simpler (has only one dataset in one file, no status flags etc)

  bool oldFormat;
  bool isVector = false;
  DataSet* ds = 0;

  if (firstLine == "DATASET")
    oldFormat = false;
  else if (firstLine == "SCALAR" || firstLine == "VECTOR")
  {
    oldFormat = true;
    isVector = (firstLine == "VECTOR");

    ds = new DataSet(fileName);
    ds->setIsTimeVarying(true);
    ds->setType(isVector ? DataSetType::Vector : DataSetType::Scalar);
    ds->setVectorRenderingEnabled(isVector);
    ds->setName(QFileInfo(fileName).baseName());
  }
  else
    return false; // unknown type

  QRegExp reSpaces("\\s+");

  while (!stream.atEnd())
  {
    QString line = stream.readLine();
    QStringList items = line.split(reSpaces, QString::SkipEmptyParts);
    if (items.count() < 1)
      continue; // empty line?? let's skip it

    QString cardType = items[0];
    if (cardType == "ND" && items.count() >= 2)
    {
      uint fileNodeCount = items[1].toUInt();
      if (mNodeCount != fileNodeCount)
        return false;
    }
    else if (!oldFormat && cardType == "NC" && items.count() >= 2)
    {
      uint fileElemCount = items[1].toUInt();
      if (mElemCount != fileElemCount)
        return false;
    }
    else if (!oldFormat && (cardType == "BEGSCL" || cardType == "BEGVEC"))
    {
      if (ds)
      {
        qDebug("Crayfish: New dataset while previous one is still active!");
        return false;
      }
      isVector = cardType == "BEGVEC";
      ds = new DataSet(fileName);
      ds->setIsTimeVarying(true);
      ds->setVectorRenderingEnabled(isVector);
      ds->setType(isVector ? DataSetType::Vector : DataSetType::Scalar);
    }
    else if (!oldFormat && cardType == "ENDDS")
    {
      if (!ds)
      {
        qDebug("Crayfish: ENDDS card for no active dataset!");
        return false;
      }
      ds->updateZRange(mNodeCount);
      mDataSets.push_back(ds);
      ds = 0;
    }
    else if (!oldFormat && cardType == "NAME" && items.count() >= 2)
    {
      if (!ds)
      {
        qDebug("Crayfish: NAME card for no active dataset!");
        return false;
      }

      int quoteIdx1 = line.indexOf('\"');
      int quoteIdx2 = line.indexOf('\"', quoteIdx1+1);
      if (quoteIdx1 > 0 && quoteIdx2 > 0)
        ds->setName(line.mid(quoteIdx1+1, quoteIdx2-quoteIdx1-1));
    }
    else if (oldFormat && (cardType == "SCALAR" || cardType == "VECTOR"))
    {
      // just ignore - we know the type from earlier...
    }
    else if (cardType == "TS" && items.count() >= (oldFormat ? 2 : 3))
    {
      bool hasStatus = (oldFormat ? false : items[1].toInt());
      float t = items[oldFormat ? 1 : 2].toFloat();

      Output* o = new Output;
      o->init(mNodeCount, mElemCount, isVector);
      o->time = t / 3600.;

      if (hasStatus)
      {
        // only for new format
        for (uint i = 0; i < mElemCount; ++i)
        {
          o->statusFlags[i] = stream.readLine().toInt();
        }
      }
      else
        memset(o->statusFlags, 1, mElemCount); // there is no status flag -> everything is active

      for (uint i = 0; i < mNodeCount; ++i)
      {
        QStringList tsItems = stream.readLine().split(reSpaces, QString::SkipEmptyParts);
        if (isVector)
        {
          if (tsItems.count() >= 2) // BASEMENT files with vectors have 3 columns
          {
            o->values_x[i] = tsItems[0].toFloat();
            o->values_y[i] = tsItems[1].toFloat();
          }
          else
          {
            qDebug("Crayfish: invalid timestep line");
            o->values_x[i] = o->values_y[i] = 0;
          }
          o->values[i] = sqrt( pow(o->values_x[i],2) + pow(o->values_y[i],2) ); // Determine the magnitude
        }
        else
        {
          if (tsItems.count() >= 1)
            o->values[i] = tsItems[0].toFloat();
          else
          {
            qDebug("Crayfish: invalid timestep line");
            o->values[i] = 0;
          }
        }
      }

      ds->addOutput(o);
    }
    else
    {
      qDebug("Crafish: Unknown card: %s", items.join(" ").toAscii().data());
    }
  }

  if (oldFormat)
  {
    if (ds->outputCount() > 0)
    {
      ds->updateZRange(mNodeCount);
      mDataSets.push_back(ds);
      return true;
    }
    else
    {
      delete ds;
      return false;
    }
  }

  return true;
}


bool CrayfishViewer::isDataSetLoaded(QString fileName)
{
  for (size_t i = 0; i < mDataSets.size(); ++i)
  {
    if (dataSet(i)->fileName() == fileName)
      return true;
  }
  return false;
}



void CrayfishViewer::setCanvasSize(const QSize& size)
{
  if(size.width() != mCanvasWidth || size.height() != mCanvasHeight){
      // The size of the canvas has changed so we need to re-allocate out QImage
      delete mImage;
      mImage = new QImage(size, QImage::Format_ARGB32);
  }
  mCanvasWidth = size.width();
  mCanvasHeight = size.height();
}

QSize CrayfishViewer::canvasSize() const
{
  return QSize(mCanvasWidth, mCanvasHeight);
}

void CrayfishViewer::setExtent(double llX, double llY, double pixelSize)
{
  mLlX = llX;
  mLlY = llY;
  mPixelSize = pixelSize;

  mUrX = mLlX + (mCanvasWidth*mPixelSize);
  mUrY = mLlY + (mCanvasHeight*mPixelSize);
}

QRectF CrayfishViewer::extent() const
{
  return QRectF(QPointF(mLlX,mUrY), QPointF(mUrX,mLlY));
}

void CrayfishViewer::setMeshRenderingEnabled(bool enabled)
{
  mRenderMesh = enabled;
}

bool CrayfishViewer::isMeshRenderingEnabled() const
{
  return mRenderMesh;
}

void CrayfishViewer::setMeshColor(const QColor& color)
{
  mMeshColor = color;
}

QColor CrayfishViewer::meshColor() const
{
  return mMeshColor;
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
  if (dataSetIndex < 0 || dataSetIndex >= (int)mDataSets.size())
    return 0;

  return mDataSets.at(dataSetIndex);
}

const DataSet *CrayfishViewer::currentDataSet() const
{
  return dataSet(mCurDataSetIdx);
}

void CrayfishViewer::setNoProjection()
{
  if (!mProjection)
    return; // nothing to do

  delete [] mProjNodes;
  mProjNodes = 0;
  delete [] mProjBBoxes;
  mProjBBoxes = 0;

  for (uint i = 0; i < mElemCount; ++i)
  {
    if (mElems[i].eType == ElementType::E4Q)
      E4Q_computeMapping(mElems[i], mE4Qtmp[mElems[i].indexTmp], mNodes);
  }

  mProjection = false;
  mSrcProj4.clear();
  mDestProj4.clear();
}

bool CrayfishViewer::setProjection(const QString& srcProj4, const QString& destProj4)
{
  Q_ASSERT(!srcProj4.isEmpty() && !destProj4.isEmpty());

  if (mSrcProj4 == srcProj4 && mDestProj4 == destProj4)
    return true; // nothing has changed - so do nothing!

  mProjection = true;
  mSrcProj4 = srcProj4;
  mDestProj4 = destProj4;

  projPJ projSrc = pj_init_plus(srcProj4.toAscii().data());
  if (!projSrc)
  {
    qDebug("Crayfish: source proj4 string is not valid! (%s)", pj_strerrno(pj_errno));
    setNoProjection();
    return false;
  }

  projPJ projDst = pj_init_plus(destProj4.toAscii().data());
  if (!projDst)
  {
    pj_free(projSrc);
    qDebug("Crayfish: source proj4 string is not valid! (%s)", pj_strerrno(pj_errno));
    setNoProjection();
    return false;
  }

  if (mProjNodes == 0)
    mProjNodes = new Node[mNodeCount];

  memcpy(mProjNodes, mNodes, sizeof(Node)*mNodeCount);

  if (pj_is_latlong(projSrc))
  {
    // convert source from degrees to radians
    for (uint i = 0; i < mNodeCount; ++i)
    {
      mProjNodes[i].x *= DEG2RAD;
      mProjNodes[i].y *= DEG2RAD;
    }
  }

  int res = pj_transform(projSrc, projDst, mNodeCount, 2, &mProjNodes->x, &mProjNodes->y, NULL);

  if (res != 0)
  {
    qDebug("Crayfish: reprojection failed (%s)", pj_strerrno(res));
    setNoProjection();
    return false;
  }

  if (pj_is_latlong(projDst))
  {
    // convert source from degrees to radians
    for (uint i = 0; i < mNodeCount; ++i)
    {
      mProjNodes[i].x *= RAD2DEG;
      mProjNodes[i].y *= RAD2DEG;
    }
  }

  pj_free(projSrc);
  pj_free(projDst);

  if (mProjBBoxes == 0)
    mProjBBoxes = new BBox[mElemCount];

  for (uint i = 0; i < mElemCount; ++i)
  {
    updateBBox(mProjBBoxes[i], mElems[i], mProjNodes);

    if (mElems[i].eType == ElementType::E4Q)
      E4Q_computeMapping(mElems[i], mE4Qtmp[mElems[i].indexTmp], mProjNodes); // update interpolation coefficients
  }

  return true;
}

bool CrayfishViewer::hasProjection() const
{
  return mProjection;
}

void CrayfishViewer::updateBBox(BBox& bbox, const Element& elem, Node* nodes)
{
  const Node& node0 = nodes[elem.p[0]];

  bbox.minX = node0.x;
  bbox.minY = node0.y;
  bbox.maxX = node0.x;
  bbox.maxY = node0.y;

  for (int j = 1; j < elem.nodeCount; ++j)
  {
    const Node& n = nodes[elem.p[j]];
    if (n.x < bbox.minX) bbox.minX = n.x;
    if (n.x > bbox.maxX) bbox.maxX = n.x;
    if (n.y < bbox.minY) bbox.minY = n.y;
    if (n.y > bbox.maxY) bbox.maxY = n.y;
  }

  bbox.maxSize = std::max( (bbox.maxX - bbox.minX),
                           (bbox.maxY - bbox.minY) );

}


QImage* CrayfishViewer::draw(){

    // Some sanity checks

    const DataSet* ds = currentDataSet();
    if (!ds)
      return 0;

    const Output* output = ds->currentOutput();
    if ( !output )
        return 0;

    mImage->fill( qRgba(255,255,255,0) );

    if(ds->isContourRenderingEnabled())
        renderContourData(ds, output);

    if (mRenderMesh)
        renderMesh();

    if(ds->isVectorRenderingEnabled() && ds->type() == DataSetType::Vector)
        renderVectorData(ds, output);

    return mImage;
}


void CrayfishViewer::renderContourData(const DataSet* ds, const Output* output)
{
        // Render E4Q before E3T
        QVector<ElementType::Enum> typesToRender;
        typesToRender.append(ElementType::E4Q);
        typesToRender.append(ElementType::E3T);
        QVectorIterator<ElementType::Enum> it(typesToRender);
        while(it.hasNext()){

            ElementType::Enum elemTypeToRender = it.next();

            for(uint i=0; i<mElemCount; i++){

                const Element& elem = mElems[i];
                if( elem.eType != elemTypeToRender )
                    continue;

                if( elem.isDummy )
                    continue;

                // For each element

                // If the element's activity flag is off, ignore it
                if( ! output->statusFlags[i] ){
                    continue;
                }

                // If the element is outside the view of the canvas, skip it
                if( elemOutsideView(i) ){
                    continue;
                }

                //
                const BBox& bbox = (mProjection ? mProjBBoxes[i] : elem.bbox);
                if( bbox.maxSize < mPixelSize ){
                    // The element is smaller than the pixel size so there is no point rendering the element properly
                    // Just take the value of the first point associated with the element instead
                    QPoint pp = realToPixel( elem.p[0] );
                    pp.setX( std::min(pp.x(), mCanvasWidth-1) );
                    pp.setX( std::max(pp.x(), 0) );
                    pp.setY( std::min(pp.y(), mCanvasHeight-1) );
                    pp.setY( std::max(pp.y(), 0) );

                    QRgb* line = (QRgb*) mImage->scanLine(pp.y());
                    float val = output->values[ elem.p[0] ];
                    line[pp.x()] = ds->contourColorMap().value(val);

                }else{
                    // Get the BBox of the element in pixels
                    QPoint ll = realToPixel(bbox.minX, bbox.minY);
                    QPoint ur = realToPixel(bbox.maxX, bbox.maxY);
                    int topLim = std::max( ur.y(), 0 );
                    int bottomLim = std::min( ll.y(), mCanvasHeight-1 );
                    int leftLim = std::max( ll.x(), 0 );
                    int rightLim = std::min( ur.x(), mCanvasWidth-1 );

                    for(int j=topLim; j<=bottomLim; j++){ // FIXME - are we missing the last line?  Should this be j<=bottomLim ?
                        paintRow(i, j, leftLim, rightLim, ds, output);
                    }
                }
            } // for all elements

        } // for element types
}


void CrayfishViewer::renderVectorData(
    const DataSet* ds,
    const Output* output)
{
    VectorLengthMethod shaftLengthCalculationMethod = ds->vectorShaftLengthMethod();
    float minShaftLength   = ds->vectorShaftLengthMin();
    float maxShaftLength   = ds->vectorShaftLengthMax();
    float scaleFactor      = ds->vectorShaftLengthScaleFactor();
    float fixedShaftLength = ds->vectorShaftLengthFixed();
    int lineWidth          = ds->vectorPenWidth();
    float vectorHeadWidthPerc  = ds->vectorHeadWidth();
    float vectorHeadLengthPerc = ds->vectorHeadLength();

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
        float minVal = ds->minZValue();
        float maxVal = ds->maxZValue();

        // Get a list of nodes that are within the current render extent
        std::vector<int> candidateNodes;

        for(uint i=0; i<mNodeCount; i++){
            if (nodeInsideView(i))
                candidateNodes.push_back( i );
        }


        QPainter p;
        p.begin(mImage);
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

        for(uint i=0; i<candidateNodes.size(); i++){
            // Get the value
            uint nodeIndex = candidateNodes.at(i);

            float xVal = output->values_x[nodeIndex];
            float yVal = output->values_y[nodeIndex];
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

            if(shaftLengthCalculationMethod == MinMax){
                double k = (V - minVal) / (maxVal - minVal);
                double L = minShaftLength + k * (maxShaftLength - minShaftLength);
                xDist = cosAlpha * L;
                yDist = sinAlpha * L;
            }else if(shaftLengthCalculationMethod == Scaled){
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
                lineStart.x() > mCanvasWidth ||
                lineStart.y() < 0 ||
                lineStart.y() > mCanvasHeight ||
                lineEnd.x() < 0 ||
                lineEnd.x() > mCanvasWidth ||
                lineEnd.y() < 0 ||
                lineEnd.y() > mCanvasHeight ){

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


void CrayfishViewer::renderMesh()
{
      // render mesh as a wireframe

      QPainter p(mImage);
      p.setPen(mMeshColor);
      QPoint pts[5];
      for (uint i=0; i < mElemCount; ++i)
      {
        if( mElems[i].isDummy )
            continue;

        // If the element is outside the view of the canvas, skip it
        if( elemOutsideView(i) )
            continue;

        if (mElems[i].eType == ElementType::E4Q)
        {
          pts[0] = pts[4] = realToPixel( mElems[i].p[0] ); // first and last point
          pts[1] = realToPixel( mElems[i].p[1] );
          pts[2] = realToPixel( mElems[i].p[2] );
          pts[3] = realToPixel( mElems[i].p[3] );
          p.drawPolyline(pts, 5);
        }
        else if (mElems[i].eType == ElementType::E3T)
        {
          pts[0] = pts[3] = realToPixel( mElems[i].p[0] ); // first and last point
          pts[1] = realToPixel( mElems[i].p[1] );
          pts[2] = realToPixel( mElems[i].p[2] );
          p.drawPolyline(pts, 4);
        }
      }
}

QPoint CrayfishViewer::realToPixel(int nodeIndex){
  const Node& n = (mProjection ? mProjNodes[nodeIndex] : mNodes[nodeIndex]);
  return realToPixel(n.x, n.y);
}

QPoint CrayfishViewer::realToPixel(double x, double y){
    int px = (x - mLlX) / mPixelSize;
    int py = mCanvasHeight - (y - mLlY) / mPixelSize;
    return QPoint(px, py);
}

QPointF CrayfishViewer::realToPixelF(int nodeIndex){
  const Node& n = (mProjection ? mProjNodes[nodeIndex] : mNodes[nodeIndex]);
  return realToPixel(n.x, n.y);
}

QPointF CrayfishViewer::realToPixelF(double x, double y){
    int px = (x - mLlX) / mPixelSize;
    int py = float(mCanvasHeight) - (y - mLlY) / mPixelSize;
    return QPointF(px, py);
}

void CrayfishViewer::paintRow(uint elementIdx, int rowIdx, int leftLim, int rightLim, const DataSet* ds, const Output* output){
    /*
      Grab the pointer to the row if we do not have it already
      */
    QRgb* line = (QRgb*) mImage->scanLine(rowIdx);

    for(int j=leftLim; j<=rightLim; j++){
        // Determine real-world coords
        // Interpolate a value from the element
        // Set the value in the QImage
        QPointF p = pixelToReal(j, rowIdx);

        double val;
        if( interpolatValue(elementIdx, p.x(), p.y(), &val, output) ){
            // The supplied point was inside the element
            line[j] = ds->contourColorMap().value(val);
        }
    }
}


bool CrayfishViewer::nodeInsideView(uint nodeIndex)
{
  const Node& n = (mProjection ? mProjNodes[nodeIndex] : mNodes[nodeIndex]);
  return n.x > mLlX && n.x < mUrX && n.y > mLlY && n.y < mUrY;
}

bool CrayfishViewer::elemOutsideView(uint i){
  const BBox& bbox = (mProjection ? mProjBBoxes[i] : mElems[i].bbox);
  // Determine if this element is visible within the view
  return bbox.maxX < mLlX || bbox.minX > mUrX || bbox.minY > mUrY || bbox.maxY < mLlY;
}

bool CrayfishViewer::interpolatValue(uint elementIndex, double x, double y, double* interpolatedVal, const Output* output){

    Element& elem = mElems[elementIndex];

    if(elem.eType == ElementType::E4Q){

        E4Qtmp& e4q = mE4Qtmp[elem.indexTmp];

        double Lx, Ly;
        if (!E4Q_mapPhysicalToLogical(e4q, x, y, Lx, Ly))
          return false;

        if (Lx < 0 || Ly < 0 || Lx > 1 || Ly > 1)
          return false;

        double q11 = output->values[ elem.p[2] ];
        double q12 = output->values[ elem.p[1] ];
        double q21 = output->values[ elem.p[3] ];
        double q22 = output->values[ elem.p[0] ];

        *interpolatedVal = q11*Lx*Ly + q21*(1-Lx)*Ly + q12*Lx*(1-Ly) + q22*(1-Lx)*(1-Ly);

        return true;

    }else if(elem.eType == ElementType::E3T){

        /*
            So - we're interpoalting a 3-noded triangle
            The query point must be within the bounding box of this triangl but not nessisarily
            within the triangle itself.
          */

        /*
          First determine if the point of interest lies within the triangle using Barycentric techniques
          described here:  http://www.blackpawn.com/texts/pointinpoly/
          */

        Node* nodes = mProjection ? mProjNodes : mNodes;
        QPointF pA(nodes[elem.p[0]].toPointF());
        QPointF pB(nodes[elem.p[1]].toPointF());
        QPointF pC(nodes[elem.p[2]].toPointF());

        if (pA == pB || pA == pC || pB == pC)
          return false; // this is not a valid triangle!

        QPointF pP(x, y);

        // Compute vectors
        QVector2D v0( pC - pA );
        QVector2D v1( pB - pA );
        QVector2D v2( pP - pA );

        // Compute dot products
        double dot00 = QVector2D::dotProduct(v0, v0);
        double dot01 = QVector2D::dotProduct(v0, v1);
        double dot02 = QVector2D::dotProduct(v0, v2);
        double dot11 = QVector2D::dotProduct(v1, v1);
        double dot12 = QVector2D::dotProduct(v1, v2);

        // Compute barycentric coordinates
        double invDenom = 1.0 / (dot00 * dot11 - dot01 * dot01);
        double lam1 = (dot11 * dot02 - dot01 * dot12) * invDenom;
        double lam2 = (dot00 * dot12 - dot01 * dot02) * invDenom;
        double lam3 = 1.0 - lam1 - lam2;

        // Return if POI is outside triangle
        if( (lam1 < 0) || (lam2 < 0) || (lam3 < 0) ){
            return false;
        }

        // Now interpolate

        double z1 = output->values[ elem.p[0] ];
        double z2 = output->values[ elem.p[1] ];
        double z3 = output->values[ elem.p[2] ];
        *interpolatedVal = lam1 * z3 + lam2 * z2 + lam3 * z1;
        return true;

    }else{
      Q_ASSERT(0 && "unknown element type");
      return false;
    }
}

QPointF CrayfishViewer::pixelToReal(int i, int j){
    double x = mLlX + (i * mPixelSize);
    // double y = mCanvasHeight - (mLlY + (j * mPixelSize));
    double y = mLlY + mPixelSize * (mCanvasHeight-1-j);
    return QPointF(x,y);
}

double CrayfishViewer::valueAtCoord(const Output* output, double xCoord, double yCoord){

    /*
      We want to find the value at the given coordinate
      */

    /*
        Loop through all the elements in the dataset and make a list of those
      */

    std::vector<uint> candidateElementIds;

    for(uint i=0; i<mElemCount; i++){

        const BBox& bbox = (mProjection ? mProjBBoxes[i] : mElems[i].bbox);
        if( bbox.isPointInside(xCoord, yCoord) ){

            candidateElementIds.push_back(i);
        }
    }

    if( candidateElementIds.size() == 0 ){
        return -9999.0;
    }

    double value;

    for(uint i=0; i<candidateElementIds.size(); i++){

        uint elemIndex = candidateElementIds.at(i);
        if( ! output->statusFlags[elemIndex] ){
            continue;
        }
        if( interpolatValue(elemIndex, xCoord, yCoord, &value, output) ){
            // We successfully got a value, return it and leave
            return value;
        }
    }

    return -9999.0;
}
