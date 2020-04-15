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
    delta = []
    for i in range(3) :
        delta.append(max([pnt[i] for pnt in bblist])-min([pnt[i] for pnt in bblist]))
    return Vector(delta)
        
    
def resizetomatchboundboxes(hilodobj,lolodobj) :
    '''
    Adjust second object to match bounding box of first
    '''
    boundshi = hilodobj.bound_box                       # get bounding box
    for bnd in boundshi :
        print("Corner: <%f %f %f>" % (bnd[0],bnd[1],bnd[2]))                    # ***TEMP***
    print("Range: " + str(bbrange(boundshi)))                                   # ***TEMP***
    boundslo = lolodobj.bound_box
    pass         
    
   
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
            #   Calculate how much to stretch to get desired height between platform ref points
            print("Ref target is %s." % reftarget.name)
            oldheight = getrefvertcoords(reftarget, PLATTOP).co.z - getrefvertcoords(reftarget, PLATBOTTOM).co.z  # previous height
            zchange = self.desired_height - oldheight        # need to change Z by this much
            oldstretchvec = getrefvertcoords(reftarget, REFTOP).co - getrefvertcoords(reftarget, REFBOTTOM).co    # previous stretch vector
            newstretchvec = oldstretchvec * ((oldstretchvec.z + zchange) / oldstretchvec.z)                 # desired stretch vector
            dist = newstretchvec.magnitude - oldstretchvec.magnitude    # distance to add to stretch vector
            toprefv = getrefvertcoords(reftarget, REFTOP)
            bottomrefv = getrefvertcoords(reftarget, REFBOTTOM)
            refvec = toprefv.co - bottomrefv.co                         # movement direction
            if refvec.magnitude < 0.001 :
                raise ValueError("Reference vertices are in the same place.")
            for target in targets: 
                stretchmodel(target, VERTSTOP, dist*refvec.normalized())
            #   Checking
            finalheight = getrefvertcoords(reftarget, PLATTOP).co.z - getrefvertcoords(reftarget, PLATBOTTOM).co.z    # final height
            if abs(finalheight - self.desired_height) > 0.01 :
                raise ValueError("Model error: height %1.3f after stretching does not match goal of %1.3f" % (finalheight, self.desired_height))
            
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

#   Test only
def test() :
    context = C
    if not context.selected_objects :
        return({'ERROR_INVALID_INPUT'}, "Nothing selected.")
    target = context.selected_objects[-1]       # target impostor (last selection)

    msg = stretchmodel(target, REFBOTTOM, REFTOP, VERTSTOP, 5.0)
    if (msg) :
        print("Error: %s" % (str(msg),))
