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

#ifndef CRAYFISH_MESH_H
#define CRAYFISH_MESH_H

#include <QPointF>
#include <QString>
#include <QVector>
#include <queue>

#include "crayfish_element.h"

struct BBox;
struct E4Qtmp;
struct E4QNormalization;
class DataSet;
class ElementOutput;
class Output;
class NodeOutput;

//Callback class to update an output
class outputUpdater {
    size_t size;
    size_t maxSize;
    std::queue<Output *> allocatedOutputs;
public:
    outputUpdater(){
        size = 0;
        maxSize = 2UL * 1024UL * 1024UL * 1024UL; //Todo should be a parameter.
    }

    virtual ~outputUpdater(){}
    virtual int update(Output *o, int iOutput, int iDataset) = 0;
    void checkMem(Output *addedOutput);
};


struct Node
{
    double x;
    double y;

    bool operator==(const Node& other) const { return x == other.x && y == other.y; }
    QPointF toPointF() const { return QPointF(x,y); }
    void setId(int id) {mId = id;}
    int id() const {return mId;}
private:
    int mId;    //!< just a reference to the ID in the input file (internally we use indices)
};

struct BBox
{
  double minX;
  double maxX;
  double minY;
  double maxY;

  bool isPointInside(double x, double y) const { return x >= minX && x <= maxX && y >= minY && y <= maxY; }
};

/** core Mesh data structure: nodes + elements */
class BasicMesh
{
public:
  typedef QVector<Node> Nodes;
  typedef QVector<Element> Elements;
  typedef QVector<DataSet*> DataSets;

  BasicMesh(const Nodes& nodes, const Elements& elements);
  ~BasicMesh();

  const Nodes& nodes() const { return mNodes; }
  const Elements& elements() const { return mElems; }

  int elementCountForType(Element::Type type);

protected:

  // mesh topology
  Nodes mNodes;
  Elements mElems;

};

struct ValueAccessor;

/** Adds data + functionality for reprojection, identification, support for rendering */
class Mesh : public BasicMesh
{
public:
  Mesh(const Nodes& nodes, const Elements& elements);
  ~Mesh();

  void addDataSet(DataSet* ds);

  const DataSets& dataSets() const { return mDataSets; }
  DataSet* dataSet(const QString& name);

  BBox extent() const { return mExtent; }

  double valueAt(const Output* output, double xCoord, double yCoord) const;
  bool valueAt(uint elementIndex, double x, double y, double* value, const Output* output) const;

  bool vectorValueAt(uint elementIndex, double x, double y, double* valueX, double* valueY, const Output* output) const;

  void setSourceCrs(const QString& srcProj4); // proj4
  void setSourceCrsFromWKT(const QString& wkt); // wkt
  void setSourceCrsFromEPSG(int epsg); // EPSG code

  void setDestinationCrs(const QString& destProj4);
  bool hasProjection() const;
  QString sourceCrs() const { return mSrcProj4; }
  QString destinationCrs() const { return mDestProj4; }

  BBox projectedExtent() const { return mProjection ? mProjExtent : mExtent; }
  const Node* projectedNodes() const { return mProjection ? mProjNodes : mNodes.constData(); }
  const Node& projectedNode(int nodeIndex) const { return mProjection ? mProjNodes[nodeIndex] : mNodes[nodeIndex]; }
  const BBox& projectedBBox(int elemIndex) const { return mProjection ? mProjBBoxes[elemIndex] : mBBoxes[elemIndex]; }

  //! calculate centroid of given element (takes reprojection into account)
  void elementCentroid(int elemIndex, double& cx, double& cy) const;

  outputUpdater *updater;

protected:

  bool reprojectMesh();
  void setNoProjection();

  BBox computeMeshExtent(bool projected);
  void computeTempRendererData();

  //! low-level interpolation routine
  bool interpolate(uint elementIndex, double x, double y, double* value, const NodeOutput* output, const ValueAccessor* accessor) const;

  //! low-level interpolation routine for element-centered results
  bool interpolateElementCentered(uint elementIndex, double x, double y, double* value, const ElementOutput* output, const ValueAccessor* accessor) const;

  BBox mExtent; //!< unprojected mesh extent

  // associated data
  DataSets mDataSets;  //!< pointers to datasets are owned by this class

  // cached data for rendering

  E4Qtmp* mE4Qtmp;   //!< contains rendering information for quads
  int* mE4QtmpIndex; //!< for conversion from element index to mE4Qtmp indexes
  BBox* mBBoxes; //! bounding boxes of elements (non-projected)
  E4QNormalization* mE4Qnorm; //! normalization of coordinates

  // reprojection support

  QString mSrcProj4;  //!< CRS's proj.4 string of the source (layer)
  QString mDestProj4; //!< CRS's proj.4 string of the destination (project)

  bool mProjection; //!< whether doing reprojection from mesh coords to map coords
  Node* mProjNodes; //!< reprojected nodes
  BBox* mProjBBoxes; //!< reprojected bounding boxes of elements
  BBox mProjExtent;
};

BBox computeExtent(const Node* nodes, int size);

#endif // CRAYFISH_MESH_H
