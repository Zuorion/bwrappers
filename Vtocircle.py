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

class ZuoV2CirclelSettings:
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


class ZuoVert2Circle(bpy.types.Operator, ZuoV2CirclelSettings):
    bl_idname = "mesh.zuo_vert2circle"
    bl_label = "Vert to Circle Modal Wrapper"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Create circle from vert using Bevel and Looptols"



    #method = EnumProperty(name="Method", items=methoditems, default="OFFSET")

    segments: IntProperty(name="Division", default=4, min=1, max=30)
    
    width: FloatProperty(name="Offset", default=0.1, min=0.000001, step=0.1)

    looptools_circle: BoolProperty(name="LT Circularize", default=False)
    
    checker: BoolProperty(default=False, name="Deselect")
    checker_nth: IntProperty(name="Nth element", default=1, min=1, max=30)
    checker_skip: IntProperty(name="Nth Skip", default=1, min=1, max=30)
    checker_offset: IntProperty(name="Nth Offset", default=0, min=1, max=30)
    
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
        draw_init(self, args)

        draw_title(self, "Vert to Circle")


        draw_prop(self, "Width", self.width, offset=18, decimal=3, active=True, hint="move LEFT/RIGHT, reset W")
        draw_prop(self, "Division", self.segments, offset=18, hint="scroll UP/DOWN, resset Alt+W")
        draw_prop(self, "Circularize", self.looptools_circle, offset=18, active=self.looptools_exists, hint="·S· Looptools circularize")
        
        draw_prop(self, "Checker", self.checker, offset=18, active=self.looptools_exists, hint="·D· Checker")
        if self.checker:
            draw_prop(self, "Skip", self.checker_skip, offset=18, hint="CTRL scroll UP/DOWN")
            draw_prop(self, "Nth", self.checker_nth, offset=18, hint="ALT scroll UP/DOWN")
            draw_prop(self, "Offset", self.checker_offset, offset=18, hint="SHIFT scroll UP/DOWN")
        
        self.offset += 10
        #HELP
        draw_text(self, "Help [H]", offset=28, size=10)
        if self.showhelp:
            draw_text(self, "[Alt] - swap value control", offset=12, size=10)
            draw_text(self, "[Q] - native bevel modal", offset=12, size=10)

        
    def modal(self, context, event):
        context.area.tag_redraw()

        # update mouse postion for HUD
        if event.type == "MOUSEMOVE":
            self.mouse_x = event.mouse_region_x
            self.mouse_y = event.mouse_region_y
            
        if self.resetmouse:
            self.init_mouse_x = self.mouse_x
            self.temp_width = self.width
            self.resetmouse = False

        events = ['WHEELUPMOUSE', 'LEFT_SHIFT', 'LEFT_CTRL', 'LEFT_ALT', 'UP_ARROW', 'ONE', 'WHEELDOWNMOUSE', 'DOWN_ARROW', 'TWO', 'R', 'S', 'D']

        # only consider MOUSEMOVE as a trigger for main(), when modalwidth or modaltension are actually active
        if any([self.allowmodalwidth]):
            events.append('MOUSEMOVE')

        
        
        if event.type in events:
            
            
            #Save init mouse for SHIFT CTRL ALT
            if event.type == 'LEFT_SHIFT' or event.type == 'LEFT_CTRL':
                if event.value == 'PRESS' or event.value == 'RELEASE':
                    self.init_mouse_x = self.mouse_x
                    self.temp_width = self.width
            
            # CONTROL width and tension
            if event.type == 'MOUSEMOVE':
                delta_x = self.mouse_x - self.init_mouse_x  # bigger if going to the right
                delta_y = self.mouse_y - self.init_mouse_y  # bigger if going to the up
                
                if self.allowmodalwidth:
                    wrap_mouse(self, context, event, x=True)
                    if event.shift:  
                        self.width = self.temp_width+delta_x   * 0.001 * self.factor
                    elif event.ctrl:
                        self.width = self.temp_width+delta_x  * 0.05 * self.factor  
                    else:
                        self.width = self.temp_width+delta_x * self.factor * 0.1
                    
            
            
            # CONTROL segments, method, profile preset

            elif event.type in {'WHEELUPMOUSE', 'UP_ARROW', 'ONE'} and event.value == 'PRESS':
                if event.shift:
                    self.checker_offset += 1
                elif event.alt:
                    self.checker_nth += 1
                elif event.ctrl:
                    self.checker_skip += 1
                else:
                    self.segments += 1

            elif event.type in {'WHEELDOWNMOUSE', 'DOWN_ARROW', 'TWO'} and event.value == 'PRESS':
                if event.shift:
                    self.checker_offset -= 1
                elif event.alt:
                    self.checker_nth -= 1
                elif event.ctrl:
                    self.checker_skip -= 1
                else:
                    self.segments -= 1

            elif event.type == 'S' and event.value == "PRESS":
                if addon_exists("mesh_looptools"):
                    self.looptools_circle = not self.looptools_circle
            
            elif event.type == 'D' and event.value == "PRESS":
                self.checker = not self.checker
                    
            elif event.type == 'W' and event.value == "PRESS":
                if event.alt:
                    self.segments=1
                else:
                    self.init_mouse_x = self.mouse_x
                    self.width = 0
                    self.temp_width = 0
            
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

        
        # mouse positions
        self.mouse_x = self.init_mouse_x = self.fixed_mouse_x = event.mouse_region_x
        self.mouse_y = self.init_mouse_y = self.fixed_mouse_y = event.mouse_region_y

        self.temp_width = 0
        self.width = 0
        self.resetmouse = False
        self.showhelp = True
        
        self.looptools_exists = addon_exists("mesh_looptools")
        if not self.looptools_exists:
            self.looptools_circle = False
            
        #Calculate factor for mouse move values
        self.active = context.active_object
        self.active.update_from_editmode()
        self.initbm = bmesh.new()
        self.initbm.from_mesh(self.active.data)
        self.factor = get_zoom_factor(self.active.matrix_world, [v.co for v in self.initbm.verts if v.select])
        
        try:
            ret = self.main(modal=True)
            if ret:
                self.save_settings()
            else:
                self.cancel_modal(removeHUD=False)
                return {'FINISHED'}

        except:
            return {'FINISHED'}  
        args = (self, event)
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
               
        if self.checker:
            bpy.ops.mesh.select_nth(skip=self.checker_skip, nth=self.checker_nth, offset=self.checker_offset)

        bpy.ops.mesh.bevel(offset=self.width, profile=0.085, segments=self.segments, clamp_overlap=True, vertex_only=True)
        bpy.ops.mesh.dissolve_faces()
        bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')
        
        if self.looptools_circle:
            bpy.ops.mesh.looptools_circle(custom_radius=False, fit='best', flatten=True, influence=100, lock_x=False, lock_y=False, lock_z=False, regular=True)

        return True

