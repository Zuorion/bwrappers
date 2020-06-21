# ***** BEGIN GPL LICENSE BLOCK *****
#
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ***** END GPL LICENCE BLOCK *****

bl_info = {
    "name": "Dumb Operator Wrappers",
    "author": "Zuorion",
    "version": (0, 1),
    "blender": (2, 81, 0),
    "location": "",
    "description": "Modal Wrappers for: Bevel, Inset, OffsetEdges done via operator+REDO",
    "warning": "",
    "wiki_url": "https://github.com/Zuorion/bwrappers/wiki",
    "category": "Mesh",
    }

import bpy  
from bpy.props import IntProperty, StringProperty, CollectionProperty, BoolProperty, EnumProperty
import rna_keymap_ui

from .bevel import *
from .offset import *
from .Vtocircle import *
from .deselect import *
#from .ripoffset import *


def get_hotkey_entry_item(km, kmi_name):
    for i, km_item in enumerate(km.keymap_items):
        if km.keymap_items.keys()[i] == kmi_name:
            return km_item
    return None

class AddonPreferences(bpy.types.AddonPreferences):
    bl_idname = __name__
    
    
    hud_Color:bpy.props.FloatVectorProperty(name="HUD",description="HUD Color", default=(1.0,1.0,1.0),subtype='COLOR')
    hud_ActiveColor:bpy.props.FloatVectorProperty(name="Actived",description="Activated bool property color", default=(0.3,0.6,0.3),subtype='COLOR')
    hud_DisableColor:bpy.props.FloatVectorProperty(name="Disabled",description="Disabled bool property color", default=(0.6,0.3,0.3),subtype='COLOR')
    hud_scale:bpy.props.FloatProperty(name="HUD Scale", description="HUD Scale factor", min=0.1, step=0.05, default=1.0)
    hud_hints:bpy.props.BoolProperty(name="Always show hints",description="Always show help hints next to property, if off hints can be toogled by [H]", default=True)
    hud_StickSide: bpy.props.EnumProperty(name="HUD location",description="HUD anchor location",
        items=(
            ('TOP', "Top", ""),
            ('BOTTOM', "Bottom", ""),
            ('MOUSE', "Mouse Start", ""),
            ('MOUSEFOLLOW', "Follow Mouse", ""),
        ), default='TOP')
    
    def draw(self, context):
        layout = self.layout
        wm = bpy.context.window_manager
        
        box = layout.box()
        box.label(text="HUD display Options")
        URow = box.row(align=True)
        URow.prop(self, "hud_Color")
        URow.prop(self, "hud_ActiveColor")
        URow.prop(self, "hud_DisableColor")
        box.prop(self, "hud_scale")
        URow = box.row(align=True)
        URow.prop(self, "hud_hints")
        URow.prop(self, "hud_StickSide")
        
        
        box = layout.box()
        split = box.split()
        col = split.column()
        col.label(text='Hotkeys')
        col.separator()
        kc = wm.keyconfigs.user
        km = kc.keymaps['Mesh']
        kmi = get_hotkey_entry_item(km, 'mesh.zuo_vert2circle')
        
        
        col.context_pointer_set("keymap", km)
        rna_keymap_ui.draw_kmi([], kc, km, kmi, col, 0)
        
        kmi = get_hotkey_entry_item(km, 'mesh.zuo_offsetedges')
        col.context_pointer_set("keymap", km)
        rna_keymap_ui.draw_kmi([], kc, km, kmi, col, 0)
        
        kmi = get_hotkey_entry_item(km, 'mesh.zuo_bevel')
        col.context_pointer_set("keymap", km)
        rna_keymap_ui.draw_kmi([], kc, km, kmi, col, 0)
        
        box = layout.box()
        split = box.split()
        col = split.column()
        col.label(text='Info')
        col.separator()
        col.operator("wm.url_open", text="Documentation").url = "https://github.com/Zuorion/bwrappers/wiki"
        col.operator("wm.url_open", text="Tutorial").url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ" 
        col.operator("wm.url_open", text="MESHmachin3 addon").url = "https://machin3.io/MESHmachine/docs/"
         
            
classes = (
    ZuoBevel,
    ZuoOffsetEdges,
    #ZuoInset
    #ZuoRipOffsetEdges,
    AddonPreferences,
    ZuoVert2Circle,
    ZuoDeselect
)


addon_keymaps = []

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
        
    wm = bpy.context.window_manager
    if wm.keyconfigs.addon:
        # As Ctrl + J
        km = wm.keyconfigs.addon.keymaps.new(name='Mesh')
        kmi = km.keymap_items.new('mesh.zuo_vert2circle', 'V', 'PRESS', ctrl=True, shift=True, alt=True)
        kmi.active = False
        
        kmi = km.keymap_items.new('mesh.zuo_offsetedges', 'O', 'PRESS', ctrl=True, alt=True)
        kmi.active = False
        
        kmi = km.keymap_items.new('mesh.zuo_bevel', 'B', 'PRESS', ctrl=True, alt=True)
        kmi.active = False
        addon_keymaps.append((km, kmi))


def unregister():

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
        
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        for km, kmi in addon_keymaps:
            km.keymap_items.remove(kmi)
    addon_keymaps.clear()

if __name__ == "__main__":
    register()

