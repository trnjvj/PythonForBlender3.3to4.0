import bpy
from bpy import context
import numpy as np
import builtins as __builtin__

npa = np.ndarray

def console_print(*args) -> None:
    for a in context.screen.areas:
        if a.type == 'CONSOLE':
            c = {'area': a, 'space_data': a.spaces.active, 'region': a.regions[-1], 'window': context.window,
                 'screen': context.screen}
            s = " ".join([str(arg) for arg in args])
            for line in s.split("\n"):
                bpy.ops.console.scrollback_append(c, text=line)

def print(*args, **kwargs):
    console_print(*args)  # to py consoles
    __builtin__.print(*args, **kwargs)  # to system console

class ColumnVector(npa):
    def __init__(self, x: float, y: float, z: float):
        self[0] = x
        self[1] = y
        self[2] = z
        self[3] = 1

    def __new__(cls, x: float, y: float, z: float):
        obj = super(ColumnVector, cls).__new__(cls, (4,), np.float64)

        return obj

    def __eq__(self, other):
        return np.array_equal(self, other)

    def __matmul__(self, other):
        return self @ other


class ThreeDObject:
    def __init__(self, three_d_object_name: str = None):
        self.ref = None
        self.three_d_object_name = three_d_object_name if three_d_object_name else "unnamed_3D_object"

    def __str__(self):
        return self.three_d_object_name

    def __repr__(self):
        return self.three_d_object_name

    def __enter__(self):
        bpy.ops.object.select_all(action='DESELECT')  # Deselect all objects
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.ref = bpy.context.object

        if self.three_d_object_name:
            self.ref.name = self.three_d_object_name
            self.ref.show_name = True
        bpy.ops.object.select_all(action='DESELECT')

    def keyframe_insert(self, frame: int, _property: str = "location"):
        self.ref.keyframe_insert(data_path=_property, frame=frame, index=-1)

class Point(ColumnVector, ThreeDObject):
    def __init__(self, x: float, y: float, z: float, three_d_object_name: str = None, _type="PLAIN_AXES", radius=.25):
        ColumnVector.__init__(self, x, y, z)
        ThreeDObject.__init__(self, three_d_object_name)
        self.type = _type
        self.radius = radius

    def __new__(cls, x: float, y: float, z: float, three_d_object_name: str = None, _type="PLAIN_AXES"):
        obj = super(Point, cls).__new__(cls, x, y, z)
        return obj

    def __str__(self):
        name = f'"{self.three_d_object_name}"' if self.three_d_object_name else "Unnamed"
        return f"Point<{name}>({self[0]}, {self[1]}, {self[2]})"

    def place(self):
        with self:
            bpy.ops.object.empty_add(
                type=self.type,
                radius=self.radius,
                location=(self[:-1]),
            )

    def update(self, _point=None):
        if _point.any():
            self[0], self[1], self[2] = _point[0], _point[1], _point[2]
            self.ref.location = _point[:-1]

    def angle_between(self, axis: str = 'x') -> float:
        if axis not in ['x', 'y', 'z']:
            raise ValueError("Axis must be 'x', 'y', or 'z'.")
        if axis == 'x':
            angle = np.degrees(np.arctan(self[1] / self[0]))
        elif axis == 'y':
            angle = np.degrees(np.arctan(self[0] / self[1]))
        else:  # axis == 'z'
            angle = np.degrees(np.arctan(
                np.sqrt(self[0] ** 2 + self[1] ** 2) / self[2]
            ))
        return 0 if np.isnan(angle) else angle

    def translation(self, c_vector: ColumnVector):
        translation_matrix = np.identity(4)
        translation_matrix[0][3] = c_vector[0]
        translation_matrix[1][3] = c_vector[1]
        translation_matrix[2][3] = c_vector[2]
        final_matrix = translation_matrix @ np.array(self)
        self.update(final_matrix)

    def scaling(self, c_vector: ColumnVector):
        homothety_matrix = np.identity(4)
        homothety_matrix[0][0] = c_vector[0]
        homothety_matrix[1][1] = c_vector[1]
        homothety_matrix[2][2] = c_vector[2]
        final_matrix = homothety_matrix @ np.array(self)
        self.update(final_matrix)

    def rotation_x(self, angle: float):
        angle = np.radians(angle)
        rotation_matrix = np.identity(4)
        rotation_matrix[1][1] = np.cos(angle)
        rotation_matrix[1][2] = -np.sin(angle)
        rotation_matrix[2][1] = np.sin(angle)
        rotation_matrix[2][2] = np.cos(angle)
        final_matrix = rotation_matrix @ np.array(self)
        self.update(final_matrix)

    def rotation_y(self, angle: float):
        angle = np.radians(angle)
        rotation_matrix = np.identity(4)
        rotation_matrix[0][0] = np.cos(angle)
        rotation_matrix[0][2] = np.sin(angle)
        rotation_matrix[2][0] = -np.sin(angle)
        rotation_matrix[2][2] = np.cos(angle)
        final_matrix = rotation_matrix @ np.array(self)
        self.update(final_matrix)

    def rotation_z(self, angle: float):
        angle = np.radians(angle)
        rotation_matrix = np.identity(4)
        rotation_matrix[0][0] = np.cos(angle)
        rotation_matrix[0][1] = -np.sin(angle)
        rotation_matrix[1][0] = np.sin(angle)
        rotation_matrix[1][1] = np.cos(angle)
        final_matrix = rotation_matrix @ np.array(self)
        self.update(final_matrix)

def determine_common_axis(_point_1: Point, _point_2: Point, _point_3: Point) -> str:
    if _point_1[0] == _point_2[0] == _point_3[0]:
        axis = 'x'
    elif _point_1[1] == _point_2[1] == _point_3[1]:
        axis = 'y'
    elif _point_1[2] == _point_2[2] == _point_3[2]:
        axis = 'z'
    else:
        raise ValueError("The three points don't have a common axis.")
    return axis

class Edge(ThreeDObject):
    def __init__(
            self,
            _point_1: Point, _point_2: Point, _point_3: Point, _point_4: Point,
            three_d_object_name: str = None
    ):
        super().__init__(three_d_object_name)
        self.points = [_point_1, _point_2, _point_3, _point_4]
        self.plane_ref = None  # Store a reference to the plane object

    def __enter__(self):
        bpy.ops.object.select_all(action='DESELECT')  # Deselect all objects
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.ref = bpy.context.object
        if self.three_d_object_name:
            self.ref.name = self.three_d_object_name
            self.ref.show_name = True
        bpy.ops.object.select_all(action='DESELECT')

    def keyframe_insert(self, frame: int, _property: str = "location"):
        if self.ref:
            self.ref.keyframe_insert(data_path=_property, frame=frame, index=-1)

    def place(self):
        with self:
            final_location = (self.points[3] + self.points[0]) / 2
            needed_rotation = determine_common_axis(*self.points[:3])
            if needed_rotation == 'z':
                final_rotation = (0, 0, 0)
            elif needed_rotation == 'y':
                final_rotation = (np.radians(90), 0, 0)
            else:  # needed_rotation == 'x'
                final_rotation = (0, np.radians(90), 0)
            bpy.ops.mesh.primitive_plane_add(
                size=1,
                location=final_location[:-1],
                rotation=final_rotation,
            )

    def update(self, _points: list[Point] = None):
        print(f"Updating {self.three_d_object_name}")
        if _points:
            print(f"Updating {self.three_d_object_name} with {_points}")
            self.points = _points
        if self.ref:
            print(f"Updating {self.three_d_object_name} plane_ref")
            final_location = (self.points[3] + self.points[0]) / 2
            self.ref.location = final_location[:-1]

DESIRED_FPS = 24
PADDING_FRAMES = 2 * DESIRED_FPS  
ANIMATION_FRAMES = 5 * DESIRED_FPS 
Z_ANGLE = 90
DEGREES_PER_SECOND = 30
ANGLE_ANIMATION_FRAMES = Z_ANGLE // DEGREES_PER_SECOND * DESIRED_FPS
ANIM_1_END = ANIMATION_FRAMES + PADDING_FRAMES
ANIM_2_START = ANIM_1_END + PADDING_FRAMES
ANIM_2_END = ANIM_2_START + Z_ANGLE // DEGREES_PER_SECOND * DESIRED_FPS
TOTAL_FRAMES = ANIM_2_END + PADDING_FRAMES
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
points = [
    Point(0, 0, 0, "p_1"),
    Point(1, 0, 0, "p_2"),
    Point(0, 1, 0, "p_3"),
    Point(1, 1, 0, "p_4"),
    Point(0, 0, 1, "p_5"),
    Point(1, 0, 1, "p_6"),
    Point(0, 1, 1, "p_7"),
    Point(1, 1, 1, "p_8")
]
ANIM_FRAMES = ANGLE_ANIMATION_FRAMES + 1
for point in points:
    point.place()
    point.keyframe_insert(PADDING_FRAMES)
    point.translation(ColumnVector(0, 0, 2))
    point.keyframe_insert(ANIM_1_END)
    for i in range(1, ANGLE_ANIMATION_FRAMES + 1):
        point.keyframe_insert(ANIM_2_START + i)
        point.rotation_z(Z_ANGLE / ANGLE_ANIMATION_FRAMES)
bpy.context.scene.frame_end = TOTAL_FRAMES
