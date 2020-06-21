#Offset Wrapper created by Zuorion, based in substantial part on Machin3 addon
import bpy
from bpy.props import IntProperty, FloatProperty, BoolProperty, EnumProperty
import bmesh
import math
from . hud import draw_init, draw_end, draw_title, draw_prop, draw_text, wrap_mouse, step_enum, get_enumprop
from . utils import *

geometry_mode_items = [("offset", "Offset", "Offset edges"),
               ("extrude", "Extrude", "Extrude edges"),
               ("move", "Move", "Move selected edges")]
               
depth_modeitems=[('angle', "Angle", "Angle"),
               ('depth', "Depth", "Depth")]
                       

class ZuoOffsetSettings:
    # see https://blender.stackexchange.com/questions/6520/should-an-operator-remember-its-last-used-settings-when-invoked
    _settings = {}

    def save_settings(self):
        for d in dir(self.properties):
            if d in ['bl_rna', 'rna_type', 'width', 'angle', 'depth_mode', 'depth']:
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


class ZuoOffsetEdges(bpy.types.Operator, ZuoOffsetSettings):
    bl_idname = "mesh.zuo_offsetedges"
    bl_label = "OffsetEdges Modal Wrapper"
    bl_options = {'REGISTER'}
    bl_description = "Offset Edges [Modal Wrapper]"
  
    geometry_mode: EnumProperty(name="Geometory mode", items=geometry_mode_items, default='offset')
    width: FloatProperty(name="Width", default=.2, precision=4, step=1)
    flip_width: BoolProperty(name="Flip Width", default=False, description="Flip width direction")
    # hidden
    depth: FloatProperty(name="Depth", default=.0, precision=4, step=1)
    depth_mode: EnumProperty(name="Depth mode", items=depth_modeitems, default='angle')
    angle: FloatProperty(name="Angle", default=0, precision=3, step=100, min=-2*pi, max=2*pi, subtype='ANGLE', description="Angle")
    follow_face : BoolProperty(
        name="Follow Face", default=False,
        description="Offset along faces around")
    mirror_modifier : BoolProperty(
        name="Mirror Modifier", default=False,
        description="Take into account of Mirror modifier")
    edge_rail : BoolProperty(
        name="Edge Rail", default=False,
        description="Align vertices along inner edges")
    edge_rail_only_end : BoolProperty(
        name="Edge Rail Only End", default=False,
        description="Apply edge rail to end verts only")
    threshold : FloatProperty(
        name="Flat Face Threshold", default=radians(0.05), min=0, max=radians(90), precision=5,
        step=1.0e-4, subtype='ANGLE',
        description="If difference of angle between two adjacent faces is "
                    "below this value, those faces are regarded as flat.",
        options={'HIDDEN'})
    allowmodalwidth : BoolProperty(default=True,options={'HIDDEN'})
    allowmodaldepth : BoolProperty(default=False,options={'HIDDEN'})
    allowmodalthreshold : BoolProperty(default=False,options={'HIDDEN'})
    showhelp : BoolProperty(default=False,options={'HIDDEN'})
    
    
    def change_depth_mode(self):
        if self.depth_mode != 'angle':
            self.width, self.angle = self.depth_to_angle(self.width, self.depth)
        else:
            self.width, self.depth = self.angle_to_depth(self.width, self.angle)
        self.depth_mode = step_enum(self.depth_mode, depth_modeitems, 1) 
    def angle_to_depth(self, width, angle):
        """Returns: (converted_width, converted_depth)"""
        return width * cos(angle), width * sin(angle)


    def depth_to_angle(self, width, depth):
        """Returns: (converted_width, converted_angle)"""
        ret_width = sqrt(width * width + depth * depth)

        if width:
            ret_angle = atan(depth / width)
        elif depth == 0:
            ret_angle = 0
        elif depth > 0:
            ret_angle = ANGLE_90
        elif depth < 0:
            ret_angle = -ANGLE_90

        return ret_width, ret_angle
    
    


    @classmethod
    def poll(cls, context):
        bm = bmesh.from_edit_mesh(context.active_object.data)
        return len([e for e in bm.edges if e.select]) >= 1
    
    def draw(self, context):
        layout = self.layout
        layout.prop(self, 'geometry_mode', text="")
        row = layout.row(align=True)
        row.prop(self, 'width')
        layout.row().prop(self, 'depth_mode', expand=True)
        if self.depth_mode == 'angle':
            d_mode = 'angle'
            flip = 'flip_angle'
        else:
            d_mode = 'depth'
            flip = 'flip_depth'
        row = layout.row(align=True)
        row.prop(self, d_mode)
        row.prop(self, flip, icon='ARROW_LEFTRIGHT', icon_only=True)
        if self.depth_mode == 'angle':
            layout.row().prop(self, 'angle_presets', text="Presets", expand=True)

        layout.separator()

        layout.prop(self, 'follow_face')

        row = layout.row()
        row.prop(self, 'edge_rail')
        if self.edge_rail:
            row.prop(self, 'edge_rail_only_end', text="OnlyEnd", toggle=True)

        layout.prop(self, 'mirror_modifier')

        #layout.operator('mesh.offset_edges', text='Repeat')

        if self.follow_face:
            layout.separator()
            layout.prop(self, 'threshold', text='Threshold')
        #row.prop(self, 'flip_width', icon='ARROW_LEFTRIGHT', icon_only=True)
    
    def draw_HUD(self, args):
        context, event = args
        draw_init(self, args)
        draw_title(self, "Offset Edges")
        draw_prop(self, "Method", get_enumprop(self.geometry_mode,geometry_mode_items), offset=0, hint="SHIFT scroll UP/DOWN")
        self.offset += 10
        draw_prop(self, "Width", self.width, offset=18, decimal=3, active=self.allowmodalwidth, hint="[A] Change Modal Value")
        if self.depth_mode == 'angle':
            draw_prop(self, "Angle", math.degrees(self.angle), offset=20, decimal=1, active=self.allowmodaldepth, hint="[D] Change to Depth mode, ALT Scroll")
        else:
            draw_prop(self, "Depth", self.depth, offset=20, decimal=3, active=self.allowmodaldepth, hint="[D] Change to Width mode")
        draw_prop(self, "Follow Face", self.follow_face, offset=26, hint="[F]")
        if self.follow_face:
            draw_prop(self, "↳ Threshold", math.degrees(self.threshold), decimal=6, active=self.allowmodalthreshold, offset=18, hint="[T]")
            self.offset += 5
            
            
        draw_prop(self, "Edge Rail", self.edge_rail, offset=18, hint="[E]")
        if self.edge_rail:
            draw_prop(self, "↳ Only Edges", self.edge_rail_only_end, offset=18, hint="[R]")
            self.offset += 5
        
        
        draw_prop(self, "Mirror modifier", self.mirror_modifier, offset=18, hint="[M]")
        self.offset += 10
        
        
        draw_text(self, "Help [H]", offset=28, size=10)
        if self.showhelp:
            draw_text(self, "[Alt] - swap value control", offset=12, size=10)
            draw_text(self, "[S] - toggle value control", offset=12, size=10)
            draw_text(self, "[X] - invert value", offset=12, size=10)
            draw_text(self, "[Z] - reset value", offset=12, size=10)
        
        

        #draw_end()

        
    def modal(self, context, event):
        context.area.tag_redraw()

        # update mouse postion for HUD
        if event.type == "MOUSEMOVE":
            self.mouse_x = event.mouse_region_x
            self.mouse_y = event.mouse_region_y

        events = ['WHEELUPMOUSE', 'LEFT_SHIFT', 'LEFT_CTRL', 'LEFT_ALT', 'UP_ARROW', 'ONE', 'WHEELDOWNMOUSE', 'DOWN_ARROW', 'TWO', 'A', 'S', 'D', 'F', 'W', 'E', 'R', 'Z', 'X', 'M', 'T' , 'H','C','V']
        # only consider MOUSEMOVE as a trigger for main(), when modalwidth or modaltension are actually active
        print("aaaa")
        if any([self.allowmodalwidth, self.allowmodaldepth, self.allowmodalthreshold]):
            events.append('MOUSEMOVE')
        
        
        if event.type in events:
            print(event.type)
            
            #Save init mouse for SHIFT
            if event.type == 'LEFT_SHIFT' or event.type == 'LEFT_CTRL':
                if event.value == 'PRESS' or event.value == 'RELEASE':
                    self.init_mouse_x = self.mouse_x
                    if self.allowmodalwidth:
                        self.temp_modalvalue = self.width
                    else:
                        if self.depth_mode == 'angle':
                            self.temp_modalvalue = self.angle
                        else:
                            self.temp_modalvalue = self.depth
                    
            if event.type == 'LEFT_ALT':
                if event.value == 'PRESS':
                    self.init_mouse_x = self.mouse_x
                    if self.allowmodalwidth:
                        if self.depth_mode == 'angle':
                            self.temp_modalvalue = self.angle
                        else:
                            self.temp_modalvalue = self.depth
                    else:
                        self.temp_modalvalue = self.width
                    self.allowmodaldepth = not self.allowmodaldepth
                    self.allowmodalwidth = not self.allowmodalwidth
                    
                if event.value == 'RELEASE':
                    self.init_mouse_x = self.mouse_x
                    self.allowmodaldepth = not self.allowmodaldepth
                    self.allowmodalwidth = not self.allowmodalwidth
                    if self.allowmodalwidth:
                        self.temp_modalvalue = self.width
                    else:
                        if self.depth_mode == 'angle':
                            self.temp_modalvalue = self.angle
                        else:
                            self.temp_modalvalue = self.depth
                    
            if self.resetmouse:
                self.init_mouse_x = self.mouse_x
                self.resetmouse=False
                
            # CONTROL width and depth
            if event.type == 'MOUSEMOVE':
                delta_x = self.mouse_x - self.init_mouse_x  # bigger if going to the right
                delta_y = self.mouse_y - self.init_mouse_y  # bigger if going to the up
                
                if self.allowmodalthreshold:
                    wrap_mouse(self, context, event, x=True)
                    self.threshold = delta_x * delta_x * 0.00000001
                    
                elif self.allowmodalwidth:
                    wrap_mouse(self, context, event, x=True)
                    if event.shift:
                        self.width = self.temp_modalvalue+(delta_x * 0.001)* self.factor
                    elif event.ctrl:
                        self.width = self.temp_modalvalue+(delta_x * 1 )* self.factor
                    else:
                        self.width = self.temp_modalvalue+(delta_x * 0.1)* self.factor
                        
                elif self.allowmodaldepth:
                    wrap_mouse(self, context, event, x=True)
                    if self.depth_mode == 'angle':
                        if (event.shift and event.ctrl):
                            self.angle = radians((round(math.degrees(self.temp_modalvalue+delta_x*0.01)/90)*90)%360)
                        elif event.ctrl:
                            self.angle = radians((round(math.degrees(self.temp_modalvalue+delta_x*0.01)/15)*15)%360)
                        elif event.shift:
                            self.angle = (self.temp_modalvalue+(delta_x * 0.0005))
                        else:
                            self.angle = radians(round(math.degrees(self.temp_modalvalue+delta_x*0.01))%360)
                        
                        if self.angle>pi: self.angle=self.angle -pi-pi
                    else:
                        if event.shift:
                            shiftfactor = 0.01
                        else:
                            shiftfactor = 0.1
                            
                        if event.ctrl:
                            self.depth = self.temp_modalvalue+round(delta_x * self.factor * shiftfactor)
                        else:
                            self.depth = self.temp_modalvalue+(delta_x * self.factor * shiftfactor)
                
                
            # CONTROL Scroll
            elif event.type in {'WHEELUPMOUSE', 'UP_ARROW', 'ONE'} and event.value == 'PRESS':
                if event.shift:
                    self.geometry_mode = step_enum(self.geometry_mode, geometry_mode_items, 1)
                if event.alt:
                    if self.depth_mode == 'angle':
                        #self.angle_presets = step_enum(self.angle_presets, anglepresetitems, 1)
                        self.angle = radians(round(math.degrees(self.angle)/15)*15)+radians(15)
                        self.init_mouse_x = self.mouse_x
                        if self.allowmodaldepth:
                            self.temp_modalvalue = self.angle
                elif event.ctrl:
                    if self.depth_mode == 'angle':
                        self.angle = self.angle + radians(1)
                    else:
                        self.depth = self.depth + self.factor * 10
                else:
                    if self.depth_mode == 'angle':
                        self.angle = self.angle + radians(1)
                    else:
                        self.depth = self.depth + self.factor * 0.1

            elif event.type in {'WHEELDOWNMOUSE', 'DOWN_ARROW', 'TWO'} and event.value == 'PRESS':
                if event.shift:
                    self.geometry_mode = step_enum(self.geometry_mode, geometry_mode_items, -1)
                if event.alt:
                    if self.depth_mode == 'angle':
                        self.angle = radians(round(math.degrees(self.angle)/15)*15)-radians(15)
                        self.init_mouse_x = self.mouse_x
                        if self.allowmodaldepth:
                            self.temp_modalvalue = self.angle
                elif event.ctrl:
                    if self.depth_mode == 'angle':
                        self.angle = self.angle - radians(5)
                    else:
                        self.depth = self.depth - self.factor * 10
                else:
                    if self.depth_mode == 'angle':
                        self.angle = self.angle - radians(1)
                    else:
                        self.depth = self.depth - self.factor * 1
            
            # Reset modal value
            elif event.type == 'Z' and event.value == "PRESS":
                self.init_mouse_x = self.mouse_x
                if self.allowmodalwidth:
                    self.temp_modalvalue = 0
                elif self.allowmodaldepth:              
                    if self.depth_mode == 'angle':
                        self.temp_modalvalue = 0
                    else:
                        self.temp_modalvalue = 0
            
            # Preset 90
            elif event.type == 'C' and event.value == "PRESS":
                if self.allowmodaldepth:    
                        self.init_mouse_x = self.mouse_x
                        
                if self.depth_mode == 'angle':
                    self.angle = radians (90)
                    if self.allowmodaldepth:    
                        self.init_mouse_x = self.mouse_x
                        self.temp_modalvalue = self.angle
                    
            
            elif event.type == 'V' and event.value == "PRESS":
                if self.allowmodaldepth:    
                        self.init_mouse_x = self.mouse_x
                        
                if self.depth_mode == 'angle':
                    self.angle = 0
                    if self.allowmodaldepth:    
                        self.init_mouse_x = self.mouse_x
                        self.temp_modalvalue = self.angle

            
            # Invert modal value
            elif event.type == 'X' and event.value == "PRESS":
                self.init_mouse_x = self.mouse_x
                if self.allowmodalwidth:
                    self.temp_modalvalue = self.width * -1
                elif self.allowmodaldepth:              
                    if self.depth_mode == 'angle':
                        self.temp_modalvalue = self.angle* -1
                    else:
                        self.temp_modalvalue = self.depth* -1
            #Change Depth <-> Angle Mode
            elif event.type == 'D' and event.value == "PRESS":
                self.change_depth_mode()
                
            #Follow Face
            elif event.type == 'F' and event.value == "PRESS":
                self.follow_face = not self.follow_face
            
            #Mirror Modifier support
            elif event.type == 'M' and event.value == "PRESS":
                self.mirror_modifier = not self.mirror_modifier
            
            #Help
            elif event.type == 'H' and event.value == "PRESS":
                self.showhelp = not self.showhelp
            
            #Edge Rail and only
            elif event.type == 'E' and event.value == "PRESS":
                self.edge_rail = not self.edge_rail 
            elif event.type == 'R' and event.value == "PRESS":
                if self.edge_rail:
                    self.edge_rail_only_end = not self.edge_rail_only_end
            
            #Enable vertical Threshold modal
            elif event.type == 'T' and event.value == 'PRESS':
                if self.follow_face:
                    if not self.allowmodalthreshold:
                        self.init_mouse_x = self.mouse_x
                        self.allowmodalthreshold = True
                        self.allowmodaldepth = False
                        self.allowmodalwidth = False
                    else:
                        self.allowmodalthreshold = False
                        self.allowmodalwidth = True
                        self.init_mouse_x = self.mouse_x
                        if self.allowmodalwidth:
                            self.temp_modalvalue = self.width
                        else:              
                            if self.depth_mode == 'angle':
                                self.temp_modalvalue = self.angle
                            else:
                                self.temp_modalvalue = self.depth
                
            #Flip modal control
            elif event.type == 'S' and event.value == "PRESS": 
                self.allowmodaldepth = not self.allowmodaldepth
                self.allowmodalwidth = not self.allowmodalwidth
                self.init_mouse_x = self.mouse_x
                if self.allowmodalwidth:
                    self.temp_modalvalue = self.width
                else:
                    if self.depth_mode == 'angle':
                        self.temp_modalvalue = self.angle
                    else:
                        self.temp_modalvalue = self.depth
                
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
            self.init_mouse_x = self.mouse_x
            if self.allowmodalwidth:
                    self.temp_modalvalue = self.width
            else:
                if self.depth_mode == 'angle':
                    self.temp_modalvalue = self.angle
                else:
                    self.temp_modalvalue = self.depth
            self.resetmouse = True
            return {'PASS_THROUGH'}

        # FINISH

        elif event.type in {'LEFTMOUSE', 'SPACE'}:
            bpy.types.SpaceView3D.draw_handler_remove(self.HUD, 'WINDOW')
            return {'FINISHED'}

        # CANCEL

        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            bpy.ops.ed.undo()
            self.cancel_modal()
            return {'CANCELLED'}

        return {'RUNNING_MODAL'}

    def cancel_modal(self, removeHUD=True):
        print("cancel modal")
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

        #Init values
        self.resetmouse = False
        self.offset = 0
        self.temp_modalvalue = 0
        self.temp_depth = 0.0
        self.geometry_mode = 'offset'
        
        #bm = bmesh.from_edit_mesh(context.active_object.data)
        #self._factor = get_factor(context, bm.edges)
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
 
        args = (context, event)
        self.HUD = bpy.types.SpaceView3D.draw_handler_add(self.draw_HUD, (args, ), 'WINDOW', 'POST_PIXEL')

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
    
        if self.depth_mode == 'angle':
            bpy.ops.mesh.offset_edges(True, geometry_mode=self.geometry_mode, width=self.width, angle=self.angle, depth_mode='angle', follow_face=self.follow_face, threshold=self.threshold, mirror_modifier=self.mirror_modifier, edge_rail=self.edge_rail, edge_rail_only_end=self.edge_rail_only_end, caches_valid=False)
        else:
            bpy.ops.mesh.offset_edges(True, geometry_mode=self.geometry_mode, width=self.width, depth=self.depth, depth_mode='depth', follow_face=self.follow_face, threshold=self.threshold, mirror_modifier=self.mirror_modifier, edge_rail=self.edge_rail, edge_rail_only_end=self.edge_rail_only_end, caches_valid=False)
        return True
