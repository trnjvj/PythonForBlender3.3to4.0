import random
import time
import bpy
import addon_utils

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
    camera.data.lens = 45
    camera.data.passepartout_alpha = 0.9
    empty = track_empty(camera)

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

def setup_scene():
    fps = 30
    loop_seconds = 12
    frame_count = fps * loop_seconds
    project_name = "loop_grid"
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

def enable_import_images_as_planes():
    loaded_default, loaded_state = addon_utils.check("io_import_images_as_planes")
    if not loaded_state:
        addon_utils.enable("io_import_images_as_planes")

def add_light():
    bpy.ops.object.light_add(type="SUN")
    sun = active_object()
    sun.data.energy = 2
    sun.data.specular_factor = 0
    sun.data.use_shadow = False

def get_list_of_loops():
    return [
        "c:\\tmp\\project_cube_loops\\loop_0.mp4",
        "c:\\tmp\\project_cube_loops\\loop_1.mp4",
        "c:\\tmp\\project_cube_loops\\loop_10.mp4",
        "c:\\tmp\\project_cube_loops\\loop_11.mp4",
        "c:\\tmp\\project_cube_loops\\loop_12.mp4",
        "c:\\tmp\\project_cube_loops\\loop_13.mp4",
        "c:\\tmp\\project_cube_loops\\loop_14.mp4",
        "c:\\tmp\\project_cube_loops\\loop_15.mp4",
        "c:\\tmp\\project_cube_loops\\loop_2.mp4",
        "c:\\tmp\\project_cube_loops\\loop_3.mp4",
        "c:\\tmp\\project_cube_loops\\loop_4.mp4",
        "c:\\tmp\\project_cube_loops\\loop_5.mp4",
        "c:\\tmp\\project_cube_loops\\loop_6.mp4",
        "c:\\tmp\\project_cube_loops\\loop_7.mp4",
        "c:\\tmp\\project_cube_loops\\loop_8.mp4",
        "c:\\tmp\\project_cube_loops\\loop_9.mp4",
    ]

def get_grid_step(path):
    bpy.ops.import_image.to_plane(files=[{"name": path}])
    plane = active_object()
    x_step = plane.dimensions.x
    y_step = plane.dimensions.y
    bpy.ops.object.delete()
    return x_step, y_step

def gen_centerpiece():
    list_of_video_paths = get_list_of_loops()
    random.shuffle(list_of_video_paths)
    x_step, y_step = get_grid_step(list_of_video_paths[0])
    start_x = -1.5
    stop_x = 2
    current_x = start_x
    current_y = -1.5
    for mp4_path in list_of_video_paths:
        bpy.ops.import_image.to_plane(files=[{"name": mp4_path}])
        obj = active_object()
        obj.location.x = current_x
        obj.location.y = current_y
        shader_nodes = obj.active_material.node_tree.nodes
        shader_nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.0
        shader_nodes["Image Texture"].image_user.use_cyclic = True
        current_x += x_step
        if current_x > stop_x:
            current_x = start_x
            current_y += y_step

def main():
    setup_scene()
    enable_import_images_as_planes()
    gen_centerpiece()
    add_light()

if __name__ == "__main__":
    main()
