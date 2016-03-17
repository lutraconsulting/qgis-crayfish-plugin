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


#include "crayfish_e5p.h"

#include "math.h"
#include <QPointF>

#include <QVector3D>
#include <QVector2D>
#include <limits>

static double E5P_contangent(QPointF a, QPointF b, QPointF c) {
    QVector3D ba (b-a);
    QVector3D bc (b-c);

    double dp = QVector3D::dotProduct(bc, ba);
    QVector3D cp = QVector3D::crossProduct(bc, ba);

    return dp/cp.length();
}

bool E5P_physicalToLogical(const QVector<QPointF>& pX, QPointF pP, QVector<double>& lam)
{
    if (pX.size() < 3 || pX.size() != lam.size())
        return false;

    double weightSum = 0;
    QVector<QPointF>::const_iterator prev = pX.end();
    QVector<QPointF>::const_iterator next = pX.begin();

    QVector<double>::iterator lamit=lam.begin();
    for (QVector<QPointF>::const_iterator it=pX.begin(); it!=pX.end(); ++it, ++lamit)
    {
        double cotPrev = E5P_contangent(pP, *it, *prev);
        double cotNext = E5P_contangent(pP, *it, *next);
        double len2 = QVector2D(*it - pP).lengthSquared();
        double val = (cotPrev + cotNext) / len2;
        *lamit = val;
        prev = it;
    }

    for (QVector<double>::iterator lamit=lam.begin(); lamit!=lam.end(); ++lamit)
    {
        *lamit = (*lamit)/weightSum;
    }

    return true;
}

void E5P_centroid(const QVector<QPointF>& pX, double& cx, double& cy)
{
    cx = 0;
    cy = 0;

    if (pX.isEmpty())
        return;

    for (QVector<QPointF>::const_iterator it=pX.begin(); it!=pX.end(); ++it)
    {
        cx += it->x();
        cy += it->y();
    }

    cx /= pX.size();
    cy /= pX.size();
}
