
import random
import time
import math

import bpy

import addon_utils



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


def clean_scene_experimental():

    old_scene_name = "to_delete"
    bpy.context.window.scene.name = old_scene_name
    bpy.ops.scene.new()
    bpy.data.scenes.remove(bpy.data.scenes[old_scene_name])


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


def add_empty(name=None):

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

    empty = add_empty(name=f"empty.tracker-target.{obj.name}")

    make_active(obj)
    bpy.ops.object.constraint_add(type="TRACK_TO")
    bpy.context.object.constraints["Track To"].target = empty

    return empty


def set_1080px_square_render_res():

    bpy.context.scene.render.resolution_x = 1080
    bpy.context.scene.render.resolution_y = 1080


def set_fcurve_interpolation_to_linear(obj=None):

    if obj is None:
        obj = active_object()

    for fcurve in bpy.context.active_object.animation_data.action.fcurves:
        for keyframe_point in fcurve.keyframe_points:
            keyframe_point.interpolation = "LINEAR"


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


def duplicate_object(obj=None, linked=False):
    if obj is None:
        obj = active_object()
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.duplicate(linked=linked)
    duplicate_obj = active_object()
    return duplicate_obj


def enable_addon(addon_module_name):

    loaded_default, loaded_state = addon_utils.check(addon_module_name)
    if not loaded_state:
        addon_utils.enable(addon_module_name)


def enable_extra_meshes():
    enable_addon(addon_module_name="add_mesh_extra_objects")


def enable_mod_tools():
    enable_addon(addon_module_name="space_view3d_modifier_tools")


def get_random_color():
    hex_color = random.choice(
        [
            "#402217",
            "#515559",
            "#727273",
            "#8C593B",
            "#A64E1B",
            "#A65D05",
            "#A68A80",
            "#A6A6A6",
            "#BF6415",
            "#BF8B2A",
            "#C5992E",
            "#E8BB48",
            "#F2DC6B",
        ]
    )

    return hex_color_to_rgba(hex_color)


def setup_camera(loc, rot):
    bpy.ops.object.camera_add(location=loc, rotation=rot)
    camera = active_object()
    bpy.context.scene.camera = camera
    camera.data.lens = 65
    camera.data.passepartout_alpha = 0.9
    empty = track_empty(camera)
    return empty


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
    scene.cycles.device = "GPU"
    scene.cycles.samples = 300
    scene.view_settings.look = "Very High Contrast"
    set_1080px_square_render_res()

def scene_setup(i=0):
    fps = 30
    loop_seconds = 12
    frame_count = fps * loop_seconds
    project_name = "stack_overflow"
    bpy.context.scene.render.image_settings.file_format = "FFMPEG"
    bpy.context.scene.render.ffmpeg.format = "MPEG4"
    bpy.context.scene.render.filepath = f"/tmp/project_{project_name}/loop_{i}.mp4"
    seed = 0
    if seed:
        random.seed(seed)
    else:
        time_seed()
    use_clean_scene_experimental = False
    if use_clean_scene_experimental:
        clean_scene_experimental()
    else:
        clean_scene()
    set_scene_props(fps, loop_seconds)
    z_coord = 1
    loc = (6.5, -3, z_coord)
    rot = (0, 0, 0)
    empty = setup_camera(loc, rot)
    empty.location.z = 2
    context = {
        "frame_count": frame_count,
        "frame_count_loop": frame_count + 1,
    }
    return context


def create_metallic_material(color, name=None, roughness=0.1, return_nodes=False):
    if name is None:
        name = ""
    material = bpy.data.materials.new(name=f"material.metallic.{name}")
    material.use_nodes = True
    material.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = color
    material.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = roughness
    material.node_tree.nodes["Principled BSDF"].inputs["Metallic"].default_value = 1.0
    if return_nodes:
        return material, material.node_tree.nodes
    else:
        return material

def apply_metallic_material(color, name=None, roughness=0.1):
    material = create_metallic_material(color, name=name, roughness=roughness)
    obj = active_object()
    obj.data.materials.append(material)

def add_lights():
    rig_obj, empty = create_light_rig(light_count=3, light_type="AREA", rig_radius=5.0, energy=150)
    rig_obj.location.z = 3
    bpy.ops.object.light_add(type="AREA", radius=5, location=(0, 0, 5))

def create_light_rig(light_count, light_type="AREA", rig_radius=2.0, light_radius=1.0, energy=100):
    bpy.ops.mesh.primitive_circle_add(vertices=light_count, radius=rig_radius)
    rig_obj = active_object()
    empty = add_empty(name=f"empty.tracker-target.lights")
    for i in range(light_count):
        loc = rig_obj.data.vertices[i].co
        bpy.ops.object.light_add(type=light_type, radius=light_radius, location=loc)
        light = active_object()
        light.data.energy = energy
        light.parent = rig_obj
        bpy.ops.object.constraint_add(type="TRACK_TO")
        light.constraints["Track To"].target = empty
    return rig_obj, empty

def make_surface(color):
    bpy.ops.mesh.primitive_z_function_surface(div_x=64, div_y=64, size_x=1, size_y=1)
    surface = active_object()
    bpy.ops.object.shade_smooth()
    surface.data.use_auto_smooth = True
    bpy.ops.object.modifier_add(type="SOLIDIFY")
    bpy.ops.object.modifier_add(type="BEVEL")
    surface.modifiers["Bevel"].width = 0.001
    surface.modifiers["Bevel"].limit_method = "NONE"
    bpy.ops.object.apply_all_modifiers()
    apply_metallic_material(color, name="metallic", roughness=random.uniform(0.35, 0.65))
    return surface

def update_object(obj):
    obj.scale *= 1.5
    obj.location.z = 2
    obj.rotation_euler.z = math.radians(270)

def animate_object_update(context, obj, current_frame):
    obj.keyframe_insert("scale", frame=current_frame)
    obj.keyframe_insert("location", frame=current_frame)
    obj.keyframe_insert("rotation_euler", frame=current_frame)
    update_object(obj)
    frame = current_frame + context["frame_count_loop"]
    obj.keyframe_insert("scale", frame=frame)
    obj.keyframe_insert("location", frame=frame)
    obj.keyframe_insert("rotation_euler", frame=frame)
    set_fcurve_interpolation_to_linear()

def create_centerpiece(context, color):
    frame_step = 6
    buffer = 1
    count = int((context["frame_count_loop"] * 2) / frame_step) + buffer
    current_frame = -context["frame_count_loop"]
    surface = make_surface(color)
    for _ in range(count):
        duplicate_surface = duplicate_object(surface)
        animate_object_update(context, duplicate_surface, current_frame)
        current_frame += frame_step

def create_background(color):
    bottom_surface = make_surface(color)
    bottom_surface.location.z -= 0.001
    top_surface = make_surface(color)
    update_object(top_surface)
    top_surface.location.z += 0.001
    bpy.ops.mesh.primitive_plane_add(size=100, location=(0, 0, 0.5))

def main():
    context = scene_setup()
    enable_extra_meshes()
    enable_mod_tools()
    color = get_random_color()
    create_centerpiece(context, color)
    create_background(color)
    add_lights()

if __name__ == "__main__":
    main()
