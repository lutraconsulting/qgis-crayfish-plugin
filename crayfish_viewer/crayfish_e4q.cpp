
#include <math.h>

#include "crayfish_viewer_global.h"

/*
Physical vs logical mapping of quads:
http://www.particleincell.com/blog/2012/quad-interpolation/
*/

void E4Q_computeMapping(Element& elem, E4Qtmp& e4q)
{
  e4q.a[0] = elem.p1->x;
  e4q.a[1] = - elem.p1->x + elem.p2->x;
  e4q.a[2] = - elem.p1->x + elem.p4->x;
  e4q.a[3] = elem.p1->x - elem.p2->x + elem.p3->x - elem.p4->x;

  e4q.b[0] = elem.p1->y;
  e4q.b[1] = - elem.p1->y + elem.p2->y;
  e4q.b[2] = - elem.p1->y + elem.p4->y;
  e4q.b[3] = elem.p1->y - elem.p2->y + elem.p3->y - elem.p4->y;
}

void E4Q_mapLogicalToPhysical(const E4Qtmp& e4q, double Lx, double Ly, double& Px, double& Py)
{
  Px = e4q.a[0] + e4q.a[1]*Lx + e4q.a[2]*Ly + e4q.a[3]*Lx*Ly;
  Py = e4q.b[0] + e4q.b[1]*Lx + e4q.b[2]*Ly + e4q.b[3]*Lx*Ly;
}

bool E4Q_mapPhysicalToLogical(const E4Qtmp& e4q, double x, double y, double& Lx, double& Ly)
{
  const double* a = e4q.a;
  const double* b = e4q.b;

  // compute quadratic equation
  double aa = a[3]*b[2] - a[2]*b[3];
  double bb = a[3]*b[0] -a[0]*b[3] + a[1]*b[2] - a[2]*b[1] + x*b[3] - y*a[3];
  double cc = a[1]*b[0] -a[0]*b[1] + x*b[1] - y*a[1];

  if (aa == 0)
    Ly = -cc / bb;  // linear equation
  else
  {
    double detSq = bb*bb - 4*aa*cc;
    if (detSq < 0)
      return false;
    Ly = (-bb+sqrt(detSq))/(2*aa);
  }

  Lx = (x-a[0]-a[2]*Ly) / (a[1]+a[3]*Ly);
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


bool E4Q_isComplex(const Element& e)
{
  // test crossing p1-p2 vs p3-p4
  double xA[4] = { e.p1->x, e.p2->x, e.p3->x, e.p4->x };
  double yA[4] = { e.p1->y, e.p2->y, e.p3->y, e.p4->y };
  if (lineSegmentIntersection(xA, yA))
    return true;

  // test crossing p2-p3 vs p1-p4
  double xB[4] = { e.p2->x, e.p3->x, e.p1->x, e.p4->x };
  double yB[4] = { e.p2->y, e.p3->y, e.p1->y, e.p4->y };
  if (lineSegmentIntersection(xB, yB))
    return true;

  return false;
}
