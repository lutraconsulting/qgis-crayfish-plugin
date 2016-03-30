"""
Python script that produces a time series plot.
"""

import csv
from qgis.core import QgsGeometry, QgsPoint

import crayfish.plot

from . import load_example_mesh

# Load mesh and a results file
mesh = load_example_mesh()

# Get data for the plot
dataset = mesh.dataset(1)  # second dataset (first one is bed elevation)
point_geometry = QgsGeometry.fromPoint(QgsPoint(1020,1001))
x, y = crayfish.plot.timeseries_plot_data(dataset, point_geometry)

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
