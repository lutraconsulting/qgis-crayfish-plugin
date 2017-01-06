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

#include "crayfish_element.h"

Element::Element(): mEType(Undefined), mP(4) {}
Element::~Element() {}

int Element::nodeCount() const {
  return mP.size();
}
bool Element::isDummy() const {
  return mEType == Undefined;
}
Element::Type Element::eType() const {
  return mEType;
}

void Element::setEType(Type eType) {
  Q_ASSERT(eType != ENP);
  switch (eType) {
  case E4Q :
    setEType(eType, 4);
    break;
  case E3T :
    setEType(eType, 3);
    break;
  case E2L :
    setEType(eType, 2);
    break;
  default:
    setEType(eType, 0);
  }
}
void Element::setEType(Type eType, int node_count) {
  mEType = eType;
  mP.resize(node_count);
}
uint Element::p(int idx) const {
  Q_ASSERT(idx < nodeCount());
  return mP[idx];
}
void Element::setP(int idx, uint val) {
  Q_ASSERT(idx < nodeCount());
  mP[idx] = val;
}
void Element::setP(uint* vals) {
  for (int i=0; i<nodeCount(); i++) {
    mP[i] = vals[i];
  }
}
void Element::setId(int id) {
  mId = id;
}
int Element::id() const {
  return mId;
}
