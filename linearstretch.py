#
#   linearstretch.py
#
#   Linear stretch along a vector defined by two reference points.
#
#   Animats
#   December, 2018
#   License: GPL
#
#   This stretches a model by moving the top vertex set
#   along the vector from the bottom ref point to the
#   top ref point.
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
def stretchmodel(target, bottomrefname, toprefname, topname, dist) :
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
    toprefv = getrefvertcoords(target, toprefname)
    bottomrefv = getrefvertcoords(target, bottomrefname)
    topgroup = target.vertex_groups[topname]
    topvs = getvertsingroup(target, topgroup)               # verts to move
    refvec = toprefv.co - bottomrefv.co                     # movement direction
    print("topref: %s  bottomref: %s  refvec: %s" % (toprefv.co, bottomrefv.co, refvec))    # ***TEMP***
    if refvec.magnitude < 0.001 :
        raise ValueError("Reference vertices are in the same place.")
    refvecnorm = refvec.normalized()                        # unit vector
    #   All checks passed. OK to perform stretch.
    #   Move verts
    for v in topvs :
        v.co = v.co + refvecnorm * dist
    
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
   
        
#
#   asksize -- pop up dialog for size
#
class AskSizeDialogOperator(bpy.types.Operator):
    bl_idname = "object.ask_size_dialog_operator"
    bl_label = "Resizing by stretching"

    desired_height = bpy.props.FloatProperty(name="Desired height")
    
    def execute(self, context) :
        result = self.run(context)
        if result :                                 # report fail
            self.report(result[0], result[1])
            return {'CANCELLED'}                    # return fail code       
        return {'FINISHED'}


    def run(self, context):
        print("Dialog result: %1.2f" % (self.desired_height,))
        if self.desired_height < 0.1 or self.desired_height > 64.0 :
            return({'ERROR_INVALID_INPUT'}, "Desired height %1.3f out of range." % (self.desired_height))      
        if not context.selected_objects :
            return({'ERROR_INVALID_INPUT'}, "Nothing selected.")
        target = context.selected_objects[-1]       # target object (last selection)
        try :                                       # do the work
            #   Calculate how much to stretch to get desired height between platform ref points
            oldheight = getrefvertcoords(target, PLATTOP).co.z - getrefvertcoords(target, PLATBOTTOM).co.z  # previous height
            zchange = self.desired_height - oldheight        # need to change Z by this much
            oldstretchvec = getrefvertcoords(target, REFTOP).co - getrefvertcoords(target, REFBOTTOM).co    # previous stretch vector
            newstretchvec = oldstretchvec * ((oldstretchvec.z + zchange) / oldstretchvec.z)                 # desired stretch vector
            dist = newstretchvec.magnitude - oldstretchvec.magnitude    # distance to add to stretch vector
            stretchmodel(target, REFBOTTOM, REFTOP, VERTSTOP, dist)
            #   Checking
            finalheight = getrefvertcoords(target, PLATTOP).co.z - getrefvertcoords(target, PLATBOTTOM).co.z    # final height
            if abs(finalheight - self.desired_height) > 0.01 :
                raise ValueError("Model error: height %1.3f after stretching does not match goal of %1.3f" % (finalheight, self.desired_height))
            
        except ValueError as message :
            return ({'ERROR_INVALID_INPUT'}, str(message))
        return None

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)


bpy.utils.register_class(AskSizeDialogOperator)

#   Call this to use.
def linearstretch() :
    bpy.ops.object.ask_size_dialog_operator('INVOKE_DEFAULT')

#   Test only
def test() :
    context = C
    if not context.selected_objects :
        return({'ERROR_INVALID_INPUT'}, "Nothing selected.")
    target = context.selected_objects[-1]       # target impostor (last selection)

    msg = stretchmodel(target, REFBOTTOM, REFTOP, VERTSTOP, 5.0)
    if (msg) :
        print("Error: %s" % (str(msg),))
