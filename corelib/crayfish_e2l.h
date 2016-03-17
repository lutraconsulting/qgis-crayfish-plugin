#ifndef CRAYFISH_E2L_H
#define CRAYFISH_E2L_H

class QPointF;

bool E2L_physicalToBarycentric(QPointF pA, QPointF pB, QPointF pC, QPointF pP, double& lam1, double& lam2, double& lam3);

void E2L_centroid(QPointF pA, QPointF pB, QPointF pC, double& cx, double& cy);


#endif // CRAYFISH_E2L_H
