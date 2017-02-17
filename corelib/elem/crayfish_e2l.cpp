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

// copied from QGIS
inline bool qgsDoubleNear( double a, double b, double epsilon = 4 * std::numeric_limits<double>::min() )
{
   const double diff = a - b;
   return diff > -epsilon && diff <= epsilon;
}

// copied from QGIS
static double /*QgsGeometryUtils::*/sqrDistToLine( double ptX, double ptY, double x1, double y1, double x2, double y2, double& minDistX, double& minDistY, double epsilon )
{
   minDistX = x1;
   minDistY = y1;

   double dx = x2 - x1;
   double dy = y2 - y1;

   if ( !qgsDoubleNear( dx, 0.0 ) || !qgsDoubleNear( dy, 0.0 ) )
   {
     double t = (( ptX - x1 ) * dx + ( ptY - y1 ) * dy ) / ( dx * dx + dy * dy );
     if ( t > 1 )
     {
       minDistX = x2;
       minDistY = y2;
     }
     else if ( t > 0 )
     {
       minDistX += dx * t ;
       minDistY += dy * t ;
     }
   }

   dx = ptX - minDistX;
   dy = ptY - minDistY;

   double dist = dx * dx + dy * dy;

   //prevent rounding errors if the point is directly on the segment
   if ( qgsDoubleNear( dist, 0.0, epsilon ) )
   {
     minDistX = ptX;
     minDistY = ptY;
     return 0.0;
   }

    return dist;
}

bool E2L_physicalToLogical(QPointF pA, QPointF pB, QPointF pP, double& lam)
{
  if (pA == pB)
    return false; // this is not a valid line!

  double vBA = QVector2D(pB-pA).length();
  double vPA = QVector2D(pP-pA).length();
  double vPB = QVector2D(pP-pB).length();
  double minx = vBA;
  double miny = vBA;
  double dist = sqrDistToLine(pP.x(), pP.y(), pA.x(), pA.y(), pB.x(), pB.y(), minx, miny, std::numeric_limits<double>::min());

  if (dist > vBA*0.05) {
      // not on line
      return false;
  }

  lam = vPA/(vPA+vPB);
  return true;
}

void E2L_centroid(QPointF pA, QPointF pB, double& cx, double& cy)
{
  cx = (pA.x() + pB.x())/2.;
  cy = (pA.y() + pB.y())/2.;
}
