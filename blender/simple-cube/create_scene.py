from pathlib import Path

import bpy
from mathutils import Vector


PROJECT_DIR = Path(__file__).resolve().parent
BLEND_PATH = PROJECT_DIR / "simple-cube.blend"
PREVIEW_PATH = PROJECT_DIR / "preview.png"


def point_at(obj, target=(0.0, 0.0, 0.0)):
    direction = Vector(target) - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


# Start from a clean scene.
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)

scene = bpy.context.scene
scene.name = "Simple Cube Scene"
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 800
scene.render.resolution_y = 800
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.filepath = str(PREVIEW_PATH)
scene.render.film_transparent = False
scene.render.image_settings.color_mode = "RGBA"
scene.render.resolution_percentage = 100
scene.unit_settings.system = "METRIC"

# Cube: the only geometry in the project.
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(0.0, 0.0, 0.0))
cube = bpy.context.object
cube.name = "Simple Cube"
cube.data.name = "Simple Cube Mesh"

material = bpy.data.materials.new(name="Blue Material")
material.diffuse_color = (0.035, 0.24, 0.80, 1.0)
material.use_nodes = True
shader = material.node_tree.nodes.get("Principled BSDF")
shader.inputs["Base Color"].default_value = (0.035, 0.24, 0.80, 1.0)
shader.inputs["Roughness"].default_value = 0.28
shader.inputs["Metallic"].default_value = 0.05
cube.data.materials.append(material)

bevel = cube.modifiers.new(name="Small Edge Bevel", type="BEVEL")
bevel.width = 0.08
bevel.segments = 4

# Camera.
bpy.ops.object.camera_add(location=(4.2, -4.2, 3.2))
camera = bpy.context.object
camera.name = "Camera"
camera.data.lens = 55
point_at(camera)
scene.camera = camera

# Three-point studio lighting.
lights = [
    ("Key Light", (3.5, -4.0, 5.0), 900.0, 4.0),
    ("Fill Light", (-4.0, -1.5, 2.5), 500.0, 3.5),
    ("Rim Light", (2.5, 4.0, 4.5), 750.0, 3.0),
]

for name, location, energy, size in lights:
    data = bpy.data.lights.new(name=name, type="AREA")
    data.energy = energy
    data.shape = "DISK"
    data.size = size
    light = bpy.data.objects.new(name=name, object_data=data)
    scene.collection.objects.link(light)
    light.location = location
    point_at(light)

world = bpy.data.worlds.new("Dark Studio World")
world.use_nodes = True
background = world.node_tree.nodes.get("Background")
background.inputs["Color"].default_value = (0.012, 0.018, 0.040, 1.0)
background.inputs["Strength"].default_value = 0.30
scene.world = world

# Keep the cube selected when the file is opened.
bpy.context.view_layer.objects.active = cube
cube.select_set(True)
camera.select_set(False)
for obj in scene.objects:
    if obj.type == "LIGHT":
        obj.select_set(False)

bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_PATH))
bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_PATH))
