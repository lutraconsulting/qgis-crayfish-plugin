import sys
sys.path.append('..')
import qgis.core # Fix sip.setapi(api, 2)
import crayfish
import crayfish.plot
import unittest
import os
import tempfile

TEST_DIR = os.path.join(os.path.dirname(__file__), 'data')



class TestCrayfishMeshCalculator(unittest.TestCase):
    def test_storm(self):
        # test if condition and some math operation
        m = crayfish.Mesh(TEST_DIR + "/MultiAscFiles/storm_20140819_1550.asc")
        ds0 = m.dataset(m.dataset_count()-1)

        time_filter = (-1, 3) #all times
        spatial_filter = (457960, 806545, 833378, 1204746) #all points
        handle, path = tempfile.mkstemp()
        os.close(handle)
        expression = " if ( \"storm_\" > 0.2, 2 * \"storm_\", (\"storm_\" ^ 2) - 2 + (2 / 2) )"
        res = m.create_derived_dataset(expression, time_filter, spatial_filter, True, path)
        self.assertTrue(res)

        m.load_data(path)
        ds = m.dataset(m.dataset_count()-1)

        self.assertEqual(ds0.output_count(), ds.output_count())
        for i in range(ds0.output_count()):
            o = ds.output(i)
            o0 = ds0.output(i)
            self.assertEqual(o.time(), o0.time())
            for val, val0 in zip(o.values(), o0.values()):
                if val0 != -9999.0:
                    if abs(val0 - 0.2) > 1e-4: # there are some inconsistencies what is greater
                                               # to what for float between C and python,
                                               # so take only relevant
                        if (val0 > 0.2):
                            self.assertTrue(abs(val - val0 * 2) < 1e-4, (val,  val0, val0* 2))
                        else:
                            self.assertTrue(abs(val - (val0*val0 - 2 + (2/2))) < 1e-4, (val,  val0, val0*val0 - 2 + (2/2)))
                else:
                    self.assertEqual(val, -9999.0)

    def test_storm_filter(self):
        # test if condition and some math operation
        m = crayfish.Mesh(TEST_DIR + "/MultiAscFiles/storm_20140819_1550.asc")
        ds0 = m.dataset(m.dataset_count() - 1)

        time_filter = (0.1, 3)  # skip time=0
        xmax = 60000
        ymax = 100000
        spatial_filter = (45796, xmax, 833378, ymax)
        handle, path = tempfile.mkstemp()
        os.close(handle)
        expression = "\"storm_\""
        res = m.create_derived_dataset(expression, time_filter, spatial_filter, True, path)
        self.assertTrue(res)

        m.load_data(path)
        ds = m.dataset(m.dataset_count() - 1)

        # output 0 in calculated dataset should match output 1 in original one
        self.assertEqual(ds0.output_count() - 1, ds.output_count())
        for i in range(ds0.output_count() - 1):
            o = ds.output(i)
            o0 = ds0.output(i + 1)

            self.assertEqual(o.time(), o0.time())
            j = 0
            for val, val0 in zip(o.values(), o0.values()):
                if val0 != -9999.0:
                    if i > 0:
                        node = m.node(j)
                        if node.x() < xmax - 1e-4 and node.y() < ymax - 1e-4:
                            self.assertTrue(abs(val - val0) < 1e-4, (val, val0))
                        else:
                            self.assertEqual(val, -9999.0) #filtered by position
                    else: # filered by time
                        self.assertEqual(val, -9999.0)  # filtered by position
                else:
                    self.assertEqual(val, -9999.0)

                j += 1

    def test_storm_filter_mask(self):
        m = crayfish.Mesh(TEST_DIR + "/NetCDF/indonesia_nc4.nc")
        ds0 = m.dataset(m.dataset_count() - 1)

        time_filter = (1008096, 100000000)
        handle, path = tempfile.mkstemp()
        os.close(handle)
        expression = "\"2 metre temperature\""
        mask_wkt = 'Polygon ((126.08338971583219745 13.63810893098781918, 184.83508119079834842 2.41348105548037495, 127.78839648173206456 -18.89910351826793544, 126.08338971583219745 13.63810893098781918))'
        res = m.create_derived_dataset_mask(expression, time_filter, mask_wkt, True, path)
        self.assertTrue(res)
        m.load_data(path)
        ds = m.dataset(m.dataset_count() - 1)

        # output 0 in calculated dataset should match output 1 in original one
        self.assertEqual(ds0.output_count() - 1, ds.output_count())
        for i in range(ds0.output_count() - 1):
            o = ds.output(i)
            o0 = ds0.output(i + 1)

            self.assertEqual(o.time(), o0.time())
            j = 0
            for val, val0 in zip(o.values(), o0.values()):
                node = m.node(j)
                if node.x() < 127: # filter by mask position
                    self.assertEqual(val, -9999.0)
                else:
                    self.assertEqual(val, val0)
                j += 1

if __name__ == '__main__':
  unittest.main()
