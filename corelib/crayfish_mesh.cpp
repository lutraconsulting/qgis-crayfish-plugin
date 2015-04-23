/*
Crayfish - A collection of tools for TUFLOW and other hydraulic modelling packages
Copyright (C) 2015 Lutra Consulting

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

#include "crayfish_mesh.h"

#include "crayfish_e4q.h"
#include "crayfish_dataset.h"
#include "crayfish_output.h"

#include <QVector2D>

#include <proj_api.h>

#define DEG2RAD   (3.14159265358979323846 / 180)
#define RAD2DEG   (180 / 3.14159265358979323846)



BasicMesh::BasicMesh(const Mesh::Nodes& nodes, const Mesh::Elements& elements)
  : mNodes(nodes)
  , mElems(elements)
{
}

BasicMesh::~BasicMesh()
{
}

void Mesh::addDataSet(DataSet* ds)
{
  mDataSets.append(ds);
  ds->setMesh(this);
}

int BasicMesh::elementCountForType(Element::Type type)
{
  int cnt = 0;
  for (int i = 0; i < mElems.count(); ++i)
  {
    if (mElems[i].eType == type)
      ++cnt;
  }
  return cnt;
}



Mesh::Mesh(const BasicMesh::Nodes& nodes, const BasicMesh::Elements& elements)
  : BasicMesh(nodes, elements)
  , mE4Qtmp(0)
  , mE4QtmpIndex(0)
  , mBBoxes(0)
  , mProjection(false)
  , mProjNodes(0)
  , mProjBBoxes(0)
{
  mExtent = computeMeshExtent(false);
  computeTempRendererData();
}


Mesh::~Mesh()
{
  qDeleteAll(mDataSets);

  delete[] mBBoxes;
  mBBoxes = 0;

  delete[] mE4Qtmp;
  mE4Qtmp = 0;

  delete [] mE4QtmpIndex;
  mE4QtmpIndex = 0;

  delete[] mProjNodes;
  mProjNodes = 0;

  delete[] mProjBBoxes;
  mProjBBoxes = 0;
}


BBox Mesh::computeMeshExtent(bool projected)
{
  BBox b;

  const Node* nodes = projected ? projectedNodes() : mNodes.constData();

  if (mNodes.count() == 0)
    return b;

  b.minX = nodes[0].x;
  b.maxX = nodes[0].x;
  b.minY = nodes[0].y;
  b.maxY = nodes[0].y;

  for (int i = 0; i < mNodes.count(); i++)
  {
    const Node& n = nodes[i];
    if(n.x > b.maxX) b.maxX = n.x;
    if(n.x < b.minX) b.minX = n.x;
    if(n.y > b.maxY) b.maxY = n.y;
    if(n.y < b.minY) b.minY = n.y;
  }
  return b;
}


double Mesh::valueAt(const Output* output, double xCoord, double yCoord) const
{
  if (!output)
    return -9999.0;

 // We want to find the value at the given coordinate
 // Loop through all the elements in the dataset and make a list of those

  std::vector<uint> candidateElementIds;
  for (int i = 0; i < mElems.count(); i++)
  {
    const BBox& bbox = projectedBBox(i);
    if (bbox.isPointInside(xCoord, yCoord))
      candidateElementIds.push_back(i);
  }

  if( candidateElementIds.size() == 0 )
      return -9999.0;

  double value;

  for (uint i=0; i < candidateElementIds.size(); i++)
  {
    uint elemIndex = candidateElementIds.at(i);
    if (!output->active[elemIndex])
      continue;

    if (valueAt(elemIndex, xCoord, yCoord, &value, output))
      // We successfully got a value, return it and leave
      return value;
  }

  return -9999.0;
}


//! abstract class that provides values for interpolation
struct ValueAccessor
{
  virtual float value(int nodeIndex) const = 0;
};

struct ScalarValueAccessor : public ValueAccessor
{
  ScalarValueAccessor(const float* values) : mValues(values) {}
  float value(int nodeIndex) const { return mValues[nodeIndex]; }
  const float* mValues;
};

struct VectorValueAccessorX : public ValueAccessor
{
  VectorValueAccessorX(const Output::float2D* values) : mValues(values) {}
  float value(int nodeIndex) const { return mValues[nodeIndex].x; }
  const Output::float2D* mValues;
};

struct VectorValueAccessorY : public ValueAccessor
{
  VectorValueAccessorY(const Output::float2D* values) : mValues(values) {}
  float value(int nodeIndex) const { return mValues[nodeIndex].y; }
  const Output::float2D* mValues;
};


bool Mesh::valueAt(uint elementIndex, double x, double y, double* value, const Output* output) const
{
  ScalarValueAccessor accessor(output->values.constData());
  return interpolate(elementIndex, x, y, value, output, &accessor);
}

bool Mesh::interpolate(uint elementIndex, double x, double y, double* value, const Output* output, const ValueAccessor* accessor) const
{
  const Mesh* mesh = output->dataSet->mesh();
  const Element& elem = mesh->elements()[elementIndex];

  if (elem.eType == Element::E4Q)
  {
    int e4qIndex = mE4QtmpIndex[elementIndex];
    E4Qtmp& e4q = mE4Qtmp[e4qIndex];

    double Lx, Ly;
    if (!E4Q_mapPhysicalToLogical(e4q, x, y, Lx, Ly))
      return false;

    if (Lx < 0 || Ly < 0 || Lx > 1 || Ly > 1)
      return false;

    double q11 = accessor->value( elem.p[2] );
    double q12 = accessor->value( elem.p[1] );
    double q21 = accessor->value( elem.p[3] );
    double q22 = accessor->value( elem.p[0] );

    *value = q11*Lx*Ly + q21*(1-Lx)*Ly + q12*Lx*(1-Ly) + q22*(1-Lx)*(1-Ly);

    return true;

  }
  else if (elem.eType == Element::E3T)
  {

    /*
        So - we're interpoalting a 3-noded triangle
        The query point must be within the bounding box of this triangl but not nessisarily
        within the triangle itself.
      */

    /*
      First determine if the point of interest lies within the triangle using Barycentric techniques
      described here:  http://www.blackpawn.com/texts/pointinpoly/
      */

    const Node* nodes = projectedNodes();
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

    double z1 = accessor->value( elem.p[0] );
    double z2 = accessor->value( elem.p[1] );
    double z3 = accessor->value( elem.p[2] );
    *value = lam1 * z3 + lam2 * z2 + lam3 * z1;
    return true;

  }
  else
  {
    Q_ASSERT(0 && "unknown element type");
    return false;
  }
}

bool Mesh::vectorValueAt(uint elementIndex, double x, double y, double* valueX, double* valueY, const Output* output) const
{
  VectorValueAccessorX accessorX(output->valuesV.constData());
  VectorValueAccessorY accessorY(output->valuesV.constData());
  bool resX = interpolate(elementIndex, x, y, valueX, output, &accessorX);
  bool resY = interpolate(elementIndex, x, y, valueY, output, &accessorY);
  return resX && resY;
}


static void updateBBox(BBox& bbox, const Element& elem, const Node* nodes)
{
  const Node& node0 = nodes[elem.p[0]];

  bbox.minX = node0.x;
  bbox.minY = node0.y;
  bbox.maxX = node0.x;
  bbox.maxY = node0.y;

  for (int j = 1; j < elem.nodeCount(); ++j)
  {
    const Node& n = nodes[elem.p[j]];
    if (n.x < bbox.minX) bbox.minX = n.x;
    if (n.x > bbox.maxX) bbox.maxX = n.x;
    if (n.y < bbox.minY) bbox.minY = n.y;
    if (n.y > bbox.maxY) bbox.maxY = n.y;
  }

  //bbox.maxSize = std::max( (bbox.maxX - bbox.minX),
  //                         (bbox.maxY - bbox.minY) );

}



void Mesh::computeTempRendererData()
{

  // In order to keep things running quickly, we pre-compute many
  // element properties to speed up drawing at the expenses of memory.

  // Element bounding box (xmin, xmax and friends)

  mBBoxes = new BBox[mElems.count()];

  int E4Qcount = elementCountForType(Element::E4Q);
  mE4Qtmp = new E4Qtmp[E4Qcount];
  mE4QtmpIndex = new int[mElems.count()];
  memset(mE4QtmpIndex, -1, sizeof(int)*mElems.count());
  int e4qIndex = 0;

  int i = 0;
  for (Mesh::Elements::const_iterator it = mElems.constBegin(); it != mElems.constEnd(); ++it, ++i)
  {
    if (it->isDummy())
      continue;

    const Element& elem = *it;

    updateBBox(mBBoxes[i], elem, mNodes.constData());

    if (elem.eType == Element::E4Q)
    {
      // cache some temporary data for faster rendering
      mE4QtmpIndex[i] = e4qIndex;
      E4Qtmp& e4q = mE4Qtmp[e4qIndex];

      E4Q_computeMapping(elem, e4q, mNodes.constData());
      e4qIndex++;
    }
  }
}


void Mesh::setNoProjection()
{
  if (!mProjection)
    return; // nothing to do

  delete [] mProjNodes;
  mProjNodes = 0;
  delete [] mProjBBoxes;
  mProjBBoxes = 0;

  for (int i = 0; i < mElems.count(); ++i)
  {
    const Element& elem = mElems[i];
    if (elem.eType == Element::E4Q)
    {
      int e4qIndex = mE4QtmpIndex[i];
      E4Q_computeMapping(elem, mE4Qtmp[e4qIndex], mNodes.constData());
    }
  }

  mProjection = false;
  mSrcProj4.clear();
  mDestProj4.clear();
}

bool Mesh::setProjection(const QString& srcProj4, const QString& destProj4)
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
    mProjNodes = new Node[mNodes.count()];

  memcpy(mProjNodes, mNodes.constData(), sizeof(Node)*mNodes.count());

  if (pj_is_latlong(projSrc))
  {
    // convert source from degrees to radians
    for (int i = 0; i < mNodes.count(); ++i)
    {
      mProjNodes[i].x *= DEG2RAD;
      mProjNodes[i].y *= DEG2RAD;
    }
  }

  int res = pj_transform(projSrc, projDst, mNodes.count(), 3, &mProjNodes->x, &mProjNodes->y, NULL);

  if (res != 0)
  {
    qDebug("Crayfish: reprojection failed (%s)", pj_strerrno(res));
    setNoProjection();
    return false;
  }

  if (pj_is_latlong(projDst))
  {
    // convert source from degrees to radians
    for (int i = 0; i < mNodes.count(); ++i)
    {
      mProjNodes[i].x *= RAD2DEG;
      mProjNodes[i].y *= RAD2DEG;
    }
  }

  pj_free(projSrc);
  pj_free(projDst);

  mProjExtent = computeMeshExtent(true);

  if (mProjBBoxes == 0)
    mProjBBoxes = new BBox[mElems.count()];

  for (int i = 0; i < mElems.count(); ++i)
  {
    const Element& elem = mElems[i];
    updateBBox(mProjBBoxes[i], elem, mProjNodes);

    if (elem.eType == Element::E4Q)
    {
      int e4qIndex = mE4QtmpIndex[i];
      E4Q_computeMapping(elem, mE4Qtmp[e4qIndex], mProjNodes); // update interpolation coefficients
    }
  }

  return true;
}

bool Mesh::hasProjection() const
{
  return mProjection;
}
