#ifndef CRAYFISH_E3T_H
#define CRAYFISH_E3T_H

class QPointF;

bool E3T_physicalToBarycentric(QPointF pA, QPointF pB, QPointF pC, QPointF pP, double& lam1, double& lam2, double& lam3);

void E3T_centroid(QPointF pA, QPointF pB, QPointF pC, double& cx, double& cy);


#endif // CRAYFISH_E3T_H
