
#include "crayfish_mesh.h"
#include "crayfish_dataset.h"

Mesh::Mesh(const Mesh::Nodes& nodes, const Mesh::Elements& elements)
  : mNodes(nodes)
  , mElems(elements)
{
}

Mesh::~Mesh()
{
  qDeleteAll(mDataSets);
}

int Mesh::elementCountForType(Element::Type type)
{
  int cnt = 0;
  for (int i = 0; i < mElems.count(); ++i)
  {
    if (mElems[i].eType == type)
      ++cnt;
  }
  return cnt;
}
