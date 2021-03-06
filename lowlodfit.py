#
#   lowlodfit.py
#
#   Fit low-LOD model outline to high LOD
#
#   Animats
#   December, 2018
#   License: GPL
#
#   This stretches a low-LOD model (the selected object)
#   to match the bounds of a high-LOD model.
#
#   Used to adjust the low-LOD model of the escalator steps.
#   The high-LOD model is an array, where then number of
#   steps is adjustable. The low-LOD model is an outline.
#   
#   Stretching must be in the middle, and the high end
#   should not move.
#
#   Used to adjust the length of our escalator.
#   The model is designed so that the section stretched
#   has no vertices within it.
#
#   Not an addon. Typically run by
# 
#   filename = "linearstretch.py"
#   exec(compile(open(filename).read(), filename, 'exec'))
#
#   TODO:
#       Make sure in object mode.
#       Make sure scale is 1, or fix to be scale-independent.
#
import bpy
import math
#
#   Names of vertex groups in model.
#   Model must use these.
#   All "Ref" single vertex ref points must have vertex weight 0.
#
VERTSBOTTOM = "Bottom"
VERTSTOP = "Top"
REFBOTTOM = "Bottom ref"
REFTOP = "Top ref"
PLATTOP = "Top platform"
PLATBOTTOM = "Bottom platform"

#
#   getvertsingroup --  get vertices in given group
#
def getvertsingroup(obj, groupobj) :
    """
    Get vertices by vertex group
    """
    groupix = groupobj.index                    # group index
    ####print("Verts of index %d, group %s, object %s" % (groupix, groupobj.name, obj.name)) # ***TEMP***
    verts = []                                  # array of verts
    for v in obj.data.vertices :                # search for vert in group
        for g in v.groups :
            if g.group == groupix :             # Yes, O(N*M), but M is tiny
                verts.append(v)
    return verts
    
#
#   stretchmodel -- stretch selected model appropriately
#
def stretchmodel(target, topname, stretchvec) :
    """
    Stretch selected model along vector from bottom ref to top ref.
    
    dist is the desired distance between bottom ref and top ref
    """
    #   Sanity checks before starting
    if target.type != 'MESH' :
        raise ValueError("Selected object \"%s\" must be a mesh." % (target.name,))
    if target.scale[0] < 0 or target.scale[1] < 0 or target.scale[2] < 0 :
        raise ValueError("Selected object \"%s\" has a negative scale:  (%1.2f, %1.2f, %1.2f)." % 
                (target.name, target.scale[0], target.scale[1], target.scale[2]))
                
    #   Find relevant vertex groups
    ####toprefv = getrefvertcoords(reftarget, toprefname)
    ####bottomrefv = getrefvertcoords(reftarget, bottomrefname)
    topgroup = target.vertex_groups[topname]
    topvs = getvertsingroup(target, topgroup)               # verts to move
    ####refvec = toprefv.co - bottomrefv.co                     # movement direction
    ####print("object: %s  topref: %s  bottomref: %s  refvec: %s" % (target.name, toprefv.co, bottomrefv.co, refvec))    # ***TEMP***
    ####if refvec.magnitude < 0.001 :
    ####    raise ValueError("Reference vertices are in the same place.")
    ####refvecnorm = refvec.normalized()                        # unit vector
    #   All checks passed. OK to perform stretch.
    print("Stretching %s by %s" % (target.name, stretchvec))
    #   Move verts
    for v in topvs :
        v.co = v.co + stretchvec
    
def getrefvertcoords(obj, refname) :
    """
    Get coordinates of a single vertex group
    """
    if not refname in obj.vertex_groups :
        raise ValueError("Cannot find vertex group \"%s\"." % (refname,))
    refgroup = obj.vertex_groups[refname]
    refverts = getvertsingroup(obj, refgroup)
    if len(refverts) != 1 : 
        raise ValueError("Reference vertex group \"%s\" had %d vertices, not one." % (refname,len(refverts)))
    return refverts[0]                              # return the only vert
    
def adjustboundboxes(target) :
    '''
    Adjust second object to match bounding box of first
    '''
    matches = findlowlodmatch(target)
    if len(matches) != 1 :
        raise ValueError("No unique matching lower LOD mesh for: " + target.name)
    lowlodobj = matches[0]                              # will adjust this object
    resizetomatchboundboxes(target, lowlodobj)
    return 
    
def bbrange(bblist) :
    '''
    Take in list of bounding box points, return Vector(dx,dy,dz) indicating range
    '''
    return Vector(
        [max([pnt[i] for pnt in bblist])-min([pnt[i] for pnt in bblist]) for i in range(3)]) 
        
def bbcenter(bblist) :
    '''
    Take in list of bounding box points, return Vector(dx,dy,dz) indicating center
    '''
    return Vector(
        [max([pnt[i] for pnt in bblist])+min([pnt[i] for pnt in bblist]) for i in range(3)])*0.5     
    
def resizetomatchboundboxes(hilodobj,lolodobj) :
    '''
    Adjust second object to match bounding box of first
    '''
    boundshi = hilodobj.bound_box                       # get bounding box
    for bnd in boundshi :
        print("Corner: <%f %f %f>" % (bnd[0],bnd[1],bnd[2]))                    # ***TEMP***
    hirange = bbrange(hilodobj.bound_box)
    lorange = bbrange(lolodobj.bound_box)
    stretch = hirange-lorange                           # how much we have to stretch
    print("Hi Range: " + str(hirange))                                # ***TEMP***
    print("Lo Range: " + str(lorange))                                    # ***TEMP***
    print("Stretch: " + str(stretch))
    #  Find which vertices need stretching
    planeloc = Vector([0,0,0])                          # relative to object center
    planeloc = bbcenter(lolodobj.bound_box)             # center of object being modified
    plane = Vector([0,1,-1])                            # direction to look for points to stretch ***TEMP***
    stretch = Vector([plane[i]*stretch[i] for i in range(3)])   # elementwise mult ***TEMP**
    verts = findvertstostretch(lolodobj, plane, planeloc)
    print("Verts: " + str([v.co for v in verts]))
    #   All checks passed. OK to perform stretch.
    print("Stretching %s by %s" % (lolodobj.name, stretch))
    #   Move verts
    for v in verts :
        v.co = v.co + stretch 
    
def findvertstostretch(obj, plane, planeloc) :
    '''
    Return all vertices of object obj on the + sign of
    the plane defined by direction vector plane and 
    point planeloc
    '''
    plane.normalize()                                   # unit vector
    print("Plane: " + str(plane) + " Center: " + str(planeloc))                       # ***TEMP***
    return [vert for vert in obj.data.vertices if (vert.co-planeloc).dot(plane) >= 0] # vertices in front of plane    
   
def findlowlodmatch(obj) :
    print("Selected object: %s" % (obj.name))
    matches = []
    for lowlodobj in bpy.data.objects :
        print("Scene object: %s (%s)" % (lowlodobj.name, lowlodobj.type))    # ***TEMP***
        if lowlodobj == obj :                       # skip self object
            continue
        if not lowlodobj.name.startswith(obj.name) : # skip no name match
            continue   
        if not lowlodobj.type == 'MESH':            # only mesh objects
            continue
        matches.append(lowlodobj)    
    return matches

   
        
#
#   ResizeLODDialogOperator -- pop up dialog for size
#
class ResizeLODDialogOperator(bpy.types.Operator):
    bl_idname = "object.resize_lod_dialog_operator"
    bl_label = "Resizing to match high LOD model"

    ####desired_height = bpy.props.FloatProperty(name="Desired height")
    
    def execute(self, context) :
        result = self.run(context)
        if result :                                 # report fail
            self.report(result[0], result[1])
            return {'CANCELLED'}                    # return fail code       
        return {'FINISHED'}


    def run(self, context):
        if not context.selected_objects :
            return({'ERROR_INVALID_INPUT'}, "Nothing selected.")
        reftarget = context.active_object           # contains the ref points
        if not reftarget :
            return({'ERROR_INVALID_INPUT'}, "No active object.")
        try :                                       # do the work
            adjustboundboxes(reftarget)             # find other object and calc bound boxes
            return None
            
        except ValueError as message :
            return ({'ERROR_INVALID_INPUT'}, str(message))
        return None

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)


bpy.utils.register_class(ResizeLODDialogOperator)

#   Call this to use.
def lowlodfit() :
    bpy.ops.object.resize_lod_dialog_operator('INVOKE_DEFAULT')

