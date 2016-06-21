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

#ifndef CRAYFISH_E4Q_H
#define CRAYFISH_E4Q_H

/**
  Utility functions for handling quadrilateral elements.

  Physical coordinates = real coordinates within the mest
  Logical coordinates = Quadrilateral mapped to a unit square (for bilinear interpolation)
*/

#include "crayfish_mesh.h"

/** auxilliary cached data used for rendering of E4Q elements */
struct E4Qtmp
{
  double a[4], b[4]; //!< coefficients for mapping between physical and logical coords
};

struct E4QNormalization
{
  double x0;
  double y0;
  double range_x;
  double range_y;

  double normX(double x) const;
  double realX(double x) const;
  double normY(double y) const;
  double realY(double y) const;
  void init(const BBox& extent);
  E4QNormalization(): x0(0), y0(0), range_x(1), range_y(1) {}
  E4QNormalization(const BBox& extent) {init(extent);}
};

//! precalculate coefficients for the mapping between logical and physical coordinates
void E4Q_computeMapping(const Element& elem, E4Qtmp& e4q, const Node* nodes, const E4QNormalization& norm);

void E4Q_mapLogicalToPhysical(const E4Qtmp& e4q, double Lx, double Ly, double& Px, double& Py, const E4QNormalization& norm);
bool E4Q_mapPhysicalToLogical(const E4Qtmp& e4q, double x, double y, double& Lx, double& Ly, const E4QNormalization& norm);

//! check whether the quadrilateral is complex (butterfly shape)
bool E4Q_isComplex(const Element& elem, Node* nodes);

//! check if quadrilateral has correct orientation (needs clockwise)
bool E4Q_isValid(const Element& elem, Node* nodes);

//! calculate centroid of the quadrilateral
void E4Q_centroid(const E4Qtmp& e4q, double& cx, double& cy, const E4QNormalization &norm);

#endif // CRAYFISH_E4Q_H
