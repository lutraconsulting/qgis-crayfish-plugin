#ifndef CRAYFISH_E4Q_H
#define CRAYFISH_E4Q_H

/**
  Utility functions for handling quadrilateral elements.

  Physical coordinates = real coordinates within the mest
  Logical coordinates = Quadrilateral mapped to a unit square (for bilinear interpolation)
*/

#include "crayfish_mesh.h"

//! precalculate coefficients for the mapping between logical and physical coordinates
void E4Q_computeMapping(Element& elem, E4Qtmp& e4q, Node* nodes);

void E4Q_mapLogicalToPhysical(const E4Qtmp& e4q, double Lx, double Ly, double& Px, double& Py);
bool E4Q_mapPhysicalToLogical(const E4Qtmp& e4q, double x, double y, double& Lx, double& Ly);

//! check whether the quadrilateral is complex (butterfly shape)
bool E4Q_isComplex(const Element& elem, Node* nodes);

#endif // CRAYFISH_E4Q_H
