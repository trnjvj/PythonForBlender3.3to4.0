import random
import time
import math

import bpy

def purge_orphans():
    if bpy.app.version >= (3, 0, 0):
        bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)
    else:
        result = bpy.ops.outliner.orphans_purge()
        if result.pop() != "CANCELLED":
            purge_orphans()

def clean_scene():
    if bpy.context.active_object and bpy.context.active_object.mode == "EDIT":
        bpy.ops.object.editmode_toggle()
    for obj in bpy.data.objects:
        obj.hide_set(False)
        obj.hide_select = False
        obj.hide_viewport = False
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()
    collection_names = [col.name for col in bpy.data.collections]
    for name in collection_names:
        bpy.data.collections.remove(bpy.data.collections[name])
    world_names = [world.name for world in bpy.data.worlds]
    for name in world_names:
        bpy.data.worlds.remove(bpy.data.worlds[name])
    bpy.ops.world.new()
    bpy.context.scene.world = bpy.data.worlds["World"]
    purge_orphans()

def active_object():
    return bpy.context.active_object

def time_seed():
    seed = time.time()
    print(f"seed: {seed}")
    random.seed(seed)
    bpy.context.window_manager.clipboard = str(seed)
    return seed

def add_ctrl_empty(name=None):
    bpy.ops.object.empty_add(type="PLAIN_AXES", align="WORLD")
    empty_ctrl = active_object()
    if name:
        empty_ctrl.name = name
    else:
        empty_ctrl.name = "empty.cntrl"
    return empty_ctrl

def apply_material(material):
    obj = active_object()
    obj.data.materials.append(material)

def make_active(obj):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


def track_empty(obj):
    empty = add_ctrl_empty(name=f"empty.tracker-target.{obj.name}")
    make_active(obj)
    bpy.ops.object.constraint_add(type="TRACK_TO")
    bpy.context.object.constraints["Track To"].target = empty
    return empty

def setup_camera(loc, rot):
    bpy.ops.object.camera_add(location=loc, rotation=rot)
    camera = active_object()
    bpy.context.scene.camera = camera
    camera.data.lens = 70
    camera.data.passepartout_alpha = 0.9
    empty = track_empty(camera)
    return empty

def set_1080px_square_render_res():
    bpy.context.scene.render.resolution_x = 1080
    bpy.context.scene.render.resolution_y = 1080

def make_fcurves_linear():
    for fcurve in bpy.context.active_object.animation_data.action.fcurves:
        for points in fcurve.keyframe_points:
            points.interpolation = "LINEAR"

def get_random_color():
    return random.choice(
        [
            [0.984375, 0.4609375, 0.4140625, 1.0],
            [0.35546875, 0.515625, 0.69140625, 1.0],
            [0.37109375, 0.29296875, 0.54296875, 1.0],
            [0.8984375, 0.6015625, 0.55078125, 1.0],
            [0.2578125, 0.9140625, 0.86328125, 1.0],
            [0.80078125, 0.70703125, 0.59765625, 1.0],
            [0.0, 0.640625, 0.796875, 1.0],
            [0.97265625, 0.33984375, 0.0, 1.0],
            [0.0, 0.125, 0.24609375, 1.0],
            [0.67578125, 0.93359375, 0.81640625, 1.0],
            [0.375, 0.375, 0.375, 1.0],
            [0.8359375, 0.92578125, 0.08984375, 1.0],
            [0.92578125, 0.16796875, 0.19921875, 1.0],
            [0.84375, 0.3515625, 0.49609375, 1.0],
            [0.58984375, 0.734375, 0.3828125, 1.0],
            [0.0, 0.32421875, 0.609375, 1.0],
            [0.9296875, 0.640625, 0.49609375, 1.0],
            [0.0, 0.38671875, 0.6953125, 1.0],
            [0.609375, 0.76171875, 0.83203125, 1.0],
            [0.0625, 0.09375, 0.125, 1.0],
        ]
    )

def render_loop():
    bpy.ops.render.render(animation=True)

def create_background():
    create_floor()
    create_emissive_ring()

def create_emissive_ring():
    bpy.ops.mesh.primitive_circle_add(vertices=128, radius=5.5)
    ring_obj = bpy.context.active_object
    ring_obj.name = "ring.emissive"
    ring_obj.rotation_euler.x = math.radians(90)
    bpy.ops.object.convert(target="CURVE")
    ring_obj.data.bevel_depth = 0.05
    ring_obj.data.bevel_resolution = 16
    ring_material = create_emissive_ring_material()
    ring_obj.data.materials.append(ring_material)

def create_emissive_ring_material():
    color = get_random_color()
    material = bpy.data.materials.new(name="emissive_ring_material")
    material.use_nodes = True
    material.node_tree.nodes["Principled BSDF"].inputs["Emission"].default_value = color
    material.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = 30.0
    return material

def create_metal_ring_material():
    color = get_random_color()
    material = bpy.data.materials.new(name="metal_ring_material")
    material.use_nodes = True
    material.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = color
    material.node_tree.nodes["Principled BSDF"].inputs["Metallic"].default_value = 1.0
    return material

def create_floor_material():
    color = get_random_color()
    material = bpy.data.materials.new(name="floor_material")
    material.use_nodes = True
    material.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = color
    material.node_tree.nodes["Principled BSDF"].inputs["Specular"].default_value = 0
    return material

def create_floor():
    bpy.ops.mesh.primitive_plane_add(size=200, location=(0, 0, -6.0))
    floor_obj = active_object()
    floor_obj.name = "plane.floor"
    floor_material = create_floor_material()
    floor_obj.data.materials.append(floor_material)

def add_light():
    bpy.ops.object.light_add(type="AREA")
    area_light = active_object()
    area_light.location.z = 6
    area_light.scale *= 10
    area_light.data.energy = 1000

def set_scene_props(fps, loop_seconds):
    frame_count = fps * loop_seconds
    scene = bpy.context.scene
    scene.frame_end = frame_count
    world = bpy.data.worlds["World"]
    if "Background" in world.node_tree.nodes:
        world.node_tree.nodes["Background"].inputs[0].default_value = (0, 0, 0, 1)
    scene.render.fps = fps
    scene.frame_current = 1
    scene.frame_start = 1
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 200
    scene.view_settings.look = "Very High Contrast"
    set_1080px_square_render_res()

def setup_scene(i=0):
    fps = 30
    loop_seconds = 12
    frame_count = fps * loop_seconds
    project_name = "ring_loop"
    bpy.context.scene.render.image_settings.file_format = "FFMPEG"
    bpy.context.scene.render.ffmpeg.format = "MPEG4"
    bpy.context.scene.render.filepath = f"/tmp/project_{project_name}/loop_{i}.mp4"
    seed = 0
    if seed:
        random.seed(seed)
    else:
        time_seed()
    clean_scene()
    set_scene_props(fps, loop_seconds)
    loc = (20, -20, 12)
    rot = (math.radians(60), 0, math.radians(70))
    setup_camera(loc, rot)
    context = {
        "frame_count": frame_count,
    }
    return context

def animate_rotation(context, ring_obj, z_rotation, y_rotation):
    degrees = y_rotation
    radians = math.radians(degrees)
    ring_obj.rotation_euler.y = radians
    degrees = z_rotation
    radians = math.radians(degrees)
    ring_obj.rotation_euler.z = radians
    start_frame = 1
    ring_obj.keyframe_insert("rotation_euler", frame=start_frame)
    degrees = y_rotation + 360
    radians = math.radians(degrees)
    ring_obj.rotation_euler.y = radians
    degrees = z_rotation + 360 * 2
    radians = math.radians(degrees)
    ring_obj.rotation_euler.z = radians
    end_frame = context["frame_count"] + 1
    ring_obj.keyframe_insert("rotation_euler", frame=end_frame)
    make_fcurves_linear()

def create_ring(index, current_radius, ring_material):
    bpy.ops.mesh.primitive_circle_add(vertices=128, radius=current_radius)
    ring_obj = bpy.context.active_object
    ring_obj.name = f"ring.{index}"
    bpy.ops.object.convert(target="CURVE")
    ring_obj.data.bevel_depth = 0.05
    ring_obj.data.bevel_resolution = 16
    bpy.ops.object.shade_smooth()
    apply_material(ring_material)
    return ring_obj

def create_centerpiece(context):
    radius_step = 0.1
    number_rings = 50
    z_rotation_step = 10
    z_rotation = 0
    y_rotation = 30
    ring_material = create_metal_ring_material()
    for i in range(number_rings):
        current_radius = radius_step * i
        ring_obj = create_ring(i, current_radius, ring_material)
        animate_rotation(context, ring_obj, z_rotation, y_rotation)
        z_rotation = z_rotation + z_rotation_step

def main():
    context = setup_scene()
    create_centerpiece(context)
    create_background()
    add_light()

if __name__ == "__main__":
    main()
