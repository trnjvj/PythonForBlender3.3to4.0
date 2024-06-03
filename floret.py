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

def set_1080px_square_render_res():
    bpy.context.scene.render.resolution_x = 1080
    bpy.context.scene.render.resolution_y = 1080

def set_fcurve_extrapolation_to_linear():
    for fc in bpy.context.active_object.animation_data.action.fcurves:
        fc.extrapolation = "LINEAR"

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

def create_emission_material(color, name=None, energy=30, return_nodes=False):
    if name is None:
        name = ""
    material = bpy.data.materials.new(name=f"material.emission.{name}")
    material.use_nodes = True
    out_node = material.node_tree.nodes.get("Material Output")
    bsdf_node = material.node_tree.nodes.get("Principled BSDF")
    material.node_tree.nodes.remove(bsdf_node)
    node_emission = material.node_tree.nodes.new(type="ShaderNodeEmission")
    node_emission.inputs["Color"].default_value = color
    node_emission.inputs["Strength"].default_value = energy
    node_emission.location = 0, 0
    material.node_tree.links.new(node_emission.outputs["Emission"], out_node.inputs["Surface"])
    if return_nodes:
        return material, material.node_tree.nodes
    else:
        return material

def render_loop():
    bpy.ops.render.render(animation=True)


def get_random_color():
    hex_color = random.choice(
        [
            "#FC766A",
            "#5B84B1",
            "#5F4B8B",
            "#E69A8D",
            "#42EADD",
            "#CDB599",
            "#00A4CC",
            "#F95700",
            "#00203F",
            "#ADEFD1",
            "#606060",
            "#D6ED17",
            "#ED2B33",
            "#D85A7F",
        ]
    )
    return hex_color_to_rgba(hex_color)

def setup_camera(loc, rot):
    bpy.ops.object.camera_add(location=loc, rotation=rot)
    camera = active_object()
    bpy.context.scene.camera = camera
    camera.data.lens = 70
    camera.data.passepartout_alpha = 0.9
    empty = track_empty(camera)
    bpy.context.object.data.dof.use_dof = True
    bpy.context.object.data.dof.aperture_fstop = 0.1
    return empty

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
    bpy.context.scene.eevee.use_bloom = True
    scene.view_settings.look = "Very High Contrast"
    set_1080px_square_render_res()

def scene_setup(i=0):
    fps = 30
    loop_seconds = 12
    frame_count = fps * loop_seconds
    project_name = "floret"
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
    loc = (0, 0, 80)
    rot = (0, 0, 0)
    setup_camera(loc, rot)
    context = {
        "frame_count": frame_count,
        "fps": fps,
    }
    return context

def create_data_animation_loop(obj, data_path, start_value, mid_value, start_frame, loop_length, linear_extrapolation=True):
    setattr(obj, data_path, start_value)
    obj.keyframe_insert(data_path, frame=start_frame)
    setattr(obj, data_path, mid_value)
    mid_frame = start_frame + (loop_length) / 2
    obj.keyframe_insert(data_path, frame=mid_frame)
    setattr(obj, data_path, start_value)
    end_frame = start_frame + loop_length
    obj.keyframe_insert(data_path, frame=end_frame)
    if linear_extrapolation:
        set_fcurve_extrapolation_to_linear()

def calculate_end_frame(context, current_frame):
    quotient, remainder = divmod(current_frame, context["fps"])
    if remainder != 0:
        bpy.context.scene.frame_end = (quotient + 1) * context["fps"]
    else:
        bpy.context.scene.frame_end = current_frame
    return bpy.context.scene.frame_end

def animate_depth_of_field(frame_end):
    start_focus_distance = 15.0
    mid_focus_distance = bpy.data.objects["Camera"].location.z / 2
    start_frame = 1
    loop_length = frame_end
    create_data_animation_loop(
        bpy.data.objects["Camera"].data.dof,
        "focus_distance",
        start_focus_distance,
        mid_focus_distance,
        start_frame,
        loop_length,
        linear_extrapolation=False,
    )

def calculate_phyllotaxis_coordinates(n, angle, scale_fac):
    current_angle = n * angle
    current_radius = scale_fac * math.sqrt(n)
    x = current_radius * math.cos(current_angle)
    y = current_radius * math.sin(current_angle)
    return x, y

def create_centerpiece(context):
    colors = (hex_color_to_rgba("#306998"), hex_color_to_rgba("#FFD43B"))
    ico_sphere_radius = 0.2
    scale_fac = 1.0
    angle = math.radians(random.uniform(137.0, 138.0))
    current_frame = 1
    frame_step = 0.5
    start_emission_strength_value = 0
    mid_emission_strength_value = 20
    loop_length = 60
    count = 300
    for n in range(count):
        x, y = calculate_phyllotaxis_coordinates(n, angle, scale_fac)
        bpy.ops.mesh.primitive_ico_sphere_add(radius=ico_sphere_radius, location=(x, y, 0))
        obj = active_object()
        material, nodes = create_emission_material(color=random.choice(colors), name=f"{n}_sphr", energy=30, return_nodes=True)
        obj.data.materials.append(material)
        create_data_animation_loop(
            nodes["Emission"].inputs["Strength"],
            "default_value",
            start_emission_strength_value,
            mid_emission_strength_value,
            current_frame,
            loop_length,
            linear_extrapolation=False,
        )
    current_frame += frame_step
    current_frame = int(current_frame + loop_length)
    end_frame = calculate_end_frame(context, current_frame)
    animate_depth_of_field(end_frame)

def main():
    context = scene_setup()
    create_centerpiece(context)

if __name__ == "__main__":
    main()
