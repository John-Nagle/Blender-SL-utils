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

1. Select longest part of one railing
2. Select by material to get rest of railings
3. Set X-ray mode.
4. Deselect other railing by box (B) deselect (shift)
5. UV->Follow active quads
6. Repeat for other railing


This is not working for both railings. One gets properly rescaled, the other is totally wrong.

### Steps
The steps are an array, and any desired number of steps can be produced by setting the array repetition number

### Scripts
*To be provided*

### TODO
- Set vertex groups for second part of model and for lower LOD model so stretching will work.


