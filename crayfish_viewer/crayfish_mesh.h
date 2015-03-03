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

#ifndef CRAYFISH_MESH_H
#define CRAYFISH_MESH_H

#include <QPointF>
#include <QVector>

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

  double maxSize; // Largest distance (real world) across the element

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


class DataSet;

class Mesh
{
public:
  typedef QVector<Node> Nodes;
  typedef QVector<Element> Elements;
  typedef QVector<DataSet*> DataSets;

  Mesh(const Nodes& nodes, const Elements& elements);
  ~Mesh();

  const Nodes& nodes() const { return mNodes; }
  const Elements& elements() const { return mElems; }
  const DataSets& dataSets() const { return mDataSets; }

  Nodes& nodes() { return mNodes; }
  Elements& elements() { return mElems; }
  DataSets& dataSets() { return mDataSets; }

  int elementCountForType(Element::Type type);

protected:

  // mesh topology
  Nodes mNodes;
  Elements mElems;

  // associated data
  DataSets mDataSets;  //!< pointers to datasets are owned by this class

};


#endif // CRAYFISH_MESH_H
