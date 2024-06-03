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

def hex_color_to_rgb(hex_color):
    if hex_color.startswith("#"):
        hex_color = hex_color[1:]
    assert len(hex_color) == 6, f"RRGGBB is the supported hex color format: {hex_color}"
    red = int(hex_color[:2], 16)
    srgb_red = red / 255
    linear_red = convert_srgb_to_linear_rgb(srgb_red)
    green = int(hex_color[2:4], 16)
    srgb_green = green / 255
    linear_green = convert_srgb_to_linear_rgb(srgb_green)
    blue = int(hex_color[4:6], 16)
    srgb_blue = blue / 255
    linear_blue = convert_srgb_to_linear_rgb(srgb_blue)
    return tuple([linear_red, linear_green, linear_blue])

def hex_color_to_rgba(hex_color, alpha=1.0):
    linear_red, linear_green, linear_blue = hex_color_to_rgb(hex_color)
    return tuple([linear_red, linear_green, linear_blue, alpha])

def convert_srgb_to_linear_rgb(srgb_color_component):
    if srgb_color_component <= 0.04045:
        linear_color_component = srgb_color_component / 12.92
    else:
        linear_color_component = math.pow((srgb_color_component + 0.055) / 1.055, 2.4)
    return linear_color_component

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
    empty = track_empty(camera)
    camera.data.dof.use_dof = True
    camera.data.dof.focus_object = empty
    camera.data.dof.aperture_fstop = 0.1
    return empty

def set_1080px_square_render_res():
    bpy.context.scene.render.resolution_x = 1080
    bpy.context.scene.render.resolution_y = 1080

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
    scene.eevee.use_bloom = True
    scene.eevee.bloom_intensity = 0.005
    scene.eevee.use_gtao = True
    scene.eevee.gtao_distance = 4
    scene.eevee.gtao_factor = 5
    scene.eevee.taa_render_samples = 64
    scene.view_settings.look = "Very High Contrast"
    set_1080px_square_render_res()

def scene_setup(i=0):
    fps = 30
    loop_seconds = 6
    frame_count = fps * loop_seconds
    project_name = "hex_delay_spin"
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
    loc = (0, 15, 0)
    rot = (0, 0, 0)
    setup_camera(loc, rot)
    context = {
        "frame_count": frame_count,
        "material": create_metallic_material(get_random_color()),
    }
    return context

def make_fcurves_bounce():
    for fcurve in bpy.context.active_object.animation_data.action.fcurves:
        for kf in fcurve.keyframe_points:
            kf.interpolation = "BOUNCE"

def render_loop():
    bpy.ops.render.render(animation=True)

def get_random_color():
    hex_color = random.choice(
        [
            "#846295",
            "#B369AC",
            "#BFB3CB",
            "#E3E0E7",
            "#F3F0E5",
            "#557E5F",
            "#739D87",
            "#C3CDB1",
            "#7F8BC3",
            "#0D2277",
            "#72ED72",
            "#40D4BC",
            "#7EADF0",
            "#EAEC71",
            "#C4C55D",
            "#EDE1D4",
            "#DBCBBD",
            "#A98E8E",
            "#676F84",
            "#4F5D6B",
            "#990065",
            "#C60083",
            "#FF00A9",
            "#F9D19C",
            "#BFB3A7",
            "#B3A598",
            "#998995",
            "#99A1A3",
            "#74817F",
            "#815D6D",
        ]
    )
    return hex_color_to_rgba(hex_color)

def get_random_highlight_color():
    hex_color = random.choice(
        [
            "#CB5A0C",
            "#DBF227",
            "#22BABB",
            "#FFEC5C",
        ]
    )
    return hex_color_to_rgb(hex_color)

def add_lights():
    rotation = (math.radians(-60), math.radians(-15), math.radians(-45))
    bpy.ops.object.light_add(type="SUN", rotation=rotation)
    sun_light = active_object()
    sun_light.data.energy = 1.5
    if random.randint(0, 1):
        bpy.ops.object.light_add(type="AREA")
        area_light = active_object()
        area_light.scale *= 5
        area_light.data.color = get_random_highlight_color()
        area_light.data.energy = 200
        euler_x_rotation = math.radians(180)
        z_location = -4
        if random.randint(0, 1):
            euler_x_rotation = 0
            z_location = 4
        area_light.rotation_euler.x = euler_x_rotation
        area_light.location.z = z_location

def create_metallic_material(color):
    material = bpy.data.materials.new(name="metallic.material")
    material.use_nodes = True
    bsdf_node = material.node_tree.nodes["Principled BSDF"]
    bsdf_node.inputs["Base Color"].default_value = color
    bsdf_node.inputs["Metallic"].default_value = 1.0
    return material

def apply_material(obj, material):
    obj.data.materials.append(material)

def animate_rotation(context, obj, i, frame_offset):
    start_frame = 10 + i * frame_offset
    obj.keyframe_insert("rotation_euler", frame=start_frame)
    degrees = 180
    radians = math.radians(degrees)
    obj.rotation_euler.z = radians
    degrees = 120
    radians = math.radians(degrees)
    obj.rotation_euler.y = radians
    end_frame = context["frame_count"] - 10
    obj.keyframe_insert("rotation_euler", frame=end_frame)
    make_fcurves_bounce()

def create_bevel(obj):
    bpy.ops.object.convert(target="CURVE")
    obj.data.bevel_depth = 0.025
    obj.data.bevel_resolution = 16
    bpy.ops.object.shade_smooth()

def create_centerpiece(context):
    radius_step = 0.2
    number_of_shapes = 16
    frame_offset = 5
    for i in range(1, number_of_shapes):
        current_radius = i * radius_step
        bpy.ops.mesh.primitive_circle_add(vertices=6, radius=current_radius)
        shape_obj = active_object()
        degrees = -90
        radians = math.radians(degrees)
        shape_obj.rotation_euler.x = radians
        animate_rotation(context, shape_obj, i, frame_offset)
        create_bevel(shape_obj)
        apply_material(shape_obj, context["material"])

def main():
    context = scene_setup()
    create_centerpiece(context)
    add_lights()

if __name__ == "__main__":
    main()
