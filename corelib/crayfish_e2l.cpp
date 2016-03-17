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
