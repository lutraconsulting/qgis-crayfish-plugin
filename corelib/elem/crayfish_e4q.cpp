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

#include <math.h>

#include "crayfish_e4q.h"





void E4QNormalization::init(const BBox& extent)
{
    x0 = extent.minX;
    y0 = extent.minY;
    range_x = extent.maxX - extent.minX;
    range_y = extent.maxY - extent.minY;
}

double E4QNormalization::normX(double x) const
{
    return (x-x0)/range_x;
}

double E4QNormalization::normY(double y) const
{
    return (y-y0)/range_y;
}

double E4QNormalization::realX(double x) const
{
    return x*range_x + x0;
}

double E4QNormalization::realY(double y) const
{
    return y*range_y + y0;
}

bool E4Q_isValid(const Element& elem, Node* nodes)
{
    // It may not be valid for several reasons, e.g
    // lines are on line , so it is triangle with 4 vertexes
    E4Qtmp e4q;
    E4QNormalization norm;
    E4Q_computeMapping(elem, e4q, nodes, norm);
    double Lx, Ly;
    return E4Q_mapPhysicalToLogical(e4q, 0.5, 0.5, Lx, Ly, norm);
}

/*
Physical vs logical mapping of quads:
http://www.particleincell.com/blog/2012/quad-interpolation/
*/

void E4Q_computeMapping(const Element& elem, E4Qtmp& e4q, const Node* nodes, const E4QNormalization& norm)
{
  Q_ASSERT(elem.eType() == Element::E4Q);

  const Node& n1 = nodes[elem.p(0)];
  const Node& n2 = nodes[elem.p(1)];
  const Node& n3 = nodes[elem.p(2)];
  const Node& n4 = nodes[elem.p(3)];

  double n1x = norm.normX(n1.x);
  double n2x = norm.normX(n2.x);
  double n3x = norm.normX(n3.x);
  double n4x = norm.normX(n4.x);

  double n1y = norm.normY(n1.y);
  double n2y = norm.normY(n2.y);
  double n3y = norm.normY(n3.y);
  double n4y = norm.normY(n4.y);

  e4q.a[0] = n1x;
  e4q.a[1] = - n1x + n2x;
  e4q.a[2] = - n1x + n4x;
  e4q.a[3] = n1x - n2x + n3x - n4x;

  e4q.b[0] = n1y;
  e4q.b[1] = - n1y + n2y;
  e4q.b[2] = - n1y + n4y;
  e4q.b[3] = n1y - n2y + n3y - n4y;
}

void E4Q_mapLogicalToPhysical(const E4Qtmp& e4q, double Lx, double Ly, double& Px, double& Py, const E4QNormalization& norm)
{
  Px = e4q.a[0] + e4q.a[1]*Lx + e4q.a[2]*Ly + e4q.a[3]*Lx*Ly;
  Py = e4q.b[0] + e4q.b[1]*Lx + e4q.b[2]*Ly + e4q.b[3]*Lx*Ly;

  Px = norm.realX(Px);
  Py = norm.realY(Py);
}

static inline double iszero(double val, double eps=1e-30)
{
    return fabs(val) < eps;
}

bool E4Q_mapPhysicalToLogical(const E4Qtmp& e4q, double x, double y, double& Lx, double& Ly, const E4QNormalization& norm)
{
  const double* a = e4q.a;
  const double* b = e4q.b;

  x = norm.normX(x);
  y = norm.normY(y);

  if (iszero(a[3])) {
    if (iszero(a[2])) {
        if (iszero(a[1])) {
            return false;
        } else {
            Lx = (x - a[0])/a[1];
            double denom = b[2] + b[3]*Lx;
            if (iszero(denom)) {
                return false;
            } else {
                Ly = (y - b[0] - b[1]*Lx) / denom;
                return true;
            }
        }
    } else {
        if (iszero(a[1])) {
            Ly = (x - a[0])/a[2];
            double denom = b[1] + b[3]*Ly;
            if (iszero(denom)) {
                return false;
            } else {
                Lx = (y - b[0] - b[2]*Ly) / denom;
                return true;
            }
        }
    }
  }

  // compute quadratic equation
  double aa = a[3]*b[2] - a[2]*b[3];
  double bb = a[3]*b[0] - a[0]*b[3] + a[1]*b[2] - a[2]*b[1] + x*b[3] - y*a[3];
  double cc = a[1]*b[0] - a[0]*b[1] + x*b[1] - y*a[1];

  if (iszero(aa))
    Ly = -cc / bb;  // linear equation
  else
  {
    double detSq = bb*bb - 4*aa*cc;
    if (detSq < 0)
      return false;
    Ly = (-bb+sqrt(detSq))/(2*aa);
  }

  double denom = (a[1]+a[3]*Ly);
  if (iszero(denom)) {
    if (iszero(a[3])) {
        return false;
    } else {
        Ly = -a[1]/a[3];
        denom = (b[1] + b[3]*Ly);
        if (iszero(denom)) {
            return false;
        } else {
            Lx = (y-b[0]-b[2]*Ly) / denom;
        }
    }
  } else
  {
    Lx = (x-a[0]-a[2]*Ly) / denom;
  }
  return true;
}



bool lineIntersection(double x[], double y[], double& Px, double& Py)
{

  double K = (x[0]*y[1]-y[0]*x[1]);
  double L = (x[2]*y[3]-y[2]*x[3]);
  double M = (x[0]-x[1])*(y[2]-y[3]) - (y[0]-y[1])*(x[2]-x[3]);
  if (M == 0)
    return false;

  Px = ( K*(x[2]-x[3]) - L*(x[0]-x[1]) ) / M;
  Py = ( K*(y[2]-y[3]) - L*(y[0]-y[1]) ) / M;
  return true;
}


inline bool isInRange(double a1, double a2, double x)
{
  return (x >= a1 && x <= a2) || (x >= a2 && x <= a1);
}


bool lineSegmentIntersection(double x[], double y[])
{
  double Px, Py;
  if (!lineIntersection(x, y, Px, Py))
    return false;

  if (!isInRange(x[0], x[1], Px) || !isInRange(y[0], y[1], Py))
    return false;

  if (!isInRange(x[2], x[3], Px) || !isInRange(y[2], y[3], Py))
    return false;

  return true;
}


bool E4Q_isComplex(const Element& elem, Node* nodes)
{
  const Node& n1 = nodes[elem.p(0)];
  const Node& n2 = nodes[elem.p(1)];
  const Node& n3 = nodes[elem.p(2)];
  const Node& n4 = nodes[elem.p(3)];

  // test crossing p1-p2 vs p3-p4
  double xA[4] = { n1.x, n2.x, n3.x, n4.x };
  double yA[4] = { n1.y, n2.y, n3.y, n4.y };
  if (lineSegmentIntersection(xA, yA))
    return true;

  // test crossing p2-p3 vs p1-p4
  double xB[4] = { n2.x, n3.x, n1.x, n4.x };
  double yB[4] = { n2.y, n3.y, n1.y, n4.y };
  if (lineSegmentIntersection(xB, yB))
    return true;

  return false;
}

void E4Q_centroid(const E4Qtmp& e4q, double& cx, double& cy, const E4QNormalization& norm )
{
  E4Q_mapLogicalToPhysical(e4q, 0.5, 0.5, cx, cy, norm);
}
