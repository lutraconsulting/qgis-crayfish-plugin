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

#ifndef CRAYFISH_ELEMENT_H
#define CRAYFISH_ELEMENT_H

#include <QPointF>
#include <QVector>

class Element
{
public:
    enum Type
    {
      Undefined,
      ENP,
      E4Q,
      E3T,
      E2L
    };

    Element();
    ~Element();

    int nodeCount() const;
    bool isDummy() const;
    Type eType() const;
    uint p(int idx) const;
    int id() const;

    void setEType(Type eType);
    void setEType(Type eType, int node_count);
    void setP(int idx, uint val);
    void setP(uint* vals);
    void setId(int id);


private:
    int mId;        //!< just a reference to the ID in the input file (internally we use indices)
    Type mEType;
    QVector<uint> mP; //!< indices of nodes
};


#endif // CRAYFISH_ELEMENT_H
