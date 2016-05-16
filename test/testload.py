
import sys
sys.path.append('..')
import crayfish
import crayfish.plot
import unittest
import os

from qgis.core import QgsGeometry

TEST_DIR = os.path.join(os.path.dirname(__file__), 'data')


class TestCrayfishLoad(unittest.TestCase):

  def test_load_missing_mesh_file(self):
    with self.assertRaises(ValueError):
      m = crayfish.Mesh(TEST_DIR + "/missing_mesh_file.2dm")
    # TODO: test it returns "file not found"

  def test_load_invalid_mesh_file(self):
    with self.assertRaises(ValueError):
      m = crayfish.Mesh(TEST_DIR + "/not_a_mesh_file.2dm")
    # TODO: test it returns "unknown format"

  def test_load_valid_mesh_file(self):
    m = crayfish.Mesh(TEST_DIR + "/quad_and_triangle.2dm")
    self.assertTrue(m is not None)
    self.assertEqual(m.node_count(), 5)
    self.assertEqual(m.element_count(), 2)
    self.assertEqual(m.dataset_count(), 1)
    self.assertEqual(m.dataset(0).type(), crayfish.DS_Bed)
    with self.assertRaises(ValueError):
      m.dataset(1)

  def test_e4q_with_reprojection(self):
    # reprojected quad mesh issue #143
    m = crayfish.Mesh(TEST_DIR + "/e4q.2dm")
    self.assertTrue(m is not None)
    self.assertEqual(m.node_count(), 4)
    self.assertEqual(m.element_count(), 1)
    self.assertEqual(m.dataset_count(), 1)
    self.assertEqual(m.dataset(0).type(), crayfish.DS_Bed)
    o = m.dataset(0).output(0)
    val = m.value(o, -2, 0.5)
    self.assertEqual(val, 0.5)

    # reproject to see if the interpolation works in OTF too!
    m.set_source_crs("+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs")
    m.set_destination_crs("+proj=merc +a=6378137 +b=6378137 +lat_ts=0.0 +lon_0=0.0 +x_0=0.0 +y_0=0 +k=1.0 +units=m +nadgrids=@null +wktext  +no_defs") #Web Mercator
    val = m.value(o, -221164, 26333)
    self.assertEqual(val, 0.49337500748505414)

  def test_e4q2(self):
    # mesh with very small elements issue #188
    m = crayfish.Mesh(TEST_DIR + "/e4q2.2dm")
    self.assertTrue(m is not None)
    self.assertEqual(m.node_count(), 6)
    self.assertEqual(m.element_count(), 2)
    self.assertEqual(m.dataset_count(), 1)
    self.assertEqual(m.dataset(0).type(), crayfish.DS_Bed)
    o = m.dataset(0).output(0)

    x0 = 1.53033321e+002
    x1 = 1.53033159e+002
    y0 = -2.68736877e+001
    y1 = -2.68742438e+001

    # We have 2 elements, lets test that all points on diagonal are not NaN
    # Do not test edges
    for i in range(1,10):
        x = x1 + (x0-x1)*i/10.0
        y = y0 + (y1-y0)*i/10.0
        val = m.value(o, x, y)
        self.assertTrue(val != -9999, msg="{}, {} is -9999".format(x, y))

  def test_load_missing_data_file(self):
    m = crayfish.Mesh(TEST_DIR + "/quad_and_triangle.2dm")
    with self.assertRaises(ValueError):
      m.load_data(TEST_DIR + "/missing_data_file.dat")
    # TODO: test it returns "file not found"

  def test_load_invalid_data_file(self):
    m = crayfish.Mesh(TEST_DIR + "/quad_and_triangle.2dm")
    with self.assertRaises(ValueError):
      m.load_data(TEST_DIR + "/not_a_data_file.dat")
    # TODO: test it returns "unknown format"

  def test_load_old_ascii_data_file(self):
    m = crayfish.Mesh(TEST_DIR + "/quad_and_triangle.2dm")
    m.load_data(TEST_DIR + "/quad_and_triangle_ascii_old.dat")
    self.assertEqual(m.dataset_count(), 2)
    ds = m.dataset(1)
    self.assertEqual(ds.type(), crayfish.DS_Scalar)
    self.assertEqual(ds.output_count(), 2)
    o = ds.output(1)
    with self.assertRaises(ValueError):
      o2 = ds.output(2)
    self.assertEqual(o.time(), 1.)
    self.assertEqual(o.value(0), 6.)
    self.assertEqual(o.value(4), 10.)

  def test_load_new_ascii_data_file(self):
    m = crayfish.Mesh(TEST_DIR + "/quad_and_triangle.2dm")
    m.load_data(TEST_DIR + "/quad_and_triangle_ascii_new.dat")
    self.assertEqual(m.dataset_count(), 2)
    ds = m.dataset(1)
    self.assertEqual(ds.type(), crayfish.DS_Scalar)
    self.assertEqual(ds.output_count(), 2)
    o = ds.output(1)
    with self.assertRaises(ValueError):
      o2 = ds.output(2)
    self.assertEqual(o.time(), 1.)
    self.assertEqual(o.value(0), 6.)
    self.assertEqual(o.value(4), 10.)

  def test_load_binary_data_file(self):
    m = crayfish.Mesh(TEST_DIR + "/quad_and_triangle.2dm")
    m.load_data(TEST_DIR + "/quad_and_triangle_binary.dat")
    self.assertEqual(m.dataset_count(), 2)
    ds = m.dataset(1)
    self.assertEqual(ds.type(), crayfish.DS_Scalar)
    self.assertEqual(ds.output_count(), 1)
    o = ds.output(0)
    with self.assertRaises(ValueError):
      o2 = ds.output(1)
    self.assertEqual(o.time(), 0.)
    self.assertEqual(o.value(0), 1.)
    self.assertEqual(o.value(4), 5.)

  def test_load_element_centered_data(self):
    m = crayfish.Mesh(TEST_DIR + "/quad_and_triangle.2dm")
    m.load_data(TEST_DIR + "/quad_and_triangle_ascii_els_depth.dat")
    self.assertEqual(m.dataset_count(), 2)
    ds = m.dataset(1)
    self.assertEqual(ds.type(), crayfish.DS_Scalar)
    self.assertEqual(ds.output_count(), 2)
    o = ds.output(1)
    with self.assertRaises(ValueError):
      o2 = ds.output(2)
    self.assertEqual(o.time(), 1.)
    self.assertEqual(o.value(0), 3.)
    self.assertEqual(o.value(1), 4.)

  def test_load_grib_scalar_data_file(self):
    m = crayfish.Mesh(TEST_DIR + "/Madagascar.wave.7days.grb")
    self.assertEqual(m.dataset_count(), 3)
    ds = m.dataset(0)
    self.assertEqual(ds.type(), crayfish.DS_Scalar)
    self.assertEqual(ds.output_count(), 27)
    o = ds.output(0)
    self.assertEqual(o.time(), 5.973333358764648) # forecast 7 days/6hours
    self.assertEqual(o.value(0), -9999.0) #nodata
    self.assertEqual(o.value(1600), 15.34000015258789)

  def test_load_grib_vector_data_file(self):
    m = crayfish.Mesh(TEST_DIR + "/Madagascar.wind.7days.grb")
    self.assertEqual(m.dataset_count(), 1)
    ds = m.dataset(0)
    self.assertEqual(ds.type(), crayfish.DS_Vector)
    self.assertEqual(ds.output_count(), 27)
    o = ds.output(0)
    self.assertEqual(o.time(), 5.973333358764648) # forecast 7 days/6hours
    self.assertEqual(o.value(1600), 9.666419982910156)

  def test_load_netCFD_data_file(self):
    m = crayfish.Mesh("NETCDF:\"" + TEST_DIR + "/indonesia.nc\":tcc")
    self.assertEqual(m.dataset_count(), 1)
    ds = m.dataset(0)
    self.assertEqual(ds.type(), crayfish.DS_Scalar)
    self.assertEqual(ds.output_count(), 31)
    o = ds.output(0)
    self.assertEqual(o.time(), 1008072.0)
    self.assertEqual(o.value(1), 22952.0)

  def test_load_hec2d_file(self):
    m = crayfish.Mesh(TEST_DIR + "/test.p01.hdf")
    self.assertEqual(m.dataset_count(), 8)

    self.assertEqual(m.dataset(0).type(), crayfish.DS_Bed)
    self.assertEqual(m.dataset(1).type(), crayfish.DS_Scalar)

    ds = m.dataset(1)
    self.assertEqual(ds.output_count(), 41)
    o = ds.output(0)
    self.assertEqual(o.time(), 0.0)
    self.assertEqual(o.value(1), 9.699999809265137)

  def test_load_hec2d_file_2areas(self):
    m = crayfish.Mesh(TEST_DIR + "/baldeagle_multi2d.hdf")
    self.assertEqual(m.dataset_count(), 8)

    self.assertEqual(m.dataset(0).type(), crayfish.DS_Bed)
    self.assertEqual(m.dataset(1).type(), crayfish.DS_Scalar)

    ds = m.dataset(1)
    self.assertEqual(ds.output_count(), 7)
    o = ds.output(5)
    self.assertEqual(o.time(), 2.5)
    self.assertEqual(o.value(100), 606.6416015625)
    self.assertEqual(o.value(700), 655.0142211914062)

  def test_value_at_of_two_triangles(self):
    def test_cross_section(geometry, o, expect, msg):
        x,y = crayfish.plot.cross_section_plot_data(o, geometry)
        for xi, yi in zip (x, y):
            self.assertEqual(str(yi) != "nan", expect, "{} Point {} is {}, expected {}".format(msg, xi, yi, expect))

    m = crayfish.Mesh(TEST_DIR + "/2triangle.2dm")
    m.load_data(TEST_DIR + "/2triangle_ascii_els_depth.dat")
    self.assertEqual(m.dataset_count(), 2)
    ds = m.dataset(1)
    self.assertEqual(ds.type(), crayfish.DS_Scalar)
    self.assertEqual(ds.output_count(), 2)
    o = ds.output(1)

    # geometry on the border of the 2 triagles
    geometry = QgsGeometry.fromWkt("LINESTRING (1050 2000, 2000 950)")
    test_cross_section(geometry, o, True, "border")

    # other diagonal
    geometry = QgsGeometry.fromWkt("LINESTRING (1000 1000, 1950 2050)")
    test_cross_section(geometry, o, True, "diag")

    # outside
    geometry = QgsGeometry.fromWkt("LINESTRING (975 1000, 950 1925)")
    test_cross_section(geometry, o, False, "outside")

if __name__ == '__main__':
  unittest.main()
