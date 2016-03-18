#include "crayfish_element.h"
#include "crayfish_e2l.h"
#include "crayfish_e3t.h"
#include "crayfish_e4q.h"
#include "crayfish_eNp.h"

Element::Element(): mEType(Undefined), mP(4) {}
Element::~Element() {}

int Element::nodeCount() const { return mP.size(); }
bool Element::isDummy() const { return mEType == Undefined; }
Element::Type Element::eType() const {return mEType;}

void Element::setEType(Type eType) {
    Q_ASSERT(eType != ENP);
    switch (eType) {
        case E4Q : setEType(eType, 4); break;
        case E3T : setEType(eType, 3); break;
        case E2L : setEType(eType, 2); break;
        default: setEType(eType, 0);
    }
}
void Element::setEType(Type eType, int node_count) {
    mEType = eType;
    mP.resize(node_count);
}
uint Element::p(int idx) const {Q_ASSERT(idx < nodeCount()); return mP[idx];}
void Element::setP(int idx, uint val) {Q_ASSERT(idx < nodeCount()); mP[idx] = val;}
void Element::setP(uint* vals) {for (int i=0; i<nodeCount(); i++) {mP[i] = vals[i];}}
void Element::setId(int id) {mId = id;}
int Element::id() const {return mId;}
