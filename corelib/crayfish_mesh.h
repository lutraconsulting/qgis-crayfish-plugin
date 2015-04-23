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

#ifndef CRAYFISH_MESH_H
#define CRAYFISH_MESH_H

#include <QPointF>
#include <QString>
#include <QVector>


struct BBox;
struct E4Qtmp;
class DataSet;
class Output;


struct Node
{
    int id;    //!< just a reference to the ID in the input file (internally we use indices)
    double x;
    double y;

    bool operator==(const Node& other) const { return x == other.x && y == other.y; }
    QPointF toPointF() const { return QPointF(x,y); }
};

struct BBox
{
  double minX;
  double maxX;
  double minY;
  double maxY;

  bool isPointInside(double x, double y) const { return x >= minX && x <= maxX && y >= minY && y <= maxY; }
};

struct Element
{
    enum Type
    {
      Undefined,
      E4Q,
      E3T
    };

    int nodeCount() const { switch (eType) { case E4Q: return 4; case E3T: return 3; default: return 0; } }
    bool isDummy() const { return eType == Undefined; }

    int id;        //!< just a reference to the ID in the input file (internally we use indices)
    Type eType;
    uint p[4];     //!< indices of nodes
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

class ValueAccessor;

/** Adds data + functionality for reprojection, identification, support for rendering */
class Mesh : public BasicMesh
{
public:
  Mesh(const Nodes& nodes, const Elements& elements);
  ~Mesh();

  void addDataSet(DataSet* ds);

  const DataSets& dataSets() const { return mDataSets; }

  BBox extent() const { return mExtent; }

  double valueAt(const Output* output, double xCoord, double yCoord) const;
  bool valueAt(uint elementIndex, double x, double y, double* value, const Output* output) const;

  bool vectorValueAt(uint elementIndex, double x, double y, double* valueX, double* valueY, const Output* output) const;

  void setNoProjection();
  bool setProjection(const QString& srcProj4, const QString& destProj4);
  bool hasProjection() const;
  QString sourceCrsProj4() const { return mSrcProj4; }
  QString destCrsProj4() const { return mDestProj4; }

  BBox projectedExtent() const { return mProjection ? mProjExtent : mExtent; }
  const Node* projectedNodes() const { return mProjection ? mProjNodes : mNodes.constData(); }
  const Node& projectedNode(int nodeIndex) const { return mProjection ? mProjNodes[nodeIndex] : mNodes[nodeIndex]; }
  const BBox& projectedBBox(int elemIndex) const { return mProjection ? mProjBBoxes[elemIndex] : mBBoxes[elemIndex]; }

protected:

  BBox computeMeshExtent(bool projected);
  void computeTempRendererData();

  //! low-level interpolation routine
  bool interpolate(uint elementIndex, double x, double y, double* value, const Output* output, const ValueAccessor* accessor) const;

  BBox mExtent; //!< unprojected mesh extent

  // associated data
  DataSets mDataSets;  //!< pointers to datasets are owned by this class

  // cached data for rendering

  E4Qtmp* mE4Qtmp;   //!< contains rendering information for quads
  int* mE4QtmpIndex; //!< for conversion from element index to mE4Qtmp indexes
  BBox* mBBoxes; //! bounding boxes of elements (non-projected)

  // reprojection support

  QString mSrcProj4;  //!< CRS's proj.4 string of the source (layer)
  QString mDestProj4; //!< CRS's proj.4 string of the destination (project)

  bool mProjection; //!< whether doing reprojection from mesh coords to map coords
  Node* mProjNodes; //!< reprojected nodes
  BBox* mProjBBoxes; //!< reprojected bounding boxes of elements
  BBox mProjExtent;
};


#endif // CRAYFISH_MESH_H
