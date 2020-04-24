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
import bmesh
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

#   Railing info. Name of vertex group, normal to plane for selecting points, point on plane for selecting points
RAILINGS = [("Railing L",Vector([1,0,0]),Vector([0,0,0])), 
           ("Railing R",Vector([-1,0,0]),Vector([0,0,0]))]            # long face of each railing, for UV equalization
           
           
#
#   findrailingfaces -- get points for railng of interest
#
def findrailingfaces(obj, material, plane, planeloc) :
    '''
    Select faces which are in front of plane and of desired material
    '''
    return [face for face in obj.data.faces if (face.co-planeloc).dot(plane) >= 0 and face.data.material == material] # vertices in front of plane  

#
#   findpolyfromvertices
#
def findpolyfromvertices(obj,verts) :
    '''
    Takes list of vertex indicies, returns single matching face or None
    '''
    vertsset = set([v.index for v in verts])        # indices of polygon, for comparison
    print("Vertex set for face: %s" % (vertsset,))  # ***TEMP***
    for item in obj.data.polygons.items() :         # for all polygons
        (i, polygon) = item
        polyset = set(polygon.vertices)
        ####print("Vertex set for poly: %s" % (polyset,))  # ***TEMP***
        if vertsset == set(polygon.vertices) :      # if all match
            ####print("Face info: %s" % (dir(polygon))) # ***TEMP***
            return polygon                          # found
    return None                                     # no find

#
#   positivesideofplane  
#
def positivesideofplane(obj, poly, plane, planeloc) :
    '''
    True if poly is entirely on the positive side of the plane
    '''
    for vertix in poly.vertices :
        keep = (obj.data.vertices[vertix].co-planeloc).dot(plane) > 0
        ####print("Vertex %d: (%s)  %s" % (vertix, keep, obj.data.vertices[vertix].co)) # ***TEMP***
        if (not keep) :
            return(False)
        ####print("Vertex %d: (%s)  %s" % (vertix, keep, obj.data.vertices[vertix].co)) # ***TEMP***
 
    ####print("Vertex %d: %s" % (vertix, obj.data.vertices[vertix].co)) # ***TEMP***
    return(True)                                    # entirely on good side of the plane
            
#
#   findrailingfaces -- find all faces with indicated material
#
def findrailingfaces(obj, materialix, plane, planeloc) :
    '''
    Find all faces with indicated material and on + side of plane
    '''
    return [face for face in obj.data.polygons 
        if face.material_index == materialix
        and positivesideofplane(obj, face, plane, planeloc)] 
#
#   equalizerailinguvs -- equalize UVs along length of railings
#
def equalizerailinguvs(obj) :
    '''
    Equalize UVs along length of railings.
    
    After we stretch, we need to equalize UVs so the railing animation looks right
    '''
    for (refname, plane, planeloc) in RAILINGS :            # for each railing vertex group
        if not refname in obj.vertex_groups :               # can't find this vertex group
            raise ValueError("Cannot find railing vertex group \"%s\"." % (refname,))
        vertgroup = obj.vertex_groups[refname]              # got vertex group
        keyverts = getvertsingroup(obj, vertgroup)          # get verts of face
        print("Railing %s: %d verts." % (refname, len(keyverts)))   # found relevant groups
        keyface = findpolyfromvertices(obj,keyverts)         # look for verts
        if keyface is None :                                 # no find
            raise ValueError("Unable to find face that matches vertex group \"%s\"." % (refname,))
        materialix = keyface.material_index                 # get material index of key polygon
        material = obj.data.materials[materialix]           # the material
        print("Key face material is %s" % (material.name,)) # ****TEMP***
        faces = findrailingfaces(obj, materialix, plane, planeloc)
        print("Found %d faces to equalize." % (len(faces),))
        followquadsequalize(obj, keyface, faces)            # do the follow quads operation

#
#   keyfacelengths -- get length of key face
#
#   The change in this during resizing controls scaling
#
def keyfacelengths(obj, keyface, teximageaspect) :
    '''
    Get lengths of key face. This is a rectangular quad, or should be
    
    Must be in OBJECT mode.
    '''
    #   Lengths in 3D space
    uvcoords = []                                               # UV coords in 2D space
    vertcoords = []                                             # vertex coords in 3D space
    for loopix in keyface.loop_indices :                        # for all edge loops
        loop = obj.data.loops[loopix]                           # loop of interest
        edge = obj.data.edges[loop.edge_index]                  # key vertex
        uvcoords.append(obj.data.uv_layers.active.data[loopix].uv)   # UV coords of vertex for this edge
        vertcoords.append(obj.data.vertices[loop.vertex_index].co)    # 3D coords of vertex for this edge
        print("Vert: %s  Edge: %s  %s" % (obj.data.vertices[loop.vertex_index].co,obj.data.vertices[edge.vertices[0]].co , obj.data.vertices[edge.vertices[1]].co))
    print("Vertex coords: %s" % (vertcoords,))
    #   Lengths in 3D space, wrapping around
    longside = 0.0
    shortside = float('inf')
    for i in range(len(vertcoords)) :
        length = (vertcoords[i] - vertcoords[(i+1) % len(vertcoords)]).length
        longside = max(length, longside)                        # keep longest length
        shortside = min(length, shortside)                      # keep shortest length

    #   Lengths in UV space, wrapping around
    longuvside = 0.0
    shortuvside = float('inf')
    for i in range(len(uvcoords)) :
        length = (uvcoords[i] - uvcoords[(i+1) % len(uvcoords)]).length
        longuvside = max(length, longuvside)                    # keep longest length
        shortuvside = min(length, shortuvside)                  # keep shortest length

    ####for vert_idx, loop_idx in zip(keyface.vertices, keyface.loop_indices):
    ####    uv_coords = obj.data.uv_layers.active.data[loop_idx].uv
    ####    print("face idx: %i, vert idx: %i, uvs: %f, %f" % (keyface.index, vert_idx, uv_coords.x, uv_coords.y))
        
    vertratio = longside / shortside
    uvratio = longuvside / shortuvside
    uvrescale = (vertratio / uvratio) / teximageaspect          # calculate X rescale factor to make model match image
    print("Face ratios: verts %1.4f UVs %1.4f  UV rescale needed: %1.4f" % (vertratio, uvratio, uvrescale,))
    return uvrescale                                            # apply this rescale factor to X axis of UVs
            
#
#   followquadsequalize
#
def followquadsequalize(obj, keyface, faces) :
    '''
    Do a "follow active quads".
    
    Select listed faces.
    Set keyface as active.
    Do follow active quads
    
    We have to do this as a user-visible operator, because
    "follow active quads" is not directly callable on arbitrary geometry
    '''
    prevmode = bpy.context.mode                                 # for later restoration
    try :
        #   Find image being used for texture, to get its aspect ratio
        teximageaspect = 1.0                                    # texture image aspect ratio
        materialix = keyface.material_index                     # get material index of key polygon
        material = obj.data.materials[materialix]               # the material. Must have material to get here
        print("Key face material is %s" % (material.name,))     # ****TEMP***
        #   Get aspect ratio from first texture image for this material
        if material and material.use_nodes :                    # if we have a material
            for node in material.node_tree.nodes:               # look through node tree for image
                if node.type == 'TEX_IMAGE' :
                    if node.image.size[0] > 0 or node.image.size[1] > 0 :
                        print(' uses', node.image.name, 'x',node.image.size[0], 'y',node.image.size[1])
                        teximageaspect = node.image.size[0] / node.image.size[1]    # image aspect ratio X/Y
        #   Get all faces to be equalized selected. Key face to follow is the active face
        bpy.ops.object.mode_set(mode='OBJECT', toggle=False)    # strangely, we have to select faces in object mode
        #   Deselect all mesh elements of the object
        for vertex in obj.data.vertices :
            vertex.select = False
        for edge in obj.data.edges :
            edge.select = False
        for face in obj.data.polygons.values() :
            face.select = False                                 # deselect 
        #   Select faces of interest and key face
        for face in faces :                                     # for all faces
            face.select = True                                  # select face
            for loopix in face.loop_indices :                   # for all edge loops
                loop = obj.data.loops[loopix]                   # loop of interest
                obj.data.vertices[loop.vertex_index].select = True   # select vertex
                obj.data.edges[loop.edge_index].select = True        # select edges
       
        #   Make the key face the active face. 
        #   Per https://blender.stackexchange.com/questions/81395/python-set-active-face-batch-unwrap-follow-active-quads
        bpy.ops.object.mode_set(mode='EDIT', toggle=False)      # must be in edit mode for bmesh work
        bm = bmesh.from_edit_mesh(obj.data)                     # get a working bmesh
        bm.faces.ensure_lookup_table()                          # make faces indexable
        bm.faces.active = bm.faces[keyface.index]               # set key face as active face
        bmesh.update_edit_mesh(obj.data, True)                  # push bmesh back to main mesh (How does it know to use bm?)

        #   Equalize the UVs
        bpy.ops.uv.follow_active_quads(mode='LENGTH')           # equalize UVs
        #   Done
        bpy.ops.object.mode_set(mode='OBJECT', toggle=False)    # back to object mode
        #   Scale UVs to fit
        keylengths = keyfacelengths(obj,keyface, teximageaspect)# get lengths of key face
        print("Key face lengths: %s" % (keylengths,))           # ***TEMP***

        bm.free()                                               # done with bmesh
        print("Key face #%d" % (keyface.index,))                # ***TEMP***
    finally:
        pass #### bpy.ops.object.mode_set(mode=prevmode, toggle=False)    # return to previous mode

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
        ####target = context.selected_objects[-1]       # target object (last selection)
        targets = context.selected_objects          # all selected; last must contain the ref points
        reftarget = context.active_object           # contains the ref points
        ####reftarget = targets[-1]                     # contains the ref points
        try :                                       # do the work
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
            #   Finally equalize the UVs of the railing
            equalizerailinguvs(reftarget)
            
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
