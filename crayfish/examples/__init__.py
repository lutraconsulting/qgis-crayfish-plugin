
import os
import crayfish

this_dir = os.path.dirname(os.path.realpath(__file__))
my_mesh_file = os.path.join(this_dir, 'example.2dm')
my_data_file = os.path.join(this_dir, 'example_depth.dat')

def load_example_mesh():
    mesh = crayfish.Mesh(my_mesh_file)
    mesh.load_data(my_data_file)
    return mesh
