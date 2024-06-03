import bpy
from bpy import data as D
from bpy import context as C
from mathutils import *
from math import *

bpy.ops.object.delete(use_global=False)
bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=2, enter_editmode=False, align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))
bpy.ops.mesh.primitive_uv_sphere_add(radius=1, enter_editmode=False, align='WORLD', location=(0, 0, 2), scale=(1, 1, 1))
