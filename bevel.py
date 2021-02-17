#Bevel Wrapper created by Zuorion, based in substantial part on Machin3 addon
import bpy
from bpy.props import IntProperty, FloatProperty, BoolProperty, EnumProperty
import bmesh
import math
from . hud import draw_init, draw_title, draw_prop, draw_text, wrap_mouse, step_enum, get_enumprop
from . utils import *

profilepresetitems = [("CUSTOM", "Custom", ""),
                      ("0.25", "0.25", ""),
                      ("0.5", "0.5", ""),
                      ("0.66", "0.66", ""),
                      ("0.7", "0.7", ""),
                      ("1", "1", "")]
                      
profilepresetvalueitems =  {'0': 0,
                 "0.25": 0.25,
                 "0.5": 0.5,
                 "0.66": 0.66,
                 "0.7": 0.7,
                 "1": 1.0}        

methoditems = [("OFFSET", "Offset", ""),
               ("WIDTH", "Width", ""),
               ("DEPTH", "Depth", ""),
               ("PERCENT", "Percent", "")]
               
miter_outer_items = [("SHARP", "Sharp", ""),
               ("ARC", "Arc", ""),
               ("PATCH", "Patch", "")]
               
face_strength_modeitems = [("NONE", "None", ""),
               ("ALL", "All", "All selected"),
               ("AFFECTED", "Affected", "Affected Faces"),
               ("NEW", "New", "New faces")]
               
miter_inner_items = [("SHARP", "Sharp", ""),
               ("ARC", "Arc", "")]


class ZuoBevelSettings:
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


class ZuoBevel(bpy.types.Operator, ZuoBevelSettings):
    bl_idname = "mesh.zuo_bevel"
    bl_label = "Bevel Modal Wrapper"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Create rounded Bevels [Zuo Wrapper]"



    method: EnumProperty(name="Method", items=methoditems, default="OFFSET")

    segments: IntProperty(name="Segments", default=4, min=0, max=30)
    profile: FloatProperty(name="Profile", default=0.5, min=0.0, max=1, step=0.1)
    
    
    def assign_profile_presets(self, context):
        print(self.profile_preset)
        if self.profile_preset!='CUSTOM':
            self.profile = profilepresetvalueitems[self.profile_preset]
        
    profile_preset: EnumProperty(name="Profile Presets", items=profilepresetitems, default="CUSTOM", update=assign_profile_presets)
    miter_outer: EnumProperty(name="Profile Presets", items=miter_outer_items, default="ARC")
    miter_inner: EnumProperty(name="Profile Presets", items=miter_inner_items, default="SHARP")
    face_strength_mode: EnumProperty(name="Profile Presets", items=face_strength_modeitems, default="NONE")
    harden_normals: BoolProperty(name="Clamp Overlap", default=True)
    
    vertex_only: BoolProperty(name="Vertex Only", default=False)
    clamp_overlap: BoolProperty(name="Clamp Overlap", default=True)
    loop_slide:BoolProperty(name="Loop Slide", default=True)
    width: FloatProperty(name="Offset", default=0.1, min=0, step=0.1)
    spread: FloatProperty(name="Mitter Spread", default=0.3, min=0, step=0.1)
    offset_pct: FloatProperty(name="Percent", default=25, min=0.0, max=100, step=1.0)
    
    material: IntProperty(name="Material", default=-1, min=-1, max=69)
    
    usecustomprofile: BoolProperty(name="Custom Profile", default=False)
    #custom_profile: CurveProfile(name="Profile Presets", preset="CORNICE")
    #aditional
    mergeverts: BoolProperty(name="Merge vertices", default=False)

    # modal
    allowmodalwidth : BoolProperty(default=True)
    allowmodaltension : BoolProperty(default=False)
    allowmodalmitter : BoolProperty(default=False)
    
    showhelp : BoolProperty(default=False)
    
    def draw(self, context):
        layout = self.layout
        column = layout.column()

        row = column.row()
        row.prop(self, "method", expand=True)
        column.separator()
        if self.method=="PERCENT":
            column.prop(self, "offset_pct")
        else:
            column.prop(self, "width")
        row = column.row()
        column.prop(self, "segments")
        
        row = column.row()
        row.prop(self, "profile_preset", expand=True)
        row = column.row()
        row.prop(self, "profile",slider=True)
        if self.profile_preset!="CUSTOM":
            row.enabled = False
        
        column.prop(self, "vertex_only")
        column.prop(self, "clamp_overlap")
        column.prop(self, "loop_slide")
        column.prop(self, "harden_normals")
        row = column.row()
        row.label(text="Face strenght")
        row.prop(self, "face_strength_mode", expand=True)
        row = column.row()
        row.label(text="Miter inner")
        row.prop(self, "miter_inner", expand=True)
        row = column.row()
        row.label(text="Miter outer")
        row.prop(self, "miter_outer", expand=True)
        if self.miter_inner != "SHARP":
           column.prop(self, "spread") 
           
        column.prop(self, "material")
        column.prop(self, "usecustomprofile")

    @classmethod
    def poll(cls, context):
        if context.mode == 'EDIT_MESH':
            bm = bmesh.from_edit_mesh(context.active_object.data)
            return len([e for e in bm.edges if e.select]) >= 1 or len([v for v in bm.verts if v.select]) >= 1
        return False
        
    def draw_HUD(self, args):
        context, event = args
        draw_init(self, event)

        draw_title(self, "Bevel")

        draw_prop(self, "Method", get_enumprop(self.method,methoditems), offset=0, hint="SHIFT scroll UP/DOWN,")

        self.offset += 10
        if self.method=="PERCENT":
            draw_prop(self, "Percent", self.offset_pct, offset=18, decimal=1, active=(not self.allowmodaltension and not self.allowmodalmitter), hint="move LEFT/RIGHT, reset W")
        else:       
            draw_prop(self, "Width", self.width, offset=18, decimal=3, active=(not self.allowmodaltension and not self.allowmodalmitter), hint="move LEFT/RIGHT, reset W")
        
        draw_prop(self, "Segments", self.segments, offset=20, hint="scroll UP/DOWN")
        
        if self.allowmodaltension:
            draw_prop(self, "Profile", self.profile, offset=18, decimal=2, active=self.allowmodaltension, hint="move UP/DOWN or scroll, reset Alt+W")
        else:
            draw_prop(self, "Profile", self.profile, offset=18, decimal=2, active=self.allowmodaltension, hint="adjust ALT, preset Z, X, C, V")
            
        
        draw_prop(self, "Vertex only", self.vertex_only, offset=26, hint="·A·")
        draw_prop(self, "Loop Slide", self.loop_slide, offset=18, hint="·S·")
        draw_prop(self, "Clamp Overlap", self.clamp_overlap, offset=18, hint="·D·")
        draw_prop(self, "Harden Normals", self.harden_normals, offset=18, hint="·N·")
        draw_prop(self, "Merge Verts", self.mergeverts, offset=18, hint="·M·")
        draw_prop(self, "Face Strenght", get_enumprop(self.face_strength_mode,face_strength_modeitems), offset=18, hint="·J· "+get_enumprop(self.face_strength_mode,face_strength_modeitems,2))
            
        draw_prop(self, "Mitter outer", get_enumprop(self.miter_outer,miter_outer_items), offset=18, hint="·O·")
        draw_prop(self, "Mitter inner", get_enumprop(self.miter_inner,miter_inner_items), offset=18, hint="·I·")
        if self.miter_inner != "SHARP":
            draw_prop(self, "Inner Spread", self.spread, offset=18, active=self.allowmodalmitter, hint="toggle ·P·")
        if self.material >= 0:  
            draw_prop(self, "Material", self.material, offset=20, hint="·< >·")
            
        if self.usecustomprofile:
            draw_prop(self, "Custom profile", self.usecustomprofile, offset=20, hint="·/·")
        self.offset += 10
        #HELP
        draw_text(self, "Help [H]", offset=28, size=10)
        if self.showhelp:
            draw_text(self, "[Alt] - swap value control", offset=12, size=10)
            draw_text(self, "[Q] - native bevel modal", offset=12, size=10)
            draw_text(self, "[< >] - change material", offset=12, size=10)
            #draw_text(self, "[Z] - reset value", offset=12, size=10)
        #draw_end()

        
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

        events = ['WHEELUPMOUSE', 'LEFT_SHIFT', 'LEFT_CTRL', 'LEFT_ALT', 'UP_ARROW', 'ONE', 'WHEELDOWNMOUSE', 'DOWN_ARROW', 'TWO', 'R', 'S', 'D', 'Y', 'Z', 'X', 'C', 'V', 'W', 'F', 'A', 'Q','I','O','P', 'N', 'H', 'J','M', 'PERIOD', 'COMMA', 'SLASH']

        # only consider MOUSEMOVE as a trigger for main(), when modalwidth or modaltension are actually active
        if any([self.allowmodalwidth, self.allowmodalmitter]):
            events.append('MOUSEMOVE')

        
        
        if event.type in events:
            
            
            #Save init mouse for SHIFT CTRL ALT
            if event.type == 'LEFT_SHIFT' or event.type == 'LEFT_CTRL':
                if event.value == 'PRESS' or event.value == 'RELEASE':
                    self.init_mouse_x = self.mouse_x
                    if self.allowmodalwidth:
                        if self.method=="PERCENT":
                            self.temp_offset_pct = self.offset_pct
                            if event.ctrl:
                                self.temp_offset_pct=round(self.temp_offset_pct/5)*5
                        else:
                            self.temp_width = self.width
                    elif self.allowmodalmitter:
                        self.temp_spread = self.spread
                    
            if event.type == 'LEFT_ALT':
                if event.value == 'PRESS':    
                    self.allowmodaltension = True
                elif event.value == 'RELEASE':
                    self.init_mouse_x = self.mouse_x
                    self.allowmodaltension = False
            
            
            
            # CONTROL width and tension
            if event.type == 'MOUSEMOVE':
                delta_x = self.mouse_x - self.init_mouse_x  # bigger if going to the right
                delta_y = self.mouse_y - self.init_mouse_y  # bigger if going to the up
                
                if self.allowmodalwidth:
                    wrap_mouse(self, context, event, x=True)
                    if event.alt:
                            wrap_mouse(self, context, event, y=True)
                            self.profile = delta_y * 0.001 + self.init_tension
                            self.temp_width = self.width
                            self.init_mouse_x = self.mouse_x
                            self.temp_offset_pct = self.offset_pct
                    elif self.method=="PERCENT":
                        if event.shift:  
                            self.offset_pct = self.temp_offset_pct+delta_x * 0.005
                        elif event.ctrl:
                            self.offset_pct = self.temp_offset_pct+round(delta_x * 0.01)*5
                        else:
                            self.offset_pct = self.temp_offset_pct+delta_x * 0.1
                    else:                      
                        if event.shift:  
                            self.width = self.temp_width+delta_x   * 0.005 * self.factor
                        elif event.ctrl:
                            self.width = (self.temp_width+delta_x  * 0.05 * self.factor)  
                        else:
                            self.width = self.temp_width+delta_x * self.factor * 0.1
                elif self.allowmodalmitter:
                    wrap_mouse(self, context, event, x=True)
                    if event.shift:
                        self.spread = self.temp_spread+delta_x   * 0.005 * self.factor
                    elif event.ctrl:
                        self.spread = self.temp_spread+delta_x  * 0.01 * self.factor
                    else:
                        self.spread = self.temp_spread+delta_x * self.factor * 0.05
                    
            
            
            # CONTROL segments, method, profile preset

            elif event.type in {'WHEELUPMOUSE', 'UP_ARROW', 'ONE'} and event.value == 'PRESS':
                if event.shift and event.ctrl:
                    bpy.ops.view3d.zoom(delta=1, use_cursor_init=True)
                elif event.shift:
                    self.method = step_enum(self.method, methoditems, 1)
                elif event.alt:
                    self.profile_preset = step_enum(self.profile_preset, profilepresetitems, 1)
                    if self.profile_preset=="CUSTOM":
                        self.profile_preset = step_enum(self.profile_preset, profilepresetitems, 1)
                    self.init_tension = self.profile
                    self.init_mouse_y = self.mouse_y
                elif event.ctrl:
                    self.profile += 0.05
                else:
                    self.segments += 1

            elif event.type in {'WHEELDOWNMOUSE', 'DOWN_ARROW', 'TWO'} and event.value == 'PRESS':
                if event.shift and event.ctrl:
                    bpy.ops.view3d.zoom(delta=-1, use_cursor_init=True)
                elif event.shift:
                    self.method = step_enum(self.method, methoditems, -1)
                elif event.alt:
                    self.profile_preset = step_enum(self.profile_preset, profilepresetitems, -1)
                    if self.profile_preset=="CUSTOM":
                        self.profile_preset = step_enum(self.profile_preset, profilepresetitems, -1)
                        
                    
                    self.init_tension = self.profile
                    self.init_mouse_y = self.mouse_y
                elif event.ctrl:
                    self.profile -= 0.05
                else:
                    self.segments -= 1



            # SET profile presets

            elif (event.type == 'Y' and event.value == "PRESS") or (event.type == 'Z' and event.value == "PRESS"):
                self.profile_preset = "0.25"

            elif event.type == 'X' and event.value == "PRESS":
                self.profile_preset = "0.5"

            elif event.type == 'C' and event.value == "PRESS":
                self.profile_preset = "0.7"

            elif event.type == 'V' and event.value == "PRESS":
                self.profile_preset = "1"

            # Reset modal width and profile
            elif event.type == 'W' and event.value == "PRESS":
                if event.alt:
                    self.init_mouse_y = self.mouse_y
                    self.profile=0.5
                    self.init_tension = 0.5
                else:
                    if self.allowmodalmitter:
                        self.init_mouse_x = self.mouse_x
                        self.spread = 0.0
                        self.temp_spread = 0.0
                    else:
                        self.init_mouse_x = self.mouse_x
                        self.width = 0
                        self.temp_width = 0
                        self.temp_offset_pct = 25

            elif event.type == 'F' and event.value == "PRESS":
                self.allowmodaltension = not self.allowmodaltension

            # TOGGLE bevel options

            elif event.type == 'A' and event.value == "PRESS":
                self.vertex_only = not self.vertex_only

            elif event.type == 'S' and event.value == "PRESS":
                self.loop_slide = not self.loop_slide

            elif event.type == 'D' and event.value == "PRESS":
                self.clamp_overlap = not self.clamp_overlap
            elif event.type == 'H' and event.value == "PRESS":
                self.showhelp = not self.showhelp
            elif event.type == 'N' and event.value == "PRESS":
                self.harden_normals = not self.harden_normals
            elif event.type == 'I' and event.value == "PRESS":
                self.miter_inner = step_enum(self.miter_inner, miter_inner_items, 1)
                if self.miter_inner == "SHARP":
                    self.allowmodalmitter = False
                    self.allowmodalwidth = True
                    

            elif event.type == 'O' and event.value == "PRESS":
                self.miter_outer = step_enum(self.miter_outer, miter_outer_items, 1)
                
            elif event.type == 'J' and event.value == "PRESS":
                self.face_strength_mode = step_enum(self.face_strength_mode, face_strength_modeitems, 1)
            
            #Modal mitter s
            elif event.type == 'P' and event.value == "PRESS":
                if self.miter_inner != "SHARP":
                    self.allowmodalmitter = not self.allowmodalmitter
                    self.allowmodalwidth = not self.allowmodalwidth
                    self.init_mouse_x = self.mouse_x
                    self.temp_width = self.width
                    
            #/
            elif event.type == 'SLASH' and event.value == "PRESS":
                self.usecustomprofile = not self.usecustomprofile
            
            
            #Material <> » ,.
            elif event.type == 'PERIOD' and event.value == "PRESS":
                self.material += 1
                
            elif event.type == 'COMMA' and event.value == "PRESS":
                self.material -= 1
            
            #Aditional
            elif event.type == 'M' and event.value == "PRESS":
                self.mergeverts = not self.mergeverts
            
            #Fallback into regular modal
            elif event.type == 'Q' and event.value == "PRESS":
                bpy.types.SpaceView3D.draw_handler_remove(self.HUD, 'WINDOW')
                bpy.ops.ed.undo()
                bpy.ops.mesh.bevel('INVOKE_DEFAULT', True, offset_type=self.method, offset=self.width, segments=self.segments, profile=self.profile, vertex_only=self.vertex_only, clamp_overlap=self.clamp_overlap, loop_slide=self.loop_slide, material=self.material)
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

        self.init_tension = self.profile
        self.temp_width = 0
        self.temp_offset_pct = 25
        self.temp_spread = 0.3
        self.offset = 0
        self.width = 0
        self.spread=0.3
        self.resetmouse = False
        self.showhelp = True
        
        
        
        #Calculate factor for mouse move values
        self.active = context.active_object
        self.active.update_from_editmode()
        self.initbm = bmesh.new()
        self.initbm.from_mesh(self.active.data)
        self.factor = get_zoom_factor(self.active.matrix_world, [v.co for v in self.initbm.verts if v.select])
        #bm = bmesh.from_edit_mesh(context.active_object.data)
        
        #if only verts
        if len([e for e in self.initbm.edges if e.select]) == 0:
            self.vertex_only = True
        
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
               
        
        if self.miter_inner != "SHARP":
            bpy.ops.mesh.bevel(True, offset_type=self.method,
                               offset=self.width,
                               segments=self.segments,
                               profile=self.profile,
                               affect='EDGES',
                               clamp_overlap=self.clamp_overlap,
                               loop_slide=self.loop_slide,
                               miter_inner=self.miter_inner,
                               miter_outer=self.miter_outer,
                               offset_pct=self.offset_pct,
                               harden_normals=self.harden_normals,
                               face_strength_mode=self.face_strength_mode,
                               spread=self.spread,
                               material=self.material)
        else:
            bpy.ops.mesh.bevel(True, offset_type=self.method,
                               offset=self.width,
                               segments=self.segments,
                               profile=self.profile,
                               affect='EDGES',
                               clamp_overlap=self.clamp_overlap,
                               loop_slide=self.loop_slide,
                               miter_inner=self.miter_inner,
                               miter_outer=self.miter_outer,
                               offset_pct=self.offset_pct,
                               harden_normals=self.harden_normals,
                               face_strength_mode=self.face_strength_mode,
                               material=self.material)
        if self.mergeverts:
            bpy.ops.mesh.select_more(use_face_step=False)
            bpy.ops.mesh.remove_doubles(threshold=0.0001)


        return True

