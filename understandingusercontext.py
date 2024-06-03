import bpy
new_scene = bpy.data.scenes.new('Another Scene')
bpy.context.window.scene = new_scene
print('The current scene is', bpy.context.scene.name)
new_layer = bpy.context.scene.view_layers.new('My Layer')
print('New layer created:', new_layer.name)
bpy.context.window.view_layer = new_layer
print('Current layer:', bpy.context.view_layer.name)
view_layer = bpy.context.view_layer
view_layer.objects.active = bpy.data.objects['Camera']
for ob in bpy.context.selected_objects:
    if ob is bpy.context.object:
        print(ob.name, 'is active, skipping')
        continue
    print(ob.name, 'is selected')
for ob in bpy.context.selected_objects:
    ob.select_set(False)
m_layer = bpy.context.scene.view_layers.new('Sel_Mesh')
c_layer = bpy.context.scene.view_layers.new('Sel_Cam')
for ob in bpy.data.objects:
    ob.select_set(ob.type == 'MESH', view_layer=m_layer)
    ob.select_set(ob.type == 'CAMERA', view_layer=c_layer)