import bpy
from bpy import data as D
from bpy import context as C

len(bpy.data.objects)
bpy.data.objects[0]

import bpy
for ob in bpy.data.objects:
    print(ob.name, ob.type)

import bpy
for i, ob in enumerate(bpy.data.objects):
    print(i, ob.name, ob.type)

import bpy
bpy.data.objects[0].name ='z' + bpy.data.objects[0].name

import bpy
for ob in bpy.data.objects:
    ob.name ='z' + ob.name

import bpy
for ob in list(bpy.data.objects):
    ob.name = 'z' + ob.name

for name in bpy.data.objects.keys():
    print(name)

for ob in bpy.data.objects.values():
    print(ob.name, ob.type)

for name, ob in bpy.data.objects.items():
    print(name, ob.type)
