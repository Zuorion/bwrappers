import math
from math import sin, cos, pi, copysign, radians, degrees, atan, sqrt
from bpy_extras.view3d_utils import region_2d_to_location_3d
import bpy
import mathutils
from bpy_extras import view3d_utils
import bmesh
from mathutils import Vector
from time import perf_counter
import os
import addon_utils

#Made by Machin3

def get_prefValue(name):
    return getattr(bpy.context.preferences.addons[__name__].preferences,name)

def get_addon_name():
    return os.path.basename(os.path.dirname(os.path.realpath(__file__)))

def get_prefs():
    name = get_addon_name()
    return bpy.context.preferences.addons[name].preferences

def set_prefValue(name,value):
    return setattr(bpy.context.preferences.addons[__name__].preferences,name,value)

def average_locations(locationslist):
    avg = Vector()

    for n in locationslist:
        avg += n

    return avg / len(locationslist)

def addon_exists(name):
    for addon_names in bpy.context.preferences.addons.keys():
        if name in addon_names: return True
    return False

def get_zoom_factor(mxw, coords, multiply=10, debug=False):
    """
    create factor based on distance to given location and region width for zoom independet scaling
    based on work by Hidesato Ikeya from offset edges addon
    upgraded to 2.8x by Machin3
    """

    # get center/average location of coords
    center = mxw @ average_locations(coords)

    region = bpy.context.region
    r3d = bpy.context.space_data.region_3d

    win_left = Vector((0, 0))
    win_right = Vector((region.width, 0))

    # project window borders into world space to the center of the selection
    left = region_2d_to_location_3d(region, r3d, win_left, center)
    right = region_2d_to_location_3d(region, r3d, win_right, center)

    # width = (right - left).length  # region with vector length in world space
    width = ((right - left) @ mxw.inverted()).length  # also compensate for object scaling

    factor = width / region.width

    if debug:
        print("zoom factor:", factor)

    return factor * multiply