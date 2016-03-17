#include "crayfish_e2l.h"

#include <QPointF>
#include <QVector2D>

bool E2L_physicalToBarycentric(QPointF pA, QPointF pB, QPointF pC, QPointF pP, double& lam1, double& lam2, double& lam3)
{
  if (pA == pB || pA == pC || pB == pC)
    return false; // this is not a valid triangle!

  // Compute vectors
  QVector2D v0( pC - pA );
  QVector2D v1( pB - pA );
  QVector2D v2( pP - pA );

  // Compute dot products
  double dot00 = QVector2D::dotProduct(v0, v0);
  double dot01 = QVector2D::dotProduct(v0, v1);
  double dot02 = QVector2D::dotProduct(v0, v2);
  double dot11 = QVector2D::dotProduct(v1, v1);
  double dot12 = QVector2D::dotProduct(v1, v2);

  // Compute barycentric coordinates
  double invDenom = 1.0 / (dot00 * dot11 - dot01 * dot01);
  lam1 = (dot11 * dot02 - dot01 * dot12) * invDenom;
  lam2 = (dot00 * dot12 - dot01 * dot02) * invDenom;
  lam3 = 1.0 - lam1 - lam2;

  // Return if POI is outside triangle
  if( (lam1 < 0) || (lam2 < 0) || (lam3 < 0) ){
    return false;
  }

  return true;
}

void E2L_centroid(QPointF pA, QPointF pB, QPointF pC, double& cx, double& cy)
{
  cx = (pA.x() + pB.x() + pC.x())/3.;
  cy = (pA.y() + pB.y() + pC.y())/3.;
}
