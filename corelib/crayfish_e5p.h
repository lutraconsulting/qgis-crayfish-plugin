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

#ifndef CRAYFISH_E5P_H
#define CRAYFISH_E5P_H

/**
  Utility functions for handling Generalized Barycentric Coordinates on Irregular Polygons

  So far it is not cached to keep it simple. Needs 5 vertexes, but algorithm works for 3-N vertexes

  based on http://geometry.caltech.edu/pubs/MHBD02.pdf

  Physical coordinates = real coordinates within the mesh
  Logical coordinates = interpolation coefficients
*/

#include "crayfish_mesh.h"

#include <QVector>
#include <QPointF>

bool E5P_physicalToLogical(const QVector<QPointF>& pX, QPointF pP, QVector<double>& lam);

void E5P_centroid(const QVector<QPointF>& pX, double& cx, double& cy);

#endif // CRAYFISH_E5P_H
