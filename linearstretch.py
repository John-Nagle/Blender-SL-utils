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
import bpy
import math
#
VERTSBOTTOM = "Bottom"
VERTSTOP = "Top"
REFBOTTOM = "Bottom ref"
REFTOP = "Top ref"

#
#   getvertsingroup --  get vertices in given group
#
def getvertsingroup(obj, groupobj) :
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
    #   Sanity checks before starting
    if target.type != 'MESH' :
        return({'ERROR_INVALID_INPUT'}, "Selected object \"%s\" must be a mesh." % (target.name,))
    if target.scale[0] < 0 or target.scale[1] < 0 or target.scale[2] < 0 :
        return({'ERROR_INVALID_INPUT'}, "Selected object \"%s\" has a negative scale:  (%1.2f, %1.2f, %1.2f)." % 
                (target.name, target.scale[0], target.scale[1], target.scale[2]))
                
    #   Find relevant vertex groups
    bottomrefgroup = target.vertex_groups[bottomrefname]
    toprefgroup = target.vertex_groups[toprefname]
    topgroup = target.vertex_groups[topname]
    bottomrefvs = getvertsingroup(target, bottomrefgroup)   # verts in top ref group
    toprefvs = getvertsingroup(target, toprefgroup)         # verts in bottom ref group
    topvs = getvertsingroup(target, topgroup)               # verts to move
    ####print("Top ref group: %d verts. Bottom ref group: %d verts. Verts to move: %d." % (len(toprefvs), len(bottomrefvs), len(topvs))) # ***TEMP***
    if len(toprefvs) != 1 : 
        return({'ERROR_INVALID_INPUT'}, "Reference vertex group \"%s\" had %d vertices, not one." % (toprefgroup.name,len(toprefvs)))
    if len(bottomrefvs) != 1 : 
        return({'ERROR_INVALID_INPUT'}, "Reference vertex group \"%s\" had %d vertices, not one." % (bottomrefgroup.name,len(bottomrefvs)))
    refvec = toprefvs[0].co - bottomrefvs[0].co             # movement direction 
    print("topref: %s  bottomref: %s  refvec: %s" % (toprefvs[0].co, bottomrefvs[0].co, refvec))    # ***TEMP***
    if refvec.magnitude < 0.001 :
        return({'ERROR_INVALID_INPUT'}, "Reference vertices are in the same place.")
    refvecnorm = refvec.normalized()                        # unit vector
    #   All checks passed. OK to perform stretch.
    #   Move verts
    for v in topvs :
        v.co = v.co + refvecnorm * dist
    return None                                             # success
    
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
        result = stretchmodel(target, REFBOTTOM, REFTOP, VERTSTOP, self.desired_height)
        return result

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
