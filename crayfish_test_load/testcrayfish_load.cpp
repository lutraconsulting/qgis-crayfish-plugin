#include <QString>
#include <QtTest>

#include "crayfish_viewer.h"
#include "crayfish_dataset.h"
#include "crayfish_output.h"

#define TEST_DIR "../test_data/"

class TestCrayfish_load : public QObject
{
  Q_OBJECT

public:

private Q_SLOTS:
  // load mesh
  void testLoadMissingMeshFile();
  void testLoadInvalidMeshFile();
  void testLoadValidMeshFile();

  // load dataset
  void testLoadMissingDataFile();
  void testLoadInvalidDataFile();
  void testLoadOldAsciiDataFile();
  void testLoadNewAsciiDataFile();
  void testLoadBinaryDataFile();
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

  QCOMPARE((int)s.nodeCount(), 0);
  QCOMPARE((int)s.elementCount(), 0);
  QCOMPARE(s.dataSetCount(), 0);
}

void TestCrayfish_load::testLoadValidMeshFile()
{
  CrayfishViewer s(TEST_DIR "quad_and_triangle.2dm");
  QVERIFY(s.loadedOk());
  QVERIFY(s.getLastError() == CrayfishViewer::Err_None);

  QCOMPARE((int)s.nodeCount(), 5);
  QCOMPARE((int)s.elementCount(), 2);
  QCOMPARE(s.dataSetCount(), 1);
  QVERIFY(s.dataSet(0));
  QCOMPARE(s.dataSet(0)->type(), DataSetType::Bed);
  QVERIFY(!s.dataSet(1));
}

void TestCrayfish_load::testLoadMissingDataFile()
{
  CrayfishViewer s(TEST_DIR "quad_and_triangle.2dm");
  QVERIFY(s.loadedOk());

  bool res = s.loadDataSet(TEST_DIR "missing_data_file.dat");
  QVERIFY(!res);
}

void TestCrayfish_load::testLoadInvalidDataFile()
{
  CrayfishViewer s(TEST_DIR "quad_and_triangle.2dm");
  QVERIFY(s.loadedOk());

  bool res = s.loadDataSet(TEST_DIR "not_a_data_file.dat");
  QVERIFY(!res);
}

void TestCrayfish_load::testLoadOldAsciiDataFile()
{
  CrayfishViewer s(TEST_DIR "quad_and_triangle.2dm");
  QVERIFY(s.loadedOk());

  bool res = s.loadDataSet(TEST_DIR "quad_and_triangle_ascii_old.dat");
  QVERIFY(res);

  QCOMPARE(s.dataSetCount(), 2);
  const DataSet* ds = s.dataSet(1);
  QVERIFY(ds);
  QCOMPARE(ds->type(), DataSetType::Scalar);

  QCOMPARE((int)ds->outputCount(), 2);
  QVERIFY(ds->output(0));
  QVERIFY(!ds->output(2));

  const Output* output = ds->output(1);
  QCOMPARE(output->time, 1.f);
  QCOMPARE(output->values[0], 6.f);
  QCOMPARE(output->values[4], 10.f);
}

void TestCrayfish_load::testLoadNewAsciiDataFile()
{
  CrayfishViewer s(TEST_DIR "quad_and_triangle.2dm");
  QVERIFY(s.loadedOk());

  bool res = s.loadDataSet(TEST_DIR "quad_and_triangle_ascii_new.dat");
  QVERIFY(res);

  QCOMPARE(s.dataSetCount(), 2);
  const DataSet* ds = s.dataSet(1);
  QVERIFY(ds);
  QCOMPARE(ds->type(), DataSetType::Scalar);

  QCOMPARE((int)ds->outputCount(), 2);
  QVERIFY(ds->output(0));
  QVERIFY(!ds->output(2));

  const Output* output = ds->output(1);
  QCOMPARE(output->time, 1.f);
  QCOMPARE(output->values[0], 6.f);
  QCOMPARE(output->values[4], 10.f);
}


void TestCrayfish_load::testLoadBinaryDataFile()
{
  CrayfishViewer s(TEST_DIR "quad_and_triangle.2dm");
  QVERIFY(s.loadedOk());

  bool res = s.loadDataSet(TEST_DIR "quad_and_triangle_binary.dat");
  QVERIFY(res);

  QCOMPARE(s.dataSetCount(), 2);
  const DataSet* ds = s.dataSet(1);
  QVERIFY(ds);
  QCOMPARE(ds->type(), DataSetType::Scalar);

  QCOMPARE((int)ds->outputCount(), 1);
  QVERIFY(ds->output(0));
  QVERIFY(!ds->output(1));

  const Output* output = ds->output(0);
  QCOMPARE(output->time, 0.f);
  QCOMPARE(output->values[0], 1.f);
  QCOMPARE(output->values[4], 5.f);
}


QTEST_APPLESS_MAIN(TestCrayfish_load)

#include "testcrayfish_load.moc"
