"""
Python script that produces a cross section plot combining bed elevation and depth.
"""

import csv
from qgis.core import QgsGeometry, QgsPoint

import crayfish.plot

from . import load_example_mesh

# Load mesh and a results file
mesh = load_example_mesh()

# Get data for the plot
output_bed = mesh.dataset(0).output(0)  # bed elevation
output_dep = mesh.dataset(1).output(0)  # first output of second dataset
line_geometry = QgsGeometry.fromPolyline([QgsPoint(1000,1005), QgsPoint(1028,1005)])
x, y_bed = crayfish.plot.cross_section_plot_data(output_bed, line_geometry)
x, y_dep = crayfish.plot.cross_section_plot_data(output_dep, line_geometry)
# make derived array: y = bed elevation + depth
# so we can draw them together in a plot
y_bed_dep = [ yi_bed + yi_dep for yi_bed, yi_dep in zip(y_bed, y_dep) ]

# Export to CSV file
with open('/tmp/plot_data.csv', 'w') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(['x', 'bed', 'bed+depth'])
    for xi, yi_bed, yi_bed_dep in zip(x, y_bed, y_bed_dep):
        writer.writerow([xi, yi_bed, yi_bed_dep])

# Show plot
plt = crayfish.plot.show_plot(x, y_bed, pen=(0,0,0))
plt.plot(x, y_bed_dep, pen=(0,0,255))

# Export plot as an image
crayfish.plot.export_plot(plt, '/tmp/export-test.png')
