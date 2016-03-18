#ifndef CRAYFISH_E2L_H
#define CRAYFISH_E2L_H

class QPointF;

bool E2L_physicalToLogical(QPointF pA, QPointF pB, QPointF pP, double& lam);

void E2L_centroid(QPointF pA, QPointF pB, double& cx, double& cy);


#endif // CRAYFISH_E2L_H
