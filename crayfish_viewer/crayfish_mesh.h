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

#include "crayfish_viewer_global.h"

#include <QPointF>

struct Node{
    double x;
    double y;

    bool operator==(const Node& other) const { return x == other.x && y == other.y; }
    QPointF toPointF() const { return QPointF(x,y); }
};

struct BBox {
  double minX;
  double maxX;
  double minY;
  double maxY;

  double maxSize; // Largest distance (real world) across the element

  bool isPointInside(double x, double y) const { return x >= minX && x <= maxX && y >= minY && y <= maxY; }
};

struct Element{
    uint index;
    ElementType::Enum eType;
    int nodeCount;
    bool isDummy;
    uint p[4];     //!< indices of nodes
    BBox bbox;     //!< bounding box of the element

    int indexTmp; //!< index into array with temporary information for particular element type
};

/** auxilliary cached data used for rendering of E4Q elements */
struct E4Qtmp
{
  double a[4], b[4]; //!< coefficients for mapping between physical and logical coords
};


#endif // CRAYFISH_MESH_H
