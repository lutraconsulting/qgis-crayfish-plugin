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
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.from PyQt4.QtCore import *
*/

#include "crayfish_viewer.h"
#include <iostream>

#include <QVector2D>


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
    if(mRotatedNodes){
        delete[] mRotatedNodes;
        mRotatedNodes = 0;
    }

    for(size_t i=0; i<mDataSets.size(); i++)
        delete mDataSets.at(i);
    mDataSets.clear();
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
  , mElemCount(0)
  , mElems(0)
  , mNodeCount(0)
  , mRotatedNodeCount(0)
  , mNodes(0)
  , mRotatedNodes(0)
{

  //std::cerr << "CF: opening 2DM: " << twoDMFileName.toAscii().data() << std::endl;

    QFile file(twoDMFileName);
    if (!file.open(QIODevice::ReadOnly | QIODevice::Text)){
        mLoadedSuccessfully = false;
        mLastError = ViewerError::FileNotFound;
        //std::cerr << "CF: ERROR open" << std::endl;
        return;
    }

    uint quad4ElemCount = 0;

    // Find out how many nodes and elements are contained in the .2dm mesh file
    QTextStream in(&file);
    while (!in.atEnd()) {
        QString line = in.readLine();
        if( line.startsWith("E4Q") ){
            quad4ElemCount += 1;
            mElemCount += 1;
        }
        else if( line.startsWith("E3T") ){
            mElemCount += 1;
        }
        else if( line.startsWith("ND") ){
            mNodeCount += 1;
        }
        else if( line.startsWith("E2L") ||
                 line.startsWith("E3L") ||
                 line.startsWith("E6T") ||
                 line.startsWith("E8Q") ||
                 line.startsWith("E9Q") ||
                 line.startsWith("NS") ){
            mLastWarning = ViewerWarning::UnsupportedElement;
            mWarningsEncountered = true;
            mElemCount += 1; // We still count them as elements
        }
    }

    mRotatedNodeCount = quad4ElemCount * 4;

    // Allocate memory
    DataSet* bedDs = 0;
    Output* o = 0;
    try{
        mElems = new Element[mElemCount];
        mNodes = new Node[mNodeCount];
        mRotatedNodes = new Node[mRotatedNodeCount];
        bedDs = new DataSet;
        o = new Output;
        o->init(mNodeCount, mElemCount, false);
    } catch (const std::bad_alloc &) {
        /*
        // At present, QGIS crashes when the following lines are executed
        // therefore it's been commented for the moment
        std::cout << "In catch" << std::endl;
        // Clean up
        if(mElems){
            std::cout << "Deleting mElems" << std::endl;
            delete[] mElems;
        }
        if(mNodes){
            std::cout << "Deleting mNodes" << std::endl;
            delete[] mNodes;
        }
        if(mRotatedNodes){
            std::cout << "Deleting mRotatedNodes" << std::endl;
            delete[] mRotatedNodes;
        }
        if(o){
            std::cout << "Had o" << std::endl;
            if(o->statusFlags){
                std::cout << "Deleting flags" << std::endl;
                delete[] o->statusFlags;
            }
            if(o->values){
                delete[] o->values;
                std::cout << "Deleting values" << std::endl;
            }
            std::cout << "Deleting o" << std::endl;
            delete o;
        }
        if(bedDs){
            std::cout << "Deleting bedDs" << std::endl;
            delete bedDs;
        }
        std::cout << "Done, returning" << std::endl;
        */
        mLoadedSuccessfully = false;
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

    while (!in.atEnd()) {
        QString line = in.readLine();
        if( line.startsWith("E4Q") ){
            chunks = line.split(" ", QString::SkipEmptyParts);
            uint index = chunks[1].toInt()-1;
            if(index >= mElemCount){
                index += 1;
                continue;
            }
            mElems[index].index = index;
            mElems[index].eType = ElementType::E4Q;
            mElems[index].nodeCount = 4;
            mElems[index].isDummy = false;
            // Bear in mind that no check is done to ensure that the the p1-p4 pointers will point to a valid location
            mElems[index].p1 = &mNodes[ chunks[2].toInt()-1 ]; // -1 (crayfish Dat is 1-based indexing)
            mElems[index].p2 = &mNodes[ chunks[3].toInt()-1 ];
            mElems[index].p3 = &mNodes[ chunks[4].toInt()-1 ];
            mElems[index].p4 = &mNodes[ chunks[5].toInt()-1 ];
            //mElemCount += 1;
        }
        else if( line.startsWith("E3T") ){
            chunks = line.split(" ", QString::SkipEmptyParts);
            uint index = chunks[1].toInt()-1;
            if(index >= mElemCount){
                index += 1;
                continue;
            }
            mElems[index].index = index;
            mElems[index].eType = ElementType::E3T;
            mElems[index].nodeCount = 3;
            mElems[index].isDummy = false;
            // Bear in mind that no check is done to ensure that the the p1-p4 pointers will point to a valid location
            mElems[index].p1 = &mNodes[ chunks[2].toInt()-1 ]; // -1 (crayfish Dat is 1-based indexing)
            mElems[index].p2 = &mNodes[ chunks[3].toInt()-1 ];
            mElems[index].p3 = &mNodes[ chunks[4].toInt()-1 ];
            mElems[index].p4 = 0;
            //mElemCount += 1;
        }
        else if( line.startsWith("E2L") ||
                 line.startsWith("E3L") ||
                 line.startsWith("E6T") ||
                 line.startsWith("E8Q") ||
                 line.startsWith("E9Q") ){
            // We do not yet support these elements
            chunks = line.split(" ", QString::SkipEmptyParts);
            uint index = chunks[1].toInt()-1;
            if(index >= mElemCount){
                index += 1;
                continue;
            }
            mElems[index].index = index;
            mElems[index].isDummy = true;
        }
        else if( line.startsWith("ND") ){
            chunks = line.split(" ", QString::SkipEmptyParts);
            uint index = chunks[1].toInt()-1;
            if(index >= mNodeCount){
                index += 1;
                continue;
            }
            mNodes[index].index = index;
            mNodes[index].x = chunks[2].toDouble();
            mNodes[index].y = chunks[3].toDouble();
            bedDs->output(0)->values[index] = chunks[4].toFloat();
            //mNodeCount += 1;
        }
    }

    // Determine stats
    mXMin = mNodes[0].x;
    mXMax = mNodes[0].x;
    mYMin = mNodes[0].y;
    mYMax = mNodes[0].y;

    bedDs->updateZRange(mNodeCount);
    bedDs->setContourCustomRange(bedDs->minZValue(), bedDs->maxZValue());

    //mZMin = mNodes[0].z;
    //mZMax = mNodes[0].z;
    //mZMin = bedDs->outputs.at(0)->values[0];
    //mZMax = bedDs->outputs.at(0)->values[0];
    for(uint i=0; i<mNodeCount; i++){
        if(mNodes[i].x > mXMax)
            mXMax = mNodes[i].x;
        if(mNodes[i].x < mXMin)
            mXMin = mNodes[i].x;

        if(mNodes[i].y > mYMax)
            mYMax = mNodes[i].y;
        if(mNodes[i].y < mYMin)
            mYMin = mNodes[i].y;

        //if(bedDs->outputs.at(0)->values[i] > mZMax)
        //    mZMax = bedDs->outputs.at(0)->values[i];
        //if(bedDs->outputs.at(0)->values[i] < mZMin)
        //    mZMin = bedDs->outputs.at(0)->values[i];
    }

    /*
      In order to keep things running quickly, we pre-compute many
      element properties to speed up drawing at the expenses of memory.

        Element bounding box (xmin, xmax and friends)
      */

    for(uint i=0; i<mElemCount; i++){

        if( mElems[i].isDummy )
            continue;

        mElems[i].minX = mElems[i].p1->x;
        mElems[i].minY = mElems[i].p1->y;
        mElems[i].maxX = mElems[i].p1->x;
        mElems[i].maxY = mElems[i].p1->y;

        if(mElems[i].p2->x < mElems[i].minX)
            mElems[i].minX = mElems[i].p2->x;
        if(mElems[i].p2->x > mElems[i].maxX)
            mElems[i].maxX = mElems[i].p2->x;
        if(mElems[i].p2->y < mElems[i].minY)
            mElems[i].minY = mElems[i].p2->y;
        if(mElems[i].p2->y > mElems[i].maxY)
            mElems[i].maxY = mElems[i].p2->y;

        if(mElems[i].p3->x < mElems[i].minX)
            mElems[i].minX = mElems[i].p3->x;
        if(mElems[i].p3->x > mElems[i].maxX)
            mElems[i].maxX = mElems[i].p3->x;
        if(mElems[i].p3->y < mElems[i].minY)
            mElems[i].minY = mElems[i].p3->y;
        if(mElems[i].p3->y > mElems[i].maxY)
            mElems[i].maxY = mElems[i].p3->y;

        if(mElems[i].nodeCount > 3){
            if(mElems[i].p4->x < mElems[i].minX)
                mElems[i].minX = mElems[i].p4->x;
            if(mElems[i].p4->x > mElems[i].maxX)
                mElems[i].maxX = mElems[i].p4->x;
            if(mElems[i].p4->y < mElems[i].minY)
                mElems[i].minY = mElems[i].p4->y;
            if(mElems[i].p4->y > mElems[i].maxY)
                mElems[i].maxY = mElems[i].p4->y;
        }

        mElems[i].maxSize = std::max( (mElems[i].maxX - mElems[i].minX),
                                 (mElems[i].maxY - mElems[i].minY) );

        /*
          E4Q elements are re-ordered to ensure nodes are listed counter-clockwise from top-right
          */

        if(mElems[i].eType == ElementType::E4Q){

            Node* tmpPoints[4];
            Node* t;
            tmpPoints[0] = mElems[i].p1;
            tmpPoints[1] = mElems[i].p2;
            tmpPoints[2] = mElems[i].p3;
            tmpPoints[3] = mElems[i].p4;

            // Determine if we have rotation (based on how many nodes have x coord == minX)
            bool haveRotation = false;
            int numberOfNodesAtMinX = 0;
            for(int j=0; j<4; j++){
                if(tmpPoints[j]->x == mElems[i].minX){
                    numberOfNodesAtMinX += 1;
                }
            }
            if(numberOfNodesAtMinX < 2){
                haveRotation = true;
            }

            // Sort all by X
            bool swapped = true;
            while(swapped){
                swapped = false;
                for(int j=0; j<3; j++){
                    if(tmpPoints[j+1]->x < tmpPoints[j]->x){
                        // swap it
                        t = tmpPoints[j];
                        tmpPoints[j] = tmpPoints[j+1];
                        tmpPoints[j+1] = t;
                        swapped = true;
                    }
                }
            }

            // Now sort by Y depending if we are rotated or not
            if(haveRotation){
                if(tmpPoints[2]->y < tmpPoints[1]->y){
                    t = tmpPoints[1];
                    tmpPoints[1] = tmpPoints[2];
                    tmpPoints[2] = t;
                }
                mElems[i].p1 = tmpPoints[2];
                mElems[i].p2 = tmpPoints[0];
                mElems[i].p3 = tmpPoints[1];
                mElems[i].p4 = tmpPoints[3];
            }else{
                if(tmpPoints[1]->y < tmpPoints[0]->y){
                    t = tmpPoints[0];
                    tmpPoints[0] = tmpPoints[1];
                    tmpPoints[1] = t;
                }
                if(tmpPoints[3]->y < tmpPoints[2]->y){
                    t = tmpPoints[2];
                    tmpPoints[2] = tmpPoints[3];
                    tmpPoints[3] = t;
                }
                mElems[i].p1 = tmpPoints[3];
                mElems[i].p2 = tmpPoints[1];
                mElems[i].p3 = tmpPoints[0];
                mElems[i].p4 = tmpPoints[2];
            }

            // At this stage the nodes are ordered anti-clockwise from the top-right node (even with rotation)

            if(haveRotation){
                mElems[i].hasRotation = true;
                mElems[i].rotation = atan(   (mElems[i].p3->x - mElems[i].p2->x)
                                           / (mElems[i].p2->y - mElems[i].p3->y) );
                mElems[i].cosAlpha = cos(mElems[i].rotation);
                mElems[i].sinAlpha = sin(mElems[i].rotation);
                mElems[i].cosNegAlpha = cos(-1.0 * mElems[i].rotation);
                mElems[i].sinNegAlpha = sin(-1.0 * mElems[i].rotation);
                double cellSize = (mElems[i].p3->x - mElems[i].p2->x) / mElems[i].sinAlpha;
                mRotatedNodes[ (i*4) ].index = mElems[i].p1->index;
                mRotatedNodes[ (i*4) ].x = mElems[i].p2->x + cellSize;
                mRotatedNodes[ (i*4) ].y = mElems[i].p2->y;
                mRotatedNodes[ (i*4) ].z = mElems[i].p1->z;
                mRotatedNodes[ (i*4)+1 ].index = mElems[i].p2->index;
                mRotatedNodes[ (i*4)+1 ].x = mElems[i].p2->x;
                mRotatedNodes[ (i*4)+1 ].y = mElems[i].p2->y;
                mRotatedNodes[ (i*4)+1 ].z = mElems[i].p2->z;
                mRotatedNodes[ (i*4)+2 ].index = mElems[i].p3->index;
                mRotatedNodes[ (i*4)+2 ].x = mElems[i].p2->x;
                mRotatedNodes[ (i*4)+2 ].y = mElems[i].p2->y - cellSize;
                mRotatedNodes[ (i*4)+2 ].z = mElems[i].p3->z;
                mRotatedNodes[ (i*4)+3 ].index = mElems[i].p4->index;
                mRotatedNodes[ (i*4)+3 ].x = mElems[i].p2->x + cellSize;
                mRotatedNodes[ (i*4)+3 ].y = mElems[i].p2->y - cellSize;
                mRotatedNodes[ (i*4)+3 ].z = mElems[i].p4->z;
            }else{
                mElems[i].hasRotation = false;
                mElems[i].rotation = 0.0;
                mElems[i].cosAlpha = 0.0;
                mElems[i].sinAlpha = 0.0;
                mElems[i].cosNegAlpha = 0.0;
                mElems[i].sinNegAlpha = 0.0;
                mRotatedNodes[ (i*4) ].index = mElems[i].p1->index;
                mRotatedNodes[ (i*4) ].x = mElems[i].p1->x;
                mRotatedNodes[ (i*4) ].y = mElems[i].p1->y;
                mRotatedNodes[ (i*4) ].z = mElems[i].p1->z;
                mRotatedNodes[ (i*4)+1 ].index = mElems[i].p2->index;
                mRotatedNodes[ (i*4)+1 ].x = mElems[i].p2->x;
                mRotatedNodes[ (i*4)+1 ].y = mElems[i].p2->y;
                mRotatedNodes[ (i*4)+1 ].z = mElems[i].p2->z;
                mRotatedNodes[ (i*4)+2 ].index = mElems[i].p3->index;
                mRotatedNodes[ (i*4)+2 ].x = mElems[i].p3->x;
                mRotatedNodes[ (i*4)+2 ].y = mElems[i].p3->y;
                mRotatedNodes[ (i*4)+2 ].z = mElems[i].p3->z;
                mRotatedNodes[ (i*4)+3 ].index = mElems[i].p4->index;
                mRotatedNodes[ (i*4)+3 ].x = mElems[i].p4->x;
                mRotatedNodes[ (i*4)+3 ].y = mElems[i].p4->y;
                mRotatedNodes[ (i*4)+3 ].z = mElems[i].p4->z;
            }

        }else if(mElems[i].eType == ElementType::E3T){
            // Anything?
        }

    }

    /*if(mNodes){
        delete[] mNodes; // We don't need this any more
        mNodes = 0;
    } Yes we do!*/

}

bool CrayfishViewer::loadDataSet(QString datFileName){

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
    ds = new DataSet;
    ds->setIsTimeVarying(true);

    bool allocateErrorEncountered = false;

    while( card != 210 && !(allocateErrorEncountered) ){
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
            ds->setName(name);
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
                allocateErrorEncountered = true;
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

    // If we suffered an allocate error, clean up and return false
    if(allocateErrorEncountered){
        /*
        // At present, QGIS crashes when the following lines are executed
        // therefore it's been commented for the moment
        // Clean up
        for(int j=0; j<ds->outputs.size(); j++){
            Output* o = ds->outputs.at(j);
            if(o){
                if (o->values)
                    delete[] o->values;
                if (o->statusFlags)
                    delete[] o->statusFlags;
                if(ds->type == Vector){
                    if (o->values_x)
                        delete[] o->values_x;
                    if (o->values_y)
                        delete[] o->values_y;
                }
                delete o;
            }
        }
        ds->outputs.clear();
        delete ds;
        */
        return false;
    }

    if(ds->outputCount() > 0){

        ds->updateZRange(mNodeCount);

        ds->setContourCustomRange(ds->minZValue(), ds->maxZValue());
        ds->setVectorRenderingEnabled(ds->type() == DataSetType::Vector);

        mDataSets.push_back(ds);
        return true;
    }

    return false;

    /*DataSet* ds = new DataSet;
    bedDs->type = Bed;
    bedDs->outputCount = 1;
    bedDs->name = "Bed Elevation";
    bedDs->outputs = new Output;
    bedDs->outputs[0].time = 0.0;
    bedDs->outputs[0].statusFlags = new char[mElemCount];
    memset(bedDs->outputs[0].statusFlags, 1, mElemCount); // All cells active
    bedDs->outputs[0].values = new float[mNodeCount];
    mDataSets.push_back(bedDs);*/
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
  return QRectF(QPointF(mXMin,mYMax), QPointF(mXMax,mYMin));
}

void CrayfishViewer::setMeshRenderingEnabled(bool enabled)
{
  mRenderMesh = enabled;
}

bool CrayfishViewer::isMeshRenderingEnabled() const
{
  return mRenderMesh;
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

    if(ds->isVectorRenderingEnabled() && ds->type() == DataSetType::Vector)
        renderVectorData(ds, output);

    if (mRenderMesh)
        renderMesh();

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

                if( mElems[i].eType != elemTypeToRender )
                    continue;

                if( mElems[i].isDummy )
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
                if( mElems[i].maxSize < mPixelSize ){
                    // The element is smaller than the pixel size so there is no point rendering the element properly
                    // Just take the value of the first point associated with the element instead
                    QPoint pp;
                    if(elemTypeToRender == ElementType::E4Q){
                        pp = realToPixel( mRotatedNodes[ (i*4) ].x, mRotatedNodes[ (i*4) ].y );
                    }else{
                        pp = realToPixel( mElems[i].p1->x, mElems[i].p1->y );
                    }
                    pp.setX( std::min(pp.x(), mCanvasWidth-1) );
                    pp.setX( std::max(pp.x(), 0) );
                    pp.setY( std::min(pp.y(), mCanvasHeight-1) );
                    pp.setY( std::max(pp.y(), 0) );

                    QRgb* line = (QRgb*) mImage->scanLine(pp.y());
                    QColor tmpCol;
                    //double val = mRotatedNodes[ (i*4) ].z;
                    float val;
                    if(elemTypeToRender == ElementType::E4Q){
                        val = output->values[ mRotatedNodes[ (i*4) ].index ];
                    }else{
                        val = output->values[ mElems[i].p1->index ];
                    }
                    setColorFromVal(val, &tmpCol, ds);
                    line[pp.x()] = tmpCol.rgba();

                }else{
                    // Get the BBox of the element in pixels
                    QPoint ll = realToPixel(mElems[i].minX, mElems[i].minY);
                    QPoint ur = realToPixel(mElems[i].maxX, mElems[i].maxY);
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

        // Determine the range of vector sizes specified by the user for
        // rendering vectors with a min and max length
        float vectorLengthRange = maxShaftLength - minShaftLength;
        // Ensure that vectors at 45 degrees do not exceed the max user specified vector length
        vectorLengthRange *= 0.707106781;

        // Get a list of nodes that are within the current render extent
        std::vector<Node*> candidateNodes;

        for(uint i=0; i<mNodeCount; i++){
            if( mNodes[i].x > mLlX &&
                mNodes[i].x < mUrX &&
                mNodes[i].y > mLlY &&
                mNodes[i].y < mUrY ){

                candidateNodes.push_back( &mNodes[i] );
            }
        }


        QPainter p;
        // p.setRenderHint( QPainter::Antialiasing );
        p.begin(mImage);
        p.setBrush( Qt::SolidPattern );
        QPen pen = p.pen();
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
            Node* n = candidateNodes.at(i);
            uint nodeIndex = n->index;

            float xVal = output->values_x[nodeIndex];
            float yVal = output->values_y[nodeIndex];

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
                float valRange = ( maxVal - minVal );
                float percX = (absolute(xVal) - minVal) / valRange;
                float percY = (absolute(yVal) - minVal) / valRange;
                xDist = ( minShaftLength + (vectorLengthRange * percX) ) * mag(xVal);
                yDist = ( minShaftLength + (vectorLengthRange * percY) ) * mag(yVal);
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

            if(absolute(xDist) < 1 && absolute(yDist) < 1){
                continue;
            }

            // Determine the line coords
            QPointF lineStart = realToPixelF( n->x, n->y );
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
          pts[0] = pts[4] = realToPixel( mElems[i].p1->x, mElems[i].p1->y ); // first and last point
          pts[1] = realToPixel( mElems[i].p2->x, mElems[i].p2->y );
          pts[2] = realToPixel( mElems[i].p3->x, mElems[i].p3->y );
          pts[3] = realToPixel( mElems[i].p4->x, mElems[i].p4->y );
          p.drawPolyline(pts, 5);
        }
        else if (mElems[i].eType == ElementType::E3T)
        {
          pts[0] = pts[3] = realToPixel( mElems[i].p1->x, mElems[i].p1->y ); // first and last point
          pts[1] = realToPixel( mElems[i].p2->x, mElems[i].p2->y );
          pts[2] = realToPixel( mElems[i].p3->x, mElems[i].p3->y );
          p.drawPolyline(pts, 4);
        }
      }
}


QPoint CrayfishViewer::realToPixel(double x, double y){
    int px = (x - mLlX) / mPixelSize;
    int py = mCanvasHeight - (y - mLlY) / mPixelSize;
    return QPoint(px, py);
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
            // line[j] = qRgba(128,0,0,255);
            QColor tmpCol;
            setColorFromVal(val, &tmpCol, ds);
            line[j] = tmpCol.rgba();
        }
    }
}

void CrayfishViewer::setColorFromVal(double val, QColor* col, const DataSet* ds){
    // If the value is less than min or greater than max, set it to the appropriate end of the
    // spectrum

    float zMin = 0.0;
    float zMax = 0.0;

    if( ds->contourAutoRange() ){
        zMin = ds->minZValue();
        zMax = ds->maxZValue();
    }else{
        zMin = ds->contourCustomRangeMin();
        zMax = ds->contourCustomRangeMax();
    }

    if(val < zMin){
        col->setHsv(240, 255, 255); // Blue
    }
    else if(val > zMax){
        col->setHsv(0, 255, 255); // Red
    }
    else
    {
      // Else the value lies between so interpolate
      int h = (1.0-(val-zMin)/(zMax-zMin))*240;
      col->setHsv(h, 255, 255);
    }

    // set transparency
    if (ds->contourAlpha() != 255)
      col->setAlpha(ds->contourAlpha());
}

bool CrayfishViewer::elemOutsideView(uint i){
    // Determine if this element is visible within the view
    if( mElems[i].maxX < mLlX ||
        mElems[i].minX > mUrX ||
        mElems[i].minY > mUrY ||
        mElems[i].maxY < mLlY ){
        return true;
    }
    return false;
}

bool CrayfishViewer::interpolatValue(uint elementIndex, double x, double y, double* interpolatedVal, const Output* output){

    if(mElems[elementIndex].eType == ElementType::E4Q){

        // Sort points by by X coord and then by Y coord
        // (x1, y1, q11), (_x1, y2, q12), (x2, _y1, q21), (_x2, _y2, q22) = points

        double x1 = mRotatedNodes[(elementIndex*4)+2].x;
        double y1 = mRotatedNodes[(elementIndex*4)+2].y;
        //double q11 = mRotatedNodes[(elementIndex*4)+2].z;
        double q11 = output->values[ mRotatedNodes[(elementIndex*4)+2].index ];

        //double _x1 = mRotatedNodes[(elementIndex*4)+1].x;
        double y2 = mRotatedNodes[(elementIndex*4)+1].y;
        //double q12 = mRotatedNodes[(elementIndex*4)+1].z;
        double q12 = output->values[ mRotatedNodes[(elementIndex*4)+1].index ];

        double x2 = mRotatedNodes[(elementIndex*4)+3].x;
        //double _y1 = mRotatedNodes[(elementIndex*4)+3].y;
        //double q21 = mRotatedNodes[(elementIndex*4)+3].z;
        double q21 = output->values[ mRotatedNodes[(elementIndex*4)+3].index ];

        //double _x2 = mRotatedNodes[(elementIndex*4)+0].x;
        //double _y2 = mRotatedNodes[(elementIndex*4)+0].y;
        //double q22 = mRotatedNodes[(elementIndex*4)+0].z;
        double q22 = output->values[ mRotatedNodes[(elementIndex*4)+0].index ];

        // If the element has been rotated, rotate the x,y coord around node 2 in the oposite direction
        if(mElems[elementIndex].hasRotation){
            double x_ = x - mRotatedNodes[ (elementIndex*4)+1 ].x;
            double y_ = y - mRotatedNodes[ (elementIndex*4)+1 ].y;
            x = mRotatedNodes[ (elementIndex*4)+1 ].x + (  x_ * mElems[elementIndex].cosNegAlpha - y_ * mElems[elementIndex].sinNegAlpha );
            y = mRotatedNodes[ (elementIndex*4)+1 ].y + (  x_ * mElems[elementIndex].sinNegAlpha + y_ * mElems[elementIndex].cosNegAlpha );
        }

        // At this stage x1, x2, y1, y2 are the rotated coordinates and x and y have also been rotated
        if( !( x >= x1 && x <= x2 ) ||
            !( y >= y1 && y <= y2 ) ){
            // The point is not inside this rectangle
            return false;
        }

        *interpolatedVal = (q11 * (x2 - x) * (y2 - y) +
                            q21 * (x - x1) * (y2 - y) +
                            q12 * (x2 - x) * (y - y1) +
                            q22 * (x - x1) * (y - y1) )

                            / ( (x2 - x1) * (y2 - y1) + 0.0 );
        return true;

    }else if(mElems[elementIndex].eType == ElementType::E3T){

        /*
            So - we're interpoalting a 3-noded triangle
            The query point must be within the bounding box of this triangl but not nessisarily
            within the triangle itself.
          */

        /*
          First determine if the point of interest lies within the triangle using Barycentric techniques
          described here:  http://www.blackpawn.com/texts/pointinpoly/
          */

        QPointF pA(mElems[elementIndex].p1->x, mElems[elementIndex].p1->y);
        QPointF pB(mElems[elementIndex].p2->x, mElems[elementIndex].p2->y);
        QPointF pC(mElems[elementIndex].p3->x, mElems[elementIndex].p3->y);

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

        double z1 = output->values[ mElems[elementIndex].p1->index ];
        double z2 = output->values[ mElems[elementIndex].p2->index ];
        double z3 = output->values[ mElems[elementIndex].p3->index ];
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
        if( xCoord >= mElems[i].minX &&
            xCoord <= mElems[i].maxX &&
            yCoord >= mElems[i].minY &&
            yCoord <= mElems[i].maxY ){

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
