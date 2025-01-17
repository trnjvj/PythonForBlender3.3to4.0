

import random
import time

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


def set_fcurve_extrapolation_to_linear():
    for fc in bpy.context.active_object.animation_data.action.fcurves:
        fc.extrapolation = "LINEAR"


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


def set_scene_props(fps, frame_count):

    scene = bpy.context.scene
    scene.frame_end = frame_count

    world = bpy.data.worlds["World"]
    if "Background" in world.node_tree.nodes:
        world.node_tree.nodes["Background"].inputs[0].default_value = (0, 0, 0, 1)

    scene.render.fps = fps

    scene.frame_current = 1
    scene.frame_start = 1


def scene_setup():
    fps = 30
    loop_seconds = 12
    frame_count = fps * loop_seconds

    seed = 0
    if seed:
        random.seed(seed)
    else:
        time_seed()

    clean_scene()

    set_scene_props(fps, frame_count)




def link_nodes_by_mesh_socket(node_tree, from_node, to_node):
    node_tree.links.new(from_node.outputs["Mesh"], to_node.inputs["Mesh"])


def create_node(node_tree, type_name, node_x_location, node_location_step_x=0, node_y_location=0):

    node_obj = node_tree.nodes.new(type=type_name)
    node_obj.location.x = node_x_location
    node_obj.location.y = node_y_location
    node_x_location += node_location_step_x

    return node_obj, node_x_location


def create_random_bool_value_node(node_tree, node_x_location, node_y_location):
    separate_geo_random_value_node, node_x_location = create_node(node_tree, "FunctionNodeRandomValue", node_x_location, node_y_location=node_y_location)
    target_output_type = "BOOLEAN"
    separate_geo_random_value_node.data_type = target_output_type

    random_value_node_output_lookup = {socket.type: socket for socket in separate_geo_random_value_node.outputs.values()}

    target_output_socket = random_value_node_output_lookup[target_output_type]
    return target_output_socket


def create_separate_geo_node(node_tree, node_x_location, node_location_step_x):

    random_value_node_output_socket = create_random_bool_value_node(node_tree, node_x_location, node_y_location=-200)

    separate_geometry_node, node_x_location = create_node(node_tree, "GeometryNodeSeparateGeometry", node_x_location, node_location_step_x)
    separate_geometry_node.domain = "FACE"

    to_node = separate_geometry_node
    node_tree.links.new(random_value_node_output_socket, to_node.inputs["Selection"])

    return separate_geometry_node, node_x_location


def create_scale_element_geo_node(node_tree, geo_selection_node_output, node_x_location, node_y_location):
    random_value_node_output_socket = create_random_bool_value_node(node_tree, node_x_location, node_y_location=node_y_location - 200)

    scale_elements_node, node_x_location = create_node(node_tree, "GeometryNodeScaleElements", node_x_location, node_y_location=node_y_location)
    scale_elements_node.inputs["Scale"].default_value = 0.8

    start_frame = random.randint(0, 150)

    create_data_animation_loop(
        scale_elements_node.inputs["Scale"],
        "default_value",
        start_value=0.0,
        mid_value=0.8,
        start_frame=start_frame,
        loop_length=90,
        linear_extrapolation=False,
    )

    to_node = scale_elements_node
    node_tree.links.new(random_value_node_output_socket, to_node.inputs["Selection"])

    to_node = scale_elements_node
    node_tree.links.new(geo_selection_node_output, to_node.inputs["Geometry"])

    return scale_elements_node


def separate_faces_and_animate_scale(node_tree, node_x_location, node_location_step_x):

    separate_geometry_node, node_x_location = create_separate_geo_node(node_tree, node_x_location, node_location_step_x)

    scale_elements_geo_nodes = []
    top_scale_elements_node = create_scale_element_geo_node(node_tree, separate_geometry_node.outputs["Selection"], node_x_location, node_y_location=200)
    scale_elements_geo_nodes.append(top_scale_elements_node)

    bottom_scale_elements_node = create_scale_element_geo_node(node_tree, separate_geometry_node.outputs["Inverted"], node_x_location, node_y_location=-200)
    scale_elements_geo_nodes.append(bottom_scale_elements_node)

    for fcurve in node_tree.animation_data.action.fcurves.values():
        fcurve.modifiers.new(type="CYCLES")

    node_x_location += node_location_step_x

    join_geometry_node, node_x_location = create_node(node_tree, "GeometryNodeJoinGeometry", node_x_location, node_location_step_x)

    for node in scale_elements_geo_nodes:
        from_node = node
        to_node = join_geometry_node
        node_tree.links.new(from_node.outputs["Geometry"], to_node.inputs["Geometry"])

    return separate_geometry_node, join_geometry_node, node_x_location


def update_geo_node_tree(node_tree):

    out_node = node_tree.nodes["Group Output"]

    node_x_location = 0
    node_location_step_x = 300

    mesh_cube_node, node_x_location = create_node(node_tree, "GeometryNodeMeshCube", node_x_location, node_location_step_x)

    subdivide_mesh_node, node_x_location = create_node(node_tree, "GeometryNodeSubdivideMesh", node_x_location, node_location_step_x)
    subdivide_mesh_node.inputs["Level"].default_value = 3

    triangulate_node, node_x_location = create_node(node_tree, "GeometryNodeTriangulate", node_x_location, node_location_step_x)

    split_edges_node, node_x_location = create_node(node_tree, "GeometryNodeSplitEdges", node_x_location, node_location_step_x)

    separate_geometry_node, join_geometry_node, node_x_location = separate_faces_and_animate_scale(node_tree, node_x_location, node_location_step_x)

    out_node.location.x = node_x_location

    link_nodes_by_mesh_socket(node_tree, from_node=mesh_cube_node, to_node=subdivide_mesh_node)
    link_nodes_by_mesh_socket(node_tree, from_node=subdivide_mesh_node, to_node=triangulate_node)
    link_nodes_by_mesh_socket(node_tree, from_node=triangulate_node, to_node=split_edges_node)

    from_node = split_edges_node
    to_node = separate_geometry_node
    node_tree.links.new(from_node.outputs["Mesh"], to_node.inputs["Geometry"])

    from_node = join_geometry_node
    to_node = out_node
    node_tree.links.new(from_node.outputs["Geometry"], to_node.inputs["Geometry"])


def create_centerpiece():
    bpy.ops.mesh.primitive_plane_add()

    bpy.ops.node.new_geometry_nodes_modifier()
    node_tree = bpy.data.node_groups["Geometry Nodes"]

    update_geo_node_tree(node_tree)

    bpy.ops.object.modifier_add(type="SOLIDIFY")

    # make the Geo Nodes modifier the active mode at the end
    bpy.context.active_object.modifiers["GeometryNodes"].is_active = True


def main():
    scene_setup()
    create_centerpiece()


if __name__ == "__main__":
    main()
