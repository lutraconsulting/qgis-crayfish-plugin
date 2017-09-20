import sys
import os
import shutil
sys.path.append('..')
import qgis.core # Fix sip.setapi(api, 2)

import crayfish
import unittest
import tempfile
import numpy
from osgeo import gdal, ogr

TEST_DIR = os.path.join(os.path.dirname(__file__), 'data')
RENDER_DIR = os.path.join(TEST_DIR, 'render')
PERSIST_DATA = False


def tmp_dir():
    if not PERSIST_DATA:
        return tempfile.mkdtemp()
    else:
        tmp_dir = os.path.join(TEST_DIR, "tmp_output")
        return tmp_dir


class TestCrayfishExport(unittest.TestCase):
    def compare_vectors(self, shp1, shp2):
        driver = ogr.GetDriverByName("ESRI Shapefile")

        ds1 = driver.Open(shp1, 0)
        self.assertTrue(ds1 is not None)
        l1 = ds1.GetLayer()
        self.assertTrue(l1 is not None)

        ds2 = driver.Open(shp2, 0)
        self.assertTrue(ds2 is not None)
        l2 = ds2.GetLayer()
        self.assertTrue(l2 is not None)

        self.assertEqual(l1.GetFeatureCount(), l2.GetFeatureCount())

        for f1, f2 in zip(l1, l2):
            attr1 = f1.GetField("CVAL")
            attr2 = f2.GetField("CVAL")
            self.assertEqual(attr1, attr2)

            geom1 = f1.GetGeometryRef()
            self.assertTrue(geom1 is not None)
            geom2 = f2.GetGeometryRef()
            self.assertTrue(geom2 is not None)

            self.assertTrue(geom1.Equals(geom2))

    def compare_rasters(self, raster1, raster2):
        ds1 = gdal.Open(raster1)
        ds2 = gdal.Open(raster2)
        self.assertTrue(ds1 is not None)
        self.assertTrue(ds2 is not None)

        r1 = numpy.array(ds1.ReadAsArray())
        r2 = numpy.array(ds2.ReadAsArray())
        self.assertTrue(numpy.array_equal(r1,r2))

    def load_4quads(self):
        m = crayfish.Mesh(TEST_DIR + "/4quads.2dm")
        self.assertTrue(m is not None)
        self.assertEqual(m.node_count(), 9)
        self.assertEqual(m.element_count(), 4)
        self.assertEqual(m.dataset_count(), 1)
        self.assertEqual(m.dataset(0).type(), crayfish.DS_Bed)
        return m.dataset(0).output(0)

    def export_grid(self, output, mupp, wkt=""):
        tmpdir = tmp_dir()
        renderedFile = os.path.join(tmpdir, "4quads.tif")
        res = output.export_grid(mupp, renderedFile, wkt)
        self.assertTrue(res)
        return renderedFile

    def export_contours(self, output, mupp, useLines, interval=-1, proj4wkt="", suffix=""):
        cm = None
        if interval == -1:
            zMin, zMax = output.z_range()
            cm = crayfish.ColorMap(zMin, zMax) # default color map

        tmpdir = tmp_dir()
        renderedFile = os.path.join(tmpdir, "4quads" + suffix + ".shp")
        print renderedFile
        res = output.export_contours(mupp, interval, renderedFile, proj4wkt, useLines, cm)
        self.assertTrue(res)
        return renderedFile

    def test_export_raster(self):
        output = self.load_4quads()
        renderedFile = self.export_grid(output, 1.0)
        baseFile = os.path.join(RENDER_DIR, "4quads.tif")
        self.compare_rasters(baseFile, renderedFile)

    def test_export_contour_lines_interval(self):
        output = self.load_4quads()
        renderedFile = self.export_contours(output, 0.25, useLines=True, interval=0.5, suffix="_li")
        baseFile = os.path.join(RENDER_DIR, "4quads_li.shp")
        self.compare_vectors(baseFile, renderedFile)

    def test_export_contour_areas_interval(self):
        output = self.load_4quads()
        renderedFile = self.export_contours(output, 0.25, useLines=False, interval=0.5, suffix="_ai")
        baseFile = os.path.join(RENDER_DIR, "4quads_ai.shp")
        self.compare_vectors(baseFile, renderedFile)

    def test_export_contour_lines_colormap(self):
        output = self.load_4quads()
        renderedFile = self.export_contours(output, 0.25, useLines=True, suffix="_lc")
        baseFile = os.path.join(RENDER_DIR, "4quads_lc.shp")
        self.compare_vectors(baseFile, renderedFile)

    def test_export_contour_areas_colormap(self):
        output = self.load_4quads()
        renderedFile = self.export_contours(output, 0.25, useLines=False, suffix="_ac")
        baseFile = os.path.join(RENDER_DIR, "4quads_ac.shp")
        self.compare_vectors(baseFile, renderedFile)

if __name__ == '__main__':
  unittest.main()
