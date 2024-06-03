import blf
import bpy

font_info = {
    "font_id": 0,
    "handler": None,
}

def init():
    import os
    font_path = bpy.path.abspath('//Zeyada.ttf')
    if os.path.exists(font_path):
        font_info["font_id"] = blf.load(font_path)
    else:
        font_info["font_id"] = 0
    font_info["handler"] = bpy.types.SpaceView3D.draw_handler_add(
        draw_callback_px, (None, None), 'WINDOW', 'POST_PIXEL')

def draw_callback_px(self, context):
    font_id = font_info["font_id"]
    blf.position(font_id, 2, 80, 0)
    blf.size(font_id, 50.0)
    blf.draw(font_id, "Hello World")

if __name__ == '__main__':
    init()