import bpy
import blf
import rna_keymap_ui
from bpy_extras.view3d_utils import region_2d_to_location_3d
from mathutils import Vector, Matrix
import gpu
from gpu_extras.batch import batch_for_shader
import bgl

from . utils import get_prefs

# HUD DRAWING

def draw_init(self, event, HUDx_offset=0, HUDy_offset=20):
    self.font_id = 1
    
    
    
    # update HUD location
    HUDside = get_prefs().hud_StickSide
    if HUDside == 'MOUSE':
        self.HUD_x = event.mouse_region_x + HUDx_offset
        self.HUD_y = event.mouse_region_y + HUDy_offset
        print (event.mouse_region_x)
    elif HUDside == 'MOUSEFOLLOW':
        self.HUD_x = self.mouse_x + HUDx_offset
        self.HUD_y = self.mouse_y + HUDy_offset
    elif HUDside == 'TOP':
        self.HUD_x = bpy.context.area.width / 2  - 150 + HUDx_offset
        self.HUD_y = bpy.context.area.height - 90 + HUDy_offset
    else:
        self.HUD_x = bpy.context.area.width / 2  - 150 + HUDx_offset
        self.HUD_y = self.offset + 50 + HUDy_offset
        
    
    self.offset = 0


def draw_title(self, title, subtitle=None, subtitleoffset=125, HUDcolor=None, HUDalpha=0.5, shadow=True):
    if not HUDcolor:
        #HUDcolor = (1, 1, 1)
        HUDcolor = get_prefs().hud_Color
    shadow = (0, 0, 0)

    #scale = 1
    scale = bpy.context.preferences.view.ui_scale * get_prefs().hud_scale

    if shadow:
        blf.color(self.font_id, *shadow, HUDalpha * 0.7)
        blf.position(self.font_id, self.HUD_x - 7 + 1, self.HUD_y - 1, 0)
        blf.size(self.font_id, int(20 * scale), 72)
        blf.draw(self.font_id, "» " + title)

    blf.color(self.font_id, *HUDcolor, HUDalpha)
    blf.position(self.font_id, self.HUD_x - 7, self.HUD_y, 0)
    blf.size(self.font_id, int(20 * scale), 72)
    blf.draw(self.font_id, "» " + title)

    if subtitle:
        if shadow:
            blf.color(self.font_id, *shadow, HUDalpha / 2 * 0.7)
            blf.position(self.font_id, self.HUD_x - 7 + int(subtitleoffset * scale), self.HUD_y, 0)
            blf.size(self.font_id, int(15 * scale), 72)
            blf.draw(self.font_id, subtitle)

        blf.color(self.font_id, *HUDcolor, HUDalpha / 2)
        blf.position(self.font_id, self.HUD_x - 7 + int(subtitleoffset * scale), self.HUD_y, 0)
        blf.size(self.font_id, int(15 * scale), 72)
        blf.draw(self.font_id, subtitle)


def draw_prop(self, name, value, offset=0, decimal=2, active=True, HUDcolor=None, prop_offset=120, hint="", hint_offset=200, shadow=True):
    if not HUDcolor:
        # HUDcolor = (1, 1, 1)
        HUDcolor = get_prefs().hud_Color
    shadow = (0, 0, 0)

    if active:
        alpha = 1
    else:
        alpha = 0.4

    #scale = 1
    scale = bpy.context.preferences.view.ui_scale * get_prefs().hud_scale

    offset = self.offset + int(offset * scale)
    self.offset = offset


    # NAME
    if shadow:
        blf.color(self.font_id, *shadow, alpha * 0.7)
        blf.position(self.font_id, self.HUD_x + int(20 * scale) + 1, self.HUD_y - int(20 * scale) - offset - 1, 0)
        blf.size(self.font_id, int(11 * scale), 72)
        blf.draw(self.font_id, name)

    blf.color(self.font_id, *HUDcolor, alpha)
    blf.position(self.font_id, self.HUD_x + int(20 * scale), self.HUD_y - int(20 * scale) - offset, 0)
    blf.size(self.font_id, int(11 * scale), 72)
    blf.draw(self.font_id, name)


    # VALUE


    # string
    if type(value) is str:
        if shadow:
            blf.color(self.font_id, *shadow, alpha * 0.7)
            blf.position(self.font_id, self.HUD_x + int(prop_offset * scale) + 1, self.HUD_y - int(20 * scale) - offset - 1, 0)
            blf.size(self.font_id, int(14 * scale), 72)
            blf.draw(self.font_id, value)

        blf.color(self.font_id, *HUDcolor, alpha)
        blf.position(self.font_id, self.HUD_x + int(prop_offset * scale), self.HUD_y - int(20 * scale) - offset, 0)
        blf.size(self.font_id, int(14 * scale), 72)
        blf.draw(self.font_id, value)

    # bool
    elif type(value) is bool:
        prop_offset +=2
        if shadow:
            blf.color(self.font_id, *shadow, alpha * 0.7)
            blf.position(self.font_id, self.HUD_x + int(prop_offset * scale) + 1, self.HUD_y - int(20 * scale) - offset - 1, 0)
            blf.size(self.font_id, int(14 * scale), 72)
            if value:
                blf.draw(self.font_id, "■")
            else:
                blf.draw(self.font_id, "□")
            #blf.draw(self.font_id, str(value))
        
        
        if value:
            #blf.color(self.font_id, 0.3, 0.6, 0.3, alpha)
            valuecolor=get_prefs().hud_ActiveColor
        else:
            #blf.color(self.font_id, 0.6, 0.3, 0.3, alpha)
            valuecolor=get_prefs().hud_DisableColor
        blf.color(self.font_id, *valuecolor, alpha)
        
        blf.position(self.font_id, self.HUD_x + int(prop_offset * scale), self.HUD_y - int(20 * scale) - offset, 0)
        blf.size(self.font_id, int(14 * scale), 72)
        if value:
            blf.draw(self.font_id, "■")
        else:
            blf.draw(self.font_id, "□")

    # int
    elif type(value) is int:
        if shadow:
            blf.color(self.font_id, *shadow, alpha * 0.7)
            blf.position(self.font_id, self.HUD_x + int(prop_offset * scale) + 1, self.HUD_y - int(20 * scale) - offset - 1, 0)
            blf.size(self.font_id, int(20 * scale), 72)
            blf.draw(self.font_id, "%d" % (value))

        blf.color(self.font_id, *HUDcolor, alpha)
        blf.position(self.font_id, self.HUD_x + int(prop_offset * scale), self.HUD_y - int(20 * scale) - offset, 0)
        blf.size(self.font_id, int(20 * scale), 72)
        blf.draw(self.font_id, "%d" % (value))

    # float
    elif type(value) is float:
        if shadow:
            blf.color(self.font_id, *shadow, alpha * 0.7)
            blf.position(self.font_id, self.HUD_x + int(prop_offset * scale) + 1, self.HUD_y - int(20 * scale) - offset - 1, 0)
            blf.size(self.font_id, int(16 * scale), 72)
            blf.draw(self.font_id, "%.*f" % (decimal, value))

        blf.color(self.font_id, *HUDcolor, alpha)
        blf.position(self.font_id, self.HUD_x + int(prop_offset * scale), self.HUD_y - int(20 * scale) - offset, 0)
        blf.size(self.font_id, int(16 * scale), 72)
        blf.draw(self.font_id, "%.*f" % (decimal, value))

    # HINTS

    if (get_prefs().hud_hints or self.showhelp) and hint:
    #if True and hint:
        if shadow:
            blf.color(self.font_id, *shadow, 0.6 * 0.7)
            blf.position(self.font_id, self.HUD_x + int(hint_offset * scale) + 1, self.HUD_y - int(20 * scale) - offset - 1, 0)
            blf.size(self.font_id, int(11 * scale), 72)
            blf.draw(self.font_id, "%s" % (hint))

        blf.color(self.font_id, *HUDcolor, 0.6)
        blf.position(self.font_id, self.HUD_x + int(hint_offset * scale), self.HUD_y - int(20 * scale) - offset, 0)
        blf.size(self.font_id, int(11 * scale), 72)
        blf.draw(self.font_id, "%s" % (hint))


def draw_text(self, text, size, offset=0, HUDcolor=None, HUDalpha=0.5, shadow=True):
    if not HUDcolor:
        #HUDcolor = (1, 1, 1)
        HUDcolor = get_prefs().hud_Color
    shadow = (0, 0, 0)
    
    scale = 1
    scale = bpy.context.preferences.view.ui_scale * get_prefs().hud_scale

    offset = self.offset + int(offset * scale)
    self.offset = offset

    if shadow:
        blf.color(self.font_id, *shadow, HUDalpha * 0.7)
        blf.position(self.font_id, self.HUD_x + int(20 * scale) + 1, self.HUD_y - offset - 1, 0)
        blf.size(self.font_id, int(size * scale), 72)
        blf.draw(self.font_id, text)

    blf.color(self.font_id, *HUDcolor, HUDalpha)
    blf.position(self.font_id, self.HUD_x + int(20 * scale), self.HUD_y - offset, 0)
    blf.size(self.font_id, int(size * scale), 72)
    blf.draw(self.font_id, text)

def draw_end():
    bgl.glEnd()
    # restore opengl defaults
    bgl.glLineWidth(1)
    bgl.glDisable(bgl.GL_BLEND)
    bgl.glEnable(bgl.GL_DEPTH_TEST)
    bgl.glColor4f(0.0, 0.0, 0.0, 1.0)
   
  
def wrap_mouse(self, context, event, x=False, y=False):
    if x:
        if event.mouse_region_x > context.region.width - 2:
            bpy.context.window.cursor_warp(event.mouse_x - context.region.width + 2, event.mouse_y)
            self.init_mouse_x -= context.region.width

        elif event.mouse_region_x < 1:
            bpy.context.window.cursor_warp(event.mouse_x + context.region.width - 2, event.mouse_y)
            self.init_mouse_x += context.region.width

    if y:
        if event.mouse_region_y > context.region.height - 2:
            bpy.context.window.cursor_warp(event.mouse_x, event.mouse_y - context.region.height + 2)
            self.init_mouse_y -= context.region.height

        elif event.mouse_region_y < 1:
            bpy.context.window.cursor_warp(event.mouse_x, event.mouse_y + context.region.height - 2)
            self.init_mouse_y += context.region.height

def step_enum(current, items, step, loop=True):
    item_list = [item[0] for item in items]
    item_idx = item_list.index(current)

    step_idx = item_idx + step

    if step_idx >= len(item_list):
        if loop:
            step_idx = 0
        else:
            step_idx = len(item_list) - 1
    elif step_idx < 0:
        if loop:
            step_idx = len(item_list) - 1
        else:
            step_idx = 0

    return item_list[step_idx]

def get_enumprop(current, items, prop=1):
    item_list = [item[0] for item in items]
    item_idx = item_list.index(current)
    
    return items[item_idx][prop]

