"""
Python script that produces a cross section plot.
"""

import csv
from qgis.core import QgsGeometry, QgsPoint

import crayfish.plot

from . import load_example_mesh

# Load mesh and a results file
mesh = load_example_mesh()

# Get data for the plot
output = mesh.dataset(1).output(0)  # first output of second dataset
line_geometry = QgsGeometry.fromPolyline([QgsPoint(1000,1005), QgsPoint(1028,1005)])
x, y = crayfish.plot.cross_section_plot_data(output, line_geometry)

# Export to CSV file
with open('/tmp/plot_data.csv', 'w') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(['x', 'y'])
    for xi,yi in zip(x,y):
        writer.writerow([xi,yi])

# Show plot
plt = crayfish.plot.show_plot(x, y)

# Export plot as an image
crayfish.plot.export_plot(plt, '/tmp/export-test.png')
