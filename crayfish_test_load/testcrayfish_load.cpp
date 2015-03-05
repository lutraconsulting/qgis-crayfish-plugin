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
  void testLoadIncompatibleBinaryDataFile();
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
  QCOMPARE(s.dataSet(0)->type(), DataSet::Bed);
  QVERIFY(!s.dataSet(1));
}

void TestCrayfish_load::testLoadMissingDataFile()
{
  CrayfishViewer s(TEST_DIR "quad_and_triangle.2dm");
  QVERIFY(s.loadedOk());

  bool res = s.loadDataSet(TEST_DIR "missing_data_file.dat");
  QVERIFY(!res);
  QVERIFY(s.getLastError() == CrayfishViewer::Err_FileNotFound);
}

void TestCrayfish_load::testLoadInvalidDataFile()
{
  CrayfishViewer s(TEST_DIR "quad_and_triangle.2dm");
  QVERIFY(s.loadedOk());

  bool res = s.loadDataSet(TEST_DIR "not_a_data_file.dat");
  QVERIFY(!res);
  QVERIFY(s.getLastError() == CrayfishViewer::Err_UnknownFormat);
}

void TestCrayfish_load::testLoadOldAsciiDataFile()
{
  CrayfishViewer s(TEST_DIR "quad_and_triangle.2dm");
  QVERIFY(s.loadedOk());

  bool res = s.loadDataSet(TEST_DIR "quad_and_triangle_ascii_old.dat");
  QVERIFY(res);
  QVERIFY(s.getLastError() == CrayfishViewer::Err_None);

  QCOMPARE(s.dataSetCount(), 2);
  const DataSet* ds = s.dataSet(1);
  QVERIFY(ds);
  QCOMPARE(ds->type(), DataSet::Scalar);

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
  QVERIFY(s.getLastError() == CrayfishViewer::Err_None);

  QCOMPARE(s.dataSetCount(), 2);
  const DataSet* ds = s.dataSet(1);
  QVERIFY(ds);
  QCOMPARE(ds->type(), DataSet::Scalar);

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
  QVERIFY(s.getLastError() == CrayfishViewer::Err_None);

  QCOMPARE(s.dataSetCount(), 2);
  const DataSet* ds = s.dataSet(1);
  QVERIFY(ds);
  QCOMPARE(ds->type(), DataSet::Scalar);

  QCOMPARE((int)ds->outputCount(), 1);
  QVERIFY(ds->output(0));
  QVERIFY(!ds->output(1));

  const Output* output = ds->output(0);
  QCOMPARE(output->time, 0.f);
  QCOMPARE(output->values[0], 1.f);
  QCOMPARE(output->values[4], 5.f);
}



void TestCrayfish_load::testLoadIncompatibleBinaryDataFile()
{
  // the mesh size (elements, nodes) is different from the data file

  CrayfishViewer s(TEST_DIR "quad_and_triangle.2dm");
  QVERIFY(s.loadedOk());

  bool res = s.loadDataSet(TEST_DIR "incompatible_data_binary.dat");
  QVERIFY(!res);
  QVERIFY(s.getLastError() == CrayfishViewer::Err_IncompatibleMesh);
}


QTEST_APPLESS_MAIN(TestCrayfish_load)

#include "testcrayfish_load.moc"
