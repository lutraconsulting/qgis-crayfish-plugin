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

#include "crayfish_mesh.h"

#include "elem/crayfish_e2l.h"
#include "elem/crayfish_e3t.h"
#include "elem/crayfish_e4q.h"
#include "elem/crayfish_eNp.h"
#include "crayfish_dataset.h"
#include "crayfish_output.h"

#include <QVector2D>

#include <ogr_srs_api.h>
#include <proj_api.h>

#define DEG2RAD   (3.14159265358979323846 / 180)
#define RAD2DEG   (180 / 3.14159265358979323846)

void outputUpdater::checkMem(const Output *addedOutput) {
  size += addedOutput->size;
  allocatedOutputs.push(addedOutput);
  while (size > maxSize) {
    const Output *toRemove = allocatedOutputs.front();
    size -= toRemove->size;
    if (toRemove->type() == toRemove->TypeNode)
      const_cast<NodeOutput*>(static_cast<const NodeOutput*> (toRemove))->init(0, 0, true);
    else
      const_cast<ElementOutput*>(static_cast<const ElementOutput*> (toRemove))->init(0, true);
    allocatedOutputs.pop();
  }
}

BasicMesh::BasicMesh(const Mesh::Nodes& nodes, const Mesh::Elements& elements)
  : mNodes(nodes)
  , mElems(elements) {
}

BasicMesh::~BasicMesh() {
}

void Mesh::addDataSet(DataSet* ds) {
  mDataSets.append(ds);
  ds->setMesh(this);
}

int BasicMesh::elementCountForType(Element::Type type) {
  int cnt = 0;
  for (int i = 0; i < mElems.count(); ++i) {
    if (mElems[i].eType() == type)
      ++cnt;
  }
  return cnt;
}



Mesh::Mesh(const BasicMesh::Nodes& nodes, const BasicMesh::Elements& elements)
  : BasicMesh(nodes, elements)
  , mE4Qtmp(0)
  , mE4QtmpIndex(0)
  , mBBoxes(0)
  , mE4Qnorm(0)
  , mProjection(false)
  , mProjNodes(0)
  , mProjBBoxes(0) {
  mExtent = computeMeshExtent(false);

  mE4Qnorm = new E4QNormalization(mExtent);
  computeTempRendererData();
  updater = NULL;
}


Mesh::~Mesh() {
  qDeleteAll(mDataSets);

  delete[] mBBoxes;
  mBBoxes = 0;

  delete[] mE4Qtmp;
  mE4Qtmp = 0;

  delete mE4Qnorm;
  mE4Qnorm = 0;

  delete [] mE4QtmpIndex;
  mE4QtmpIndex = 0;

  delete[] mProjNodes;
  mProjNodes = 0;

  delete[] mProjBBoxes;
  mProjBBoxes = 0;

  if (updater) delete updater;
}

DataSet* Mesh::dataSet(const QString& name) {
  DataSets sets = dataSets();
  foreach (DataSet* ds, sets) {
    if (ds->name() == name) {
      return ds;
    }
  }
  return 0;
}

BBox Mesh::computeMeshExtent(bool projected) {
  const Node* nodes = projected ? projectedNodes() : mNodes.constData();
  return computeExtent(nodes, mNodes.count());
}

BBox computeExtent(const Node* nodes, int size) {
  BBox b;

  if (size == 0)
    return b;

  b.minX = nodes[0].x;
  b.maxX = nodes[0].x;
  b.minY = nodes[0].y;
  b.maxY = nodes[0].y;

  for (int i = 0; i < size; i++) {
    const Node& n = nodes[i];
    if(n.x > b.maxX) b.maxX = n.x;
    if(n.x < b.minX) b.minX = n.x;
    if(n.y > b.maxY) b.maxY = n.y;
    if(n.y < b.minY) b.minY = n.y;
  }
  return b;
}


double Mesh::valueAt(const Output* output, double xCoord, double yCoord) const {
  if (!output)
    return -9999.0;

// We want to find the value at the given coordinate
// Loop through all the elements in the dataset and make a list of those

  std::vector<uint> candidateElementIds;
  for (int i = 0; i < mElems.count(); i++) {
    const BBox& bbox = projectedBBox(i);
    if (bbox.isPointInside(xCoord, yCoord))
      candidateElementIds.push_back(i);
  }

  if( candidateElementIds.size() == 0 )
    return -9999.0;

  double value;

  for (uint i=0; i < candidateElementIds.size(); i++) {
    uint elemIndex = candidateElementIds.at(i);
    if (!output->isActive(elemIndex))
      continue;

    if (valueAt(elemIndex, xCoord, yCoord, &value, output))
      // We successfully got a value, return it and leave
      return value;
  }

  return -9999.0;
}


//! abstract class that provides values for interpolation
struct ValueAccessor {
  virtual float value(int nodeIndex) const = 0;
};

struct ScalarValueAccessor : public ValueAccessor {
  ScalarValueAccessor(const float* values) : mValues(values) {}
  float value(int nodeIndex) const {
    return mValues[nodeIndex];
  }
  const float* mValues;
};

struct VectorValueAccessorX : public ValueAccessor {
  VectorValueAccessorX(const NodeOutput::float2D* values) : mValues(values) {}
  float value(int nodeIndex) const {
    return mValues[nodeIndex].x;
  }
  const NodeOutput::float2D* mValues;
};

struct VectorValueAccessorY : public ValueAccessor {
  VectorValueAccessorY(const NodeOutput::float2D* values) : mValues(values) {}
  float value(int nodeIndex) const {
    return mValues[nodeIndex].y;
  }
  const NodeOutput::float2D* mValues;
};


bool Mesh::valueAt(uint elementIndex, double x, double y, double* value, const Output* output) const {
  if (output->type() == Output::TypeNode) {
    const NodeOutput* nodeOutput = static_cast<const NodeOutput*>(output);
    ScalarValueAccessor accessor(nodeOutput->getValues().constData());
    return interpolate(elementIndex, x, y, value, nodeOutput, &accessor);
  } else {
    const ElementOutput* elemOutput = static_cast<const ElementOutput*>(output);
    ScalarValueAccessor accessor(elemOutput->getValues().constData());
    return interpolateElementCentered(elementIndex, x, y, value, elemOutput, &accessor);
  }
}

bool Mesh::interpolate(uint elementIndex, double x, double y, double* value, const NodeOutput* output, const ValueAccessor* accessor) const {
  const Mesh* mesh = output->dataSet->mesh();
  const Element& elem = mesh->elements()[elementIndex];

  if (elem.eType() == Element::ENP) {
    const Node* nodes = projectedNodes();
    QPolygonF pX(elem.nodeCount());
    QVector<double> lam(elem.nodeCount());

    for (int i=0; i<elem.nodeCount(); i++) {
      pX[i] = nodes[elem.p(i)].toPointF();
    }

    if (!ENP_physicalToLogical(pX, QPointF(x, y), lam))
      return false;

    *value = 0;
    for (int i=0; i<elem.nodeCount(); i++) {
      *value += lam[i] * accessor->value( elem.p(i) );
    }

    return true;
  } else if (elem.eType() == Element::E4Q) {
    int e4qIndex = mE4QtmpIndex[elementIndex];
    E4Qtmp& e4q = mE4Qtmp[e4qIndex];

    double Lx, Ly;
    if (!E4Q_mapPhysicalToLogical(e4q, x, y, Lx, Ly, *mE4Qnorm))
      return false;

    if (Lx < 0 || Ly < 0 || Lx > 1 || Ly > 1)
      return false;

    double q11 = accessor->value( elem.p(2) );
    double q12 = accessor->value( elem.p(1) );
    double q21 = accessor->value( elem.p(3) );
    double q22 = accessor->value( elem.p(0) );

    *value = q11*Lx*Ly + q21*(1-Lx)*Ly + q12*Lx*(1-Ly) + q22*(1-Lx)*(1-Ly);

    return true;

  } else if (elem.eType() == Element::E3T) {

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

    double lam1, lam2, lam3;
    if (!E3T_physicalToBarycentric(nodes[elem.p(0)].toPointF(),
                                   nodes[elem.p(1)].toPointF(),
                                   nodes[elem.p(2)].toPointF(),
                                   QPointF(x, y),
                                   lam1, lam2, lam3))
      return false;

    // Now interpolate

    double z1 = accessor->value( elem.p(0));
    double z2 = accessor->value( elem.p(1));
    double z3 = accessor->value( elem.p(2));
    *value = lam1 * z3 + lam2 * z2 + lam3 * z1;
    return true;

  } else if (elem.eType() == Element::E2L) {

    /*
        So - we're interpoalting a 2-noded line
    */
    const Node* nodes = projectedNodes();
    double lam;

    if (!E2L_physicalToLogical(nodes[elem.p(0)].toPointF(),
                               nodes[elem.p(1)].toPointF(),
                               QPointF(x, y),
                               lam))
      return false;

    // Now interpolate

    double z1 = accessor->value( elem.p(0) );
    double z2 = accessor->value( elem.p(1) );

    *value = z1 + lam * (z2 - z1);
    return true;

  } else {
    Q_ASSERT(0 && "unknown element type");
    return false;
  }
}


bool Mesh::interpolateElementCentered(uint elementIndex, double x, double y, double* value, const ElementOutput* output, const ValueAccessor* accessor) const {
  const Mesh* mesh = output->dataSet->mesh();
  const Element& elem = mesh->elements()[elementIndex];

  if (elem.eType() == Element::ENP) {
    const Node* nodes = projectedNodes();
    QPolygonF pX(elem.nodeCount());
    QVector<double> lam(elem.nodeCount());

    for (int i=0; i<elem.nodeCount(); i++) {
      pX[i] = nodes[elem.p(i)].toPointF();
    }

    if (!ENP_physicalToLogical(pX, QPointF(x, y), lam))
      return false;

    *value = accessor->value(elementIndex);
    return true;
  } else if (elem.eType() == Element::E4Q) {
    int e4qIndex = mE4QtmpIndex[elementIndex];
    E4Qtmp& e4q = mE4Qtmp[e4qIndex];

    double Lx, Ly;
    if (!E4Q_mapPhysicalToLogical(e4q, x, y, Lx, Ly, *mE4Qnorm))
      return false;

    if (Lx < 0 || Ly < 0 || Lx > 1 || Ly > 1)
      return false;

    *value = accessor->value(elementIndex);
    return true;
  } else if (elem.eType() == Element::E3T) {
    const Node* nodes = projectedNodes();

    double lam1, lam2, lam3;
    if (!E3T_physicalToBarycentric(nodes[elem.p(0)].toPointF(),
                                   nodes[elem.p(1)].toPointF(),
                                   nodes[elem.p(2)].toPointF(),
                                   QPointF(x, y),
                                   lam1, lam2, lam3))
      return false;

    // Now interpolate

    *value = accessor->value(elementIndex);
    return true;

  } else if (elem.eType() == Element::E2L) {
    const Node* nodes = projectedNodes();

    double lam;
    if (!E2L_physicalToLogical(nodes[elem.p(0)].toPointF(),
                               nodes[elem.p(1)].toPointF(),
                               QPointF(x, y),
                               lam))
      return false;


    // Now interpolate
    *value = accessor->value(elementIndex);
    return true;

  } else {
    Q_ASSERT(0 && "unknown element type");
    return false;
  }

}


bool Mesh::vectorValueAt(uint elementIndex, double x, double y, double* valueX, double* valueY, const Output* output) const {
  if (output->type() == Output::TypeNode) {
    const NodeOutput* nodeOutput = static_cast<const NodeOutput*>(output);
    VectorValueAccessorX accessorX(nodeOutput->getValuesV().constData());
    VectorValueAccessorY accessorY(nodeOutput->getValuesV().constData());
    bool resX = interpolate(elementIndex, x, y, valueX, nodeOutput, &accessorX);
    bool resY = interpolate(elementIndex, x, y, valueY, nodeOutput, &accessorY);
    return resX && resY;
  } else {
    const ElementOutput* elemOutput = static_cast<const ElementOutput*>(output);
    VectorValueAccessorX accessorX(elemOutput->getValuesV().constData());
    VectorValueAccessorY accessorY(elemOutput->getValuesV().constData());
    bool resX = interpolateElementCentered(elementIndex, x, y, valueX, elemOutput, &accessorX);
    bool resY = interpolateElementCentered(elementIndex, x, y, valueY, elemOutput, &accessorY);
    return resX && resY;
  }
}


static void updateBBox(BBox& bbox, const Element& elem, const Node* nodes) {
  Q_ASSERT(elem.nodeCount() > 1);
  const Node& node0 = nodes[elem.p(0)];

  bbox.minX = node0.x;
  bbox.minY = node0.y;
  bbox.maxX = node0.x;
  bbox.maxY = node0.y;

  for (int j = 1; j < elem.nodeCount(); ++j) {
    const Node& n = nodes[elem.p(j)];
    if (n.x < bbox.minX) bbox.minX = n.x;
    if (n.x > bbox.maxX) bbox.maxX = n.x;
    if (n.y < bbox.minY) bbox.minY = n.y;
    if (n.y > bbox.maxY) bbox.maxY = n.y;
  }

  //bbox.maxSize = std::max( (bbox.maxX - bbox.minX),
  //                         (bbox.maxY - bbox.minY) );

}



void Mesh::computeTempRendererData() {

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
  for (Mesh::Elements::const_iterator it = mElems.constBegin(); it != mElems.constEnd(); ++it, ++i) {
    if (it->isDummy())
      continue;

    const Element& elem = *it;

    updateBBox(mBBoxes[i], elem, mNodes.constData());

    if (elem.eType() == Element::E4Q) {
      // cache some temporary data for faster rendering
      mE4QtmpIndex[i] = e4qIndex;
      E4Qtmp& e4q = mE4Qtmp[e4qIndex];

      E4Q_computeMapping(elem, e4q, mNodes.constData(), *mE4Qnorm);
      e4qIndex++;
    }
  }
}


void Mesh::setNoProjection() {
  if (!mProjection)
    return; // nothing to do

  delete [] mProjNodes;
  mProjNodes = 0;
  delete [] mProjBBoxes;
  mProjBBoxes = 0;

  mE4Qnorm->init(mExtent);

  for (int i = 0; i < mElems.count(); ++i) {
    const Element& elem = mElems[i];
    if (elem.eType() == Element::E4Q) {
      int e4qIndex = mE4QtmpIndex[i];
      E4Q_computeMapping(elem, mE4Qtmp[e4qIndex], mNodes.constData(), *mE4Qnorm);
    }
  }

  mProjection = false;
}

static QString _setSourceCrsFromESRI(const QString& wkt) {
  QString ret;

  QString wkt2("ESRI::" + wkt);
  OGRSpatialReferenceH hSRS = OSRNewSpatialReference(NULL);
  QByteArray arr = wkt2.toUtf8();
  if (OSRSetFromUserInput(hSRS, arr.constData()) == OGRERR_NONE) {
    char * ppszReturn = 0;
    if (OSRExportToProj4(hSRS, &ppszReturn) == OGRERR_NONE && ppszReturn != 0) {
      ret = ppszReturn;
    }
  }
  OSRDestroySpatialReference(hSRS);

  return ret;
}

static QString _setSourceCrsFromWKT(const QString& wkt) {
  QString ret;
  OGRSpatialReferenceH hSRS = OSRNewSpatialReference(NULL);
  QByteArray arr = wkt.toUtf8();
  const char* raw_data = arr.constData();
  if (OSRImportFromWkt(hSRS, const_cast<char**>(&raw_data)) == OGRERR_NONE) {
    char * ppszReturn = 0;
    if (OSRExportToProj4(hSRS, &ppszReturn) == OGRERR_NONE && ppszReturn != 0) {
      ret = ppszReturn;
    }
  }
  OSRDestroySpatialReference(hSRS);

  return ret;
}

void Mesh::setSourceCrsFromWKT(const QString& wkt) {
  QString proj4 = _setSourceCrsFromWKT(wkt);
  if (proj4.isEmpty()) {
    proj4 = _setSourceCrsFromESRI(wkt);
  }
  setSourceCrs(proj4);
}

void Mesh::setSourceCrs(const QString& srcProj4) {
  if (mSrcProj4 == srcProj4)
    return; // nothing has changed - so do nothing!

  mSrcProj4 = srcProj4;
  reprojectMesh();
}

void Mesh::setDestinationCrs(const QString& destProj4) {
  if (mDestProj4 == destProj4)
    return; // nothing has changed - so do nothing!

  mDestProj4 = destProj4;
  reprojectMesh();
}

bool Mesh::reprojectMesh() {
  // if source or destination CRS is empty, that implies we do not reproject anything
  if (mSrcProj4.isEmpty() || mDestProj4.isEmpty()) {
    setNoProjection();
    return true;
  }

  projPJ projSrc = pj_init_plus(mSrcProj4.toAscii().data());
  if (!projSrc) {
    qDebug("Crayfish: source proj4 string is not valid! (%s)", pj_strerrno(pj_errno));
    setNoProjection();
    return false;
  }

  projPJ projDst = pj_init_plus(mDestProj4.toAscii().data());
  if (!projDst) {
    pj_free(projSrc);
    qDebug("Crayfish: source proj4 string is not valid! (%s)", pj_strerrno(pj_errno));
    setNoProjection();
    return false;
  }

  mProjection = true;

  if (mProjNodes == 0)
    mProjNodes = new Node[mNodes.count()];

  memcpy(mProjNodes, mNodes.constData(), sizeof(Node)*mNodes.count());

  if (pj_is_latlong(projSrc)) {
    // convert source from degrees to radians
    for (int i = 0; i < mNodes.count(); ++i) {
      mProjNodes[i].x *= DEG2RAD;
      mProjNodes[i].y *= DEG2RAD;
    }
  }

  int res = pj_transform(projSrc, projDst, mNodes.count(), 3, &mProjNodes->x, &mProjNodes->y, NULL);

  if (res != 0) {
    qDebug("Crayfish: reprojection failed (%s)", pj_strerrno(res));
    setNoProjection();
    return false;
  }

  if (pj_is_latlong(projDst)) {
    // convert source from degrees to radians
    for (int i = 0; i < mNodes.count(); ++i) {
      mProjNodes[i].x *= RAD2DEG;
      mProjNodes[i].y *= RAD2DEG;
    }
  }

  pj_free(projSrc);
  pj_free(projDst);

  mProjExtent = computeMeshExtent(true);
  mE4Qnorm->init(mProjExtent);

  if (mProjBBoxes == 0)
    mProjBBoxes = new BBox[mElems.count()];

  for (int i = 0; i < mElems.count(); ++i) {
    const Element& elem = mElems[i];
    updateBBox(mProjBBoxes[i], elem, mProjNodes);

    if (elem.eType() == Element::E4Q) {
      int e4qIndex = mE4QtmpIndex[i];
      E4Q_computeMapping(elem, mE4Qtmp[e4qIndex], mProjNodes, *mE4Qnorm); // update interpolation coefficients
    }
  }

  return true;
}

bool Mesh::hasProjection() const {
  return mProjection;
}


void Mesh::elementCentroid(int elemIndex, double& cx, double& cy) const {
  const Element& e = mElems[elemIndex];

  if (e.eType() == Element::ENP) {
    const Node* nodes = projectedNodes();
    QPolygonF pX(e.nodeCount());
    for (int i=0; i<e.nodeCount(); i++) {
      pX[i] = nodes[e.p(i)].toPointF();
    }
    ENP_centroid(pX, cx, cy);
  } else if (e.eType() == Element::E4Q) {
    int e4qIndex = mE4QtmpIndex[elemIndex];
    E4Qtmp& e4q = mE4Qtmp[e4qIndex];
    E4Q_centroid(e4q, cx, cy, *mE4Qnorm);
  } else if (e.eType() == Element::E3T) {
    const Node* nodes = projectedNodes();
    E3T_centroid(nodes[e.p(0)].toPointF(), nodes[e.p(1)].toPointF(), nodes[e.p(2)].toPointF(), cx, cy);
  } else if (e.eType() == Element::E2L) {
    const Node* nodes = projectedNodes();
    E2L_centroid(nodes[e.p(0)].toPointF(), nodes[e.p(1)].toPointF(), cx, cy);
  } else
    Q_ASSERT(0 && "element not supported");
}
