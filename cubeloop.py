import random
import time
import math

import bpy

def purge_orphans():
    if bpy.app.version >= (3, 0, 0):
        bpy.ops.outliner.orphans_purge(
            do_local_ids=True, do_linked_ids=True, do_recursive=True
        )
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

def set_1k_square_render_res():
    bpy.context.scene.render.resolution_x = 1080
    bpy.context.scene.render.resolution_y = 1080

def set_scene_props(fps, loop_seconds):
    frame_count = fps * loop_seconds
    scene = bpy.context.scene
    scene.frame_end = frame_count
    world = bpy.data.worlds["World"]
    if "Background" in world.node_tree.nodes:
        world.node_tree.nodes["Background"].inputs["Color"].default_value = (0, 0, 0, 1)
    scene.render.fps = fps
    scene.frame_current = 1
    scene.frame_start = 1
    scene.eevee.use_bloom = True
    scene.eevee.bloom_intensity = 0.005
    scene.eevee.use_gtao = True
    scene.eevee.gtao_distance = 4
    scene.eevee.gtao_factor = 5
    scene.eevee.taa_render_samples = 64
    scene.view_settings.look = "Very High Contrast"
    set_1k_square_render_res()

def setup_scene(i=0):
    fps = 30
    loop_seconds = 12
    frame_count = fps * loop_seconds
    project_name = "cube_loops"
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
    loc = (0, 0, 15)
    rot = (0, 0, 0)
    setup_camera(loc, rot)
    context = {
        "frame_count": frame_count,
    }
    return context

def make_fcurves_linear():
    for fc in bpy.context.active_object.animation_data.action.fcurves:
        fc.extrapolation = "LINEAR"

def get_random_color():
    return random.choice(
        [
            [0.92578125, 1, 0.0, 1],
            [0.203125, 0.19140625, 0.28125, 1],
            [0.8359375, 0.92578125, 0.08984375, 1],
            [0.16796875, 0.6796875, 0.3984375, 1],
            [0.6875, 0.71875, 0.703125, 1],
            [0.9609375, 0.9140625, 0.48046875, 1],
            [0.79296875, 0.8046875, 0.56640625, 1],
            [0.96484375, 0.8046875, 0.83984375, 1],
            [0.91015625, 0.359375, 0.125, 1],
            [0.984375, 0.4609375, 0.4140625, 1],
            [0.0625, 0.09375, 0.125, 1],
            [0.2578125, 0.9140625, 0.86328125, 1],
            [0.97265625, 0.21875, 0.1328125, 1],
            [0.87109375, 0.39453125, 0.53515625, 1],
            [0.8359375, 0.92578125, 0.08984375, 1],
            [0.37109375, 0.29296875, 0.54296875, 1],
            [0.984375, 0.4609375, 0.4140625, 1],
            [0.92578125, 0.16796875, 0.19921875, 1],
            [0.9375, 0.9609375, 0.96484375, 1],
            [0.3359375, 0.45703125, 0.4453125, 1],
        ]
    )

def apply_material(obj):
    color = get_random_color()
    mat = bpy.data.materials.new(name="Material")
    mat.use_nodes = True
    mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = color
    mat.node_tree.nodes["Principled BSDF"].inputs["Specular"].default_value = 0
    obj.data.materials.append(mat)

def add_lights():
    rot = (math.radians(60), 0, math.radians(120))
    bpy.ops.object.light_add(type="SUN", rotation=rot)
    bpy.context.object.data.energy = 10
    bpy.context.object.data.angle = math.radians(180)
    bpy.context.object.data.use_shadow = False

def render_loop():
    bpy.ops.render.render(animation=True)

def animate_object_rotation(context, obj):
    frame = 1
    obj.rotation_euler.x = math.radians(random.uniform(-360, 360))
    obj.keyframe_insert("rotation_euler", index=0, frame=frame)
    obj.rotation_euler.y = math.radians(random.uniform(-360, 360))
    obj.keyframe_insert("rotation_euler", index=1, frame=frame)
    obj.rotation_euler.z = math.radians(random.uniform(-360, 360))
    obj.keyframe_insert("rotation_euler", index=2, frame=frame)
    frame += context["frame_count"]
    rotations = [-3, -2, -1, 0, 1, 2, 3]
    obj.rotation_euler.x += math.radians(360) * random.choice(rotations)
    obj.keyframe_insert("rotation_euler", index=0, frame=frame)
    obj.rotation_euler.y += math.radians(360) * random.choice(rotations)
    obj.keyframe_insert("rotation_euler", index=1, frame=frame)
    obj.rotation_euler.z += math.radians(360) * random.choice(rotations)
    obj.keyframe_insert("rotation_euler", index=2, frame=frame)
    make_fcurves_linear()

def gen_centerpiece(context):
    for _ in range(3):
        bpy.ops.mesh.primitive_cube_add(size=random.uniform(1, 3))
        cube = active_object()
        bpy.ops.object.modifier_add(type="WIREFRAME")
        cube.modifiers["Wireframe"].thickness = random.uniform(0.03, 0.1)
        animate_object_rotation(context, cube)
        apply_material(cube)

def gen_background():
    bpy.ops.mesh.primitive_plane_add(size=20, location=(0, 0, -5))
    obj = active_object()
    apply_material(obj)

def main():
    count = 16
    for i in range(count):
        context = setup_scene(i)
        add_lights()
        gen_centerpiece(context)
        gen_background()

if __name__ == "__main__":
    main()
