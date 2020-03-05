# Blender-SL-utils
Various utilities for using Blender for creating Second Life objects

## Escalator resizing
Instructions for Blender 2.82
### Frame
#### linearstretch.py
Useful for stretching models which can be divided into two sections and
stretched between those sections. Used for an escalator model.

Not a full Blender add-on. Load into Python window. See code for instructions.

To invoke:
    
    import os
    filename=os.path.dirname(bpy.data.filepath)+ "/../Blender-SL-utils/linearstretch.py"
    exec(compile(open(filename).read(), filename, 'exec'))
    
Select both parts of the high and low LOD. Main part of high LOD must be selected last because it has the reference points.
    
    linearstretch()
    
### UVs
The UVs for the railing need to be re-made after stretching so that the railing animation speed will be uniform over the whole railing.

UV->Reset
UV->Follow active quads
Then rescale until diamonds on railing are square

This is not working for both railings. One gets properly rescaled, the other is totally wrong.

### Steps
The steps are an array, and any desired number of steps can be produced by setting the array repetition number

### Scripts
*To be provided*

### TODO
- Set vertex groups for second part of model and for lower LOD model so stretching will work.


