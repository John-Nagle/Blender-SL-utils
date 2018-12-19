#
#   Escalator rescaling assist
#
#   Animats
#   December, 2018
#
#
#
#   This stretches a model by moving the top vertex set
#   along the vector from the bottom ref point to the
#   top ref point.
#
#   This is used to adjust the length of our escalator.
#   The model is designed so that the section stretched
#   has no vertices within it.
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
    print("Verts of index %d, group %s, object %s" % (groupix, groupobj.name, obj.name)) # ***TEMP***
    verts = []                                  # array of verts
    for v in obj.data.vertices :                # search for vert in group
        for g in v.groups :
            if g.group == groupix :             # Yes, O(N*M), but M is tiny
                verts.append(v)
    return verts
    
#
#   stretchmodel -- stretch selected model appropriately
#
def stretchmodel(bottomrefname, toprefname, topname, dist) :
    print("Stretchmodel")
    #   Sanity checks before starting
    context = C
    if not context.selected_objects :
        return({'ERROR_INVALID_INPUT'}, "Nothing selected.")
    target = context.selected_objects[-1]       # target impostor (last selection)
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
    print("Top ref group: %d verts. Bottom ref group: %d verts. Verts to move: %d." % (len(toprefvs), len(bottomrefvs), len(topvs))) # ***TEMP***
    if len(toprefvs) != 1 : 
        return({'ERROR_INVALID_INPUT'}, "Reference vertex group \"%s\" had %d vertices, not one." % (toprefgroup.name,len(toprefvs)))
    if len(bottomrefvs) != 1 : 
        return({'ERROR_INVALID_INPUT'}, "Reference vertex group \"%s\" had %d vertices, not one." % (bottomrefgroup.name,len(bottomrefvs)))
    toprefv = toprefvs[0]
    bottomrefv = bottomrefvs[0]
    refvec = [toprefv.co[0] - bottomrefv.co[0], toprefv.co[1] - bottomrefv.co[1], toprefv.co[2] - bottomrefv.co[2]] # movement vec
    print("topref: %s  bottomref: %s  refvec: %s" % (toprefv.co, bottomrefv.co, refvec))
    refvecl = math.sqrt(refvec[0]*refvec[0] + refvec[1]*refvec[1] + refvec[2]*refvec[2])
    if refvecl < 0.001 :
        return({'ERROR_INVALID_INPUT'}, "Reference vertices are in the same place.")
    refvecnorm = [refvec[0]/refvecl, refvec[1]/refvecl, refvec[2]/refvecl]              # normalize
    ####return # ***TEMP***
    #   Move verts
    for v in topvs :
        v.co.x = v.co.x + refvecnorm[0] * dist
        v.co.y = v.co.y + refvecnorm[1] * dist
        v.co.z = v.co.z + refvecnorm[2] * dist
        
    

        
    return None                                 # success


def test() :
    msg = stretchmodel(REFBOTTOM, REFTOP, VERTSTOP, 500.0)
    if (msg) :
        print("Error: %s" % (str(msg),))
