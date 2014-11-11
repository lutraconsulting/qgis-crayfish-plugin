#include <QString>
#include <QtTest>

#include "crayfish_viewer.h"

#define TEST_DIR "../test_data/"

class TestCrayfish_load : public QObject
{
  Q_OBJECT

public:

private Q_SLOTS:
  void testLoadMissingMeshFile();
  void testLoadInvalidMeshFile();
  void testLoadValidMeshFile();
};

void TestCrayfish_load::testLoadMissingMeshFile()
{
  CrayfishViewer s(TEST_DIR "missing_mesh_file.2dm");
  QVERIFY(!s.loadedOk());
  QVERIFY(s.getLastError() == CrayfishViewer::Err_FileNotFound);
}

void TestCrayfish_load::testLoadInvalidMeshFile()
{
  CrayfishViewer s(TEST_DIR "not_a_mesh_file.2dm");
  QVERIFY(!s.loadedOk());
  QVERIFY(s.getLastError() == CrayfishViewer::Err_UnknownFormat);
}

void TestCrayfish_load::testLoadValidMeshFile()
{
  CrayfishViewer s(TEST_DIR "quad_and_triangle.2dm");
  QVERIFY(s.loadedOk());
  QVERIFY(s.getLastError() == CrayfishViewer::Err_None);

  QCOMPARE((int)s.nodeCount(), 5);
  QCOMPARE((int)s.elementCount(), 2);
}

QTEST_APPLESS_MAIN(TestCrayfish_load)

#include "testcrayfish_load.moc"
