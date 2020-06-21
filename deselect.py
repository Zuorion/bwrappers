#Bevel Wrapper created by Zuorion
import bpy
from bpy.props import IntProperty, FloatProperty, BoolProperty, EnumProperty
import bmesh
import math
from . hud import draw_init, draw_title, draw_prop, draw_text, wrap_mouse, step_enum, get_enumprop
from . utils import *

methoditems = [("OFFSET", "Offset", ""),
               ("WIDTH", "Width", ""),
               ("DEPTH", "Depth", ""),
               ("PERCENT", "Percent", "")]

class ZuoDeselectSettings:
    # see https://blender.stackexchange.com/questions/6520/should-an-operator-remember-its-last-used-settings-when-invoked
    _settings = {}

    def save_settings(self):
        for d in dir(self.properties):
            if d in ['bl_rna', 'rna_type', 'width', 'vertex_only','loop_slide', 'clamp_overlap']:
                continue
            try:
                self.__class__._settings[d] = self.properties[d]
            except KeyError:
                # catches __doc__ etc.
                continue

    def load_settings(self):
        # what exception could occur here??
        for d in self.__class__._settings:
            self.properties[d] = self.__class__._settings[d]


class ZuoDeselect(bpy.types.Operator, ZuoDeselectSettings):
    bl_idname = "mesh.zuo_deselect"
    bl_label = "Deselect Modal Wrapper"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Deselect"


    #method = EnumProperty(name="Method", items=methoditems, default="OFFSET")


    checker_nth: IntProperty(name="Nth element", default=1, min=1, max=30)
    checker_skip: IntProperty(name="Nth Skip", default=1, min=1, max=30)
    checker_offset: IntProperty(name="Nth Offset", default=0, min=-10, max=30)
    
    # modal
    allowmodalwidth: BoolProperty(default=True, options={'HIDDEN'})
    
    showhelp: BoolProperty(default=False, options={'HIDDEN'})
    
    def draw(self, context):
        layout = self.layout
        column = layout.column()

        
        column.prop(self, "width")

           
        #column.prop(self, "material")

    @classmethod
    def poll(cls, context):
        if context.mode == 'EDIT_MESH':
            bm = bmesh.from_edit_mesh(context.active_object.data)
            return len([v for v in bm.verts if v.select]) >= 1
        return False
        
    def draw_HUD(self, args):
        context, event = args
        draw_init(self, event)

        draw_title(self, "Vert to Circle")

        if self.nonmod:
            draw_prop(self, "Skip    »»»", self.checker_skip, offset=18, hint="scroll UP/DOWN")
        else:
            draw_prop(self, "Skip ", self.checker_skip, offset=18, hint="scroll")
        
        if self.alt:
            draw_prop(self, "Nth     »»»", self.checker_nth, offset=18, hint="ALT scroll UP/DOWN")
        else:
            draw_prop(self, "Nth ", self.checker_nth, offset=18, hint="ALT scroll")
        
        if self.shift:
            draw_prop(self, "Offset  »»»", self.checker_offset, offset=18, hint="SHIFT scroll UP/DOWN")
        else:
            draw_prop(self, "Offset ", self.checker_offset, offset=18, hint="SHIFT scroll")
        
        self.offset += 10
        
        vistext='+'*self.checker_offset+('-'*self.checker_skip+"|"*self.checker_nth)*30
        if self.checker_offset<0:
            vistext = (vistext[abs(self.checker_offset):])
        vistext = (vistext[:50]) if len(vistext) > 50 else vistext
        draw_text(self, vistext, offset=28, size=10)
        
        #HELP
        draw_text(self, "Help [H]", offset=28, size=10)
        if self.showhelp:
            draw_text(self, "[W] - resent curent value", offset=12, size=10)
            draw_text(self, "[A] - resent all values", offset=12, size=10)
            draw_text(self, "[Q] - native bevel modal", offset=12, size=10)

        
    def modal(self, context, event):
        context.area.tag_redraw()


        events = ['WHEELUPMOUSE', 'LEFT_SHIFT', 'LEFT_CTRL', 'LEFT_ALT', 'UP_ARROW', 'ONE', 'WHEELDOWNMOUSE', 'DOWN_ARROW', 'H', 'A', 'W']
        
        if event.type == "MOUSEMOVE":
            self.mouse_x = event.mouse_region_x
            self.mouse_y = event.mouse_region_y
        
        if event.type in events:

            if event.shift:
                self.shift = True
                self.alt = False
                self.nonmod = False
            elif event.alt:
                self.alt = True
                self.shift = False
                self.nonmod = False
            else:
                self.alt = False
                self.shift = False
                self.nonmod = True
            
            # CONTROL segments, method, profile preset

            if event.type in {'WHEELUPMOUSE', 'UP_ARROW', 'ONE'} and event.value == 'PRESS':
                if event.shift:
                    self.checker_offset += 1
                elif event.alt:
                    self.checker_nth += 1
                else:
                    self.checker_skip += 1

            elif event.type in {'WHEELDOWNMOUSE', 'DOWN_ARROW', 'TWO'} and event.value == 'PRESS':
                if event.shift:
                    self.checker_offset -= 1
                elif event.alt:
                    self.checker_nth -= 1
                else:
                    self.checker_skip -= 1
                    
            elif event.type == 'H' and event.value == "PRESS":
                self.showhelp = not self.showhelp
            
            elif event.type == 'A' and event.value == "PRESS":
                self.checker_offset = 0
                self.checker_nth = 0
                self.checker_skip = 0
            
            elif event.type == 'W' and event.value == "PRESS":
                if event.shift:
                    self.checker_offset = 0
                elif event.alt:
                    self.checker_nth = 0
                else:
                    self.checker_skip = 0
            
            #Fallback into regular modal
            elif event.type == 'Q' and event.value == "PRESS":
                bpy.types.SpaceView3D.draw_handler_remove(self.HUD, 'WINDOW')
                bpy.ops.ed.undo()
                return {'FINISHED'}
                
                
            # modal bevel
            try:
                ret = self.main(modal=True)
                # success
                if ret:
                    self.save_settings()
                # caught an error
                else:
                    bpy.types.SpaceView3D.draw_handler_remove(self.HUD, 'WINDOW')
                    return {'FINISHED'}
            # unexpected error
            except:
                bpy.types.SpaceView3D.draw_handler_remove(self.HUD, 'WINDOW')
                return {'FINISHED'}

        # VIEWPORT control
        elif event.type in {'MIDDLEMOUSE'}:
            self.resetmouse = True
            return {'PASS_THROUGH'}

        # FINISH

        elif event.type in {'LEFTMOUSE', 'SPACE'}:
            bpy.types.SpaceView3D.draw_handler_remove(self.HUD, 'WINDOW')
            return {'FINISHED'}

        # CANCEL

        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            self.cancel_modal()
            return {'CANCELLED'}

        return {'RUNNING_MODAL'}

    def cancel_modal(self, removeHUD=True):
        bpy.ops.ed.undo()
        if removeHUD:
            bpy.types.SpaceView3D.draw_handler_remove(self.HUD, 'WINDOW')
        bpy.ops.ed.undo_push()


    def invoke(self, context, event):
        self.load_settings()

        # save this initial mesh state, this will be used when canceling the modal and to reset it for each mousemove event
        bpy.ops.ed.undo_push()

        self.showhelp = True
        
        self.offset = 0
        self.alt = False
        self.shift = False
        self.nonmod = True
        
        try:
            ret = self.main(modal=True)
            if ret:
                self.save_settings()
            else:
                self.cancel_modal(removeHUD=False)
                return {'FINISHED'}

        except:
            return {'FINISHED'} 
            
        args = (context, event)
        self.HUD = bpy.types.SpaceView3D.draw_handler_add(self.draw_HUD, (args, ), 'WINDOW', 'POST_PIXEL')
        print("a")
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}
    
    def execute(self, context):
        try:
            self.main()
        except:
            print("crasshsh")

        return {'FINISHED'}
    
    def main(self, modal=False):
        
        if modal:
            bpy.ops.ed.undo()
            bpy.ops.ed.undo_push()
               
        bpy.ops.mesh.select_nth(skip=self.checker_skip, nth=self.checker_nth, offset=self.checker_offset)

        return True

