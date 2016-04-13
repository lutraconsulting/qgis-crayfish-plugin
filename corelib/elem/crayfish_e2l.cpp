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

#include "crayfish_e2l.h"
#include "math.h"
#include <QPointF>
#include <QVector2D>
#include <limits>

bool E2L_physicalToLogical(QPointF pA, QPointF pB, QPointF pP, double& lam)
{
  if (pA == pB)
    return false; // this is not a valid line!

  //distance from pA
  double vBA = QVector2D(pB-pA).length();
  double vPA = QVector2D(pP-pA).length();
  double vPB = QVector2D(pP-pB).length();
  double eps = std::numeric_limits<double>::min();


  if (fabs(vBA - vPA - vPB) > eps) {
      // not on line
      return false;
  }

  lam = vPA/vBA;
  return true;
}

void E2L_centroid(QPointF pA, QPointF pB, double& cx, double& cy)
{
  cx = (pA.x() + pB.x())/2.;
  cy = (pA.y() + pB.y())/2.;
}
