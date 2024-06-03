import bpy
my_empty = bpy.data.objects.new('My Empty', None)
print('New Empty created:', my_empty)
bpy.data.collections['Collection'].objects.link(my_empty)
bpy.data.objects.remove(my_empty)
collection = bpy.data.collections['Collection']
collection.objects.unlink(bpy.data.objects['Cube'])