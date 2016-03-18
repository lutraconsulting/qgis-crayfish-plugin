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
