import sys
sys.path.append('..')
import crayfish
import unittest

TEST_DIR = os.path.join(os.path.dirname(__file__), 'data')

class TestCrayfishExport(unittest.TestCase):

  def test_export_raster(self):
      pass

if __name__ == '__main__':
  unittest.main()
