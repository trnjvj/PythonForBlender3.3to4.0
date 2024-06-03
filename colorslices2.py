import random
import time
import math

import bpy
import mathutils

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

def get_random_pallet_color(context):
    return random.choice(context["colors"])

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

def set_1k_square_render_res():
    bpy.context.scene.render.resolution_x = 1080
    bpy.context.scene.render.resolution_y = 1080

def set_scene_props(fps, loop_seconds):
    frame_count = fps * loop_seconds
    scene = bpy.context.scene
    scene.frame_end = frame_count
    world = bpy.data.worlds["World"]
    if "Background" in world.node_tree.nodes:
        world.node_tree.nodes["Background"].inputs[0].default_value = (0.0, 0.0, 0.0, 1)
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

def make_ramp_from_colors(colors, color_ramp_node):
    color_count = len(colors)
    step = 1 / color_count
    cur_pos = step
    for _ in range(color_count - 2):
        color_ramp_node.elements.new(cur_pos)
        cur_pos += step
    for i, color in enumerate(colors):
        color_ramp_node.elements[i].color = color

def get_color_palette():
    palette = [
        [0.83984375, 0.8046875, 0.63671875, 1.0],
        [0.5625, 0.46875, 0.1484375, 1.0],
        [0.640625, 0.40234375, 0.09765625, 1.0],
        [0.8046875, 0.24609375, 0.0546875, 1.0],
        [0.1015625, 0.046875, 0.27734375, 1.0],
    ]
    return palette

def apply_location():
    bpy.ops.object.transform_apply(location=True)

def setup_scene():
    fps = 30
    loop_seconds = 6
    frame_count = fps * loop_seconds
    project_name = "color_slices"
    bpy.context.scene.render.image_settings.file_format = "PNG"
    bpy.context.scene.render.filepath = f"/tmp/project_{project_name}/"
    seed = 0
    if seed:
        random.seed(seed)
    else:
        time_seed()
    clean_scene()
    set_scene_props(fps, loop_seconds)
    loc = (0, 0, 5)
    rot = (0, 0, 0)
    setup_camera(loc, rot)
    context = {
        "frame_count": frame_count,
    }
    context["colors"] = get_color_palette()
    return context

def gen_perlin_curve():
    bpy.ops.mesh.primitive_circle_add(vertices=512, radius=1)
    circle = active_object()
    deform_coords = []

    for vert in circle.data.vertices:
        new_location = vert.co
        noise_value = mathutils.noise.noise(new_location)
        noise_value = noise_value / 2
        deform_vector = vert.co * noise_value
        deform_coord = vert.co + deform_vector
        deform_coords.append(deform_coord)
    bpy.ops.object.convert(target="CURVE")
    curve_obj = active_object()

def main():
    context = setup_scene()
    gen_perlin_curve()

if __name__ == "__main__":
    main()
