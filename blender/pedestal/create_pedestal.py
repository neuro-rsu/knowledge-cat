from math import pi
from pathlib import Path

import bpy
from mathutils import Vector


PROJECT_DIR = Path(__file__).resolve().parent
BLEND_PATH = PROJECT_DIR / "pedestal.blend"
PREVIEW_PATH = PROJECT_DIR / "preview.png"


def point_at(obj, target=(0.0, 0.0, 0.55)):
    direction = Vector(target) - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def add_bevel(obj, width=0.006, segments=3):
    modifier = obj.modifiers.new(name="Edge Bevel", type="BEVEL")
    modifier.width = width
    modifier.segments = segments


def add_box(name, dimensions, location, material, bevel=0.006):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dimensions
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(material)
    add_bevel(obj, bevel)
    return obj


def make_stone_material():
    material = bpy.data.materials.new(name="Dark Stone")
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    nodes.clear()

    output = nodes.new("ShaderNodeOutputMaterial")
    shader = nodes.new("ShaderNodeBsdfPrincipled")
    tex_coord = nodes.new("ShaderNodeTexCoord")
    noise = nodes.new("ShaderNodeTexNoise")
    ramp = nodes.new("ShaderNodeValToRGB")
    bump = nodes.new("ShaderNodeBump")

    noise.inputs["Scale"].default_value = 7.0
    noise.inputs["Detail"].default_value = 5.0
    noise.inputs["Roughness"].default_value = 0.72
    ramp.color_ramp.elements[0].position = 0.22
    ramp.color_ramp.elements[0].color = (0.006, 0.008, 0.010, 1.0)
    ramp.color_ramp.elements[1].position = 0.80
    ramp.color_ramp.elements[1].color = (0.030, 0.035, 0.042, 1.0)
    bump.inputs["Strength"].default_value = 0.18
    bump.inputs["Distance"].default_value = 0.018
    shader.inputs["Roughness"].default_value = 0.58
    shader.inputs["Metallic"].default_value = 0.04

    links.new(tex_coord.outputs["Generated"], noise.inputs["Vector"])
    links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], shader.inputs["Base Color"])
    links.new(noise.outputs["Fac"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], shader.inputs["Normal"])
    links.new(shader.outputs["BSDF"], output.inputs["Surface"])
    return material


def make_gold_material():
    material = bpy.data.materials.new(name="Warm Brass")
    material.use_nodes = True
    shader = material.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = (0.52, 0.22, 0.035, 1.0)
    shader.inputs["Metallic"].default_value = 0.82
    shader.inputs["Roughness"].default_value = 0.25
    return material


def add_tapered_column(material):
    bottom_z = 0.13
    top_z = 0.88
    bottom_x, bottom_y = 0.29 / 2.0, 0.22 / 2.0
    top_x, top_y = 0.35 / 2.0, 0.26 / 2.0
    vertices = [
        (-bottom_x, -bottom_y, bottom_z),
        (bottom_x, -bottom_y, bottom_z),
        (bottom_x, bottom_y, bottom_z),
        (-bottom_x, bottom_y, bottom_z),
        (-top_x, -top_y, top_z),
        (top_x, -top_y, top_z),
        (top_x, top_y, top_z),
        (-top_x, top_y, top_z),
    ]
    faces = [
        (0, 3, 2, 1),
        (4, 5, 6, 7),
        (0, 1, 5, 4),
        (1, 2, 6, 5),
        (2, 3, 7, 6),
        (3, 0, 4, 7),
    ]
    mesh = bpy.data.meshes.new("Tapered Column Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new("Tapered Column", mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.data.materials.append(material)
    add_bevel(obj, width=0.007, segments=3)
    return obj


def add_rgu_letters(material):
    text_data = bpy.data.curves.new(name="RGU Lettering", type="FONT")
    text_data.body = "\u0420\u0413\u0423"
    text_data.align_x = "CENTER"
    text_data.align_y = "CENTER"
    text_data.size = 0.145
    text_data.extrude = 0.006
    text_data.bevel_depth = 0.0015
    text_data.bevel_resolution = 3

    font_path = Path(r"C:\Windows\Fonts\arialbd.ttf")
    if font_path.exists():
        text_data.font = bpy.data.fonts.load(str(font_path))

    letters = bpy.data.objects.new("RGU Letters", text_data)
    bpy.context.scene.collection.objects.link(letters)
    letters.location = (0.0, -0.126, 0.64)
    letters.rotation_euler = (pi / 2.0, 0.0, 0.0)
    letters.data.materials.append(material)

    bpy.context.view_layer.objects.active = letters
    letters.select_set(True)
    bpy.ops.object.convert(target="MESH")
    letters = bpy.context.object
    letters.name = "RGU Letters"
    return letters


# Clean scene.
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)

scene = bpy.context.scene
scene.name = "RGU Pedestal"
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 900
scene.render.resolution_y = 1100
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.image_settings.color_mode = "RGBA"
scene.render.filepath = str(PREVIEW_PATH)
scene.render.film_transparent = False
scene.unit_settings.system = "METRIC"
scene.unit_settings.length_unit = "METERS"

stone = make_stone_material()
gold = make_gold_material()

pedestal_collection = bpy.data.collections.new("Pedestal")
scene.collection.children.link(pedestal_collection)

base = add_box(
    "Lower Base Slab",
    dimensions=(0.74, 0.52, 0.08),
    location=(0.0, 0.0, 0.04),
    material=stone,
    bevel=0.012,
)
transition = add_box(
    "Lower Transition Slab",
    dimensions=(0.62, 0.43, 0.05),
    location=(0.0, 0.0, 0.105),
    material=stone,
    bevel=0.008,
)
column = add_tapered_column(stone)
capital = add_box(
    "Upper Transition Slab",
    dimensions=(0.44, 0.34, 0.05),
    location=(0.0, 0.0, 0.905),
    material=stone,
    bevel=0.008,
)
top = add_box(
    "Upper Support Slab",
    dimensions=(0.60, 0.45, 0.09),
    location=(0.0, 0.0, 0.975),
    material=stone,
    bevel=0.012,
)
letters = add_rgu_letters(gold)

for obj in (base, transition, column, capital, top, letters):
    for collection in list(obj.users_collection):
        collection.objects.unlink(obj)
    pedestal_collection.objects.link(obj)

# Camera and studio lights are kept outside the pedestal collection.
bpy.ops.object.camera_add(location=(1.62, -2.45, 1.48))
camera = bpy.context.object
camera.name = "Camera"
camera.data.lens = 58
point_at(camera, target=(0.0, 0.0, 0.52))
scene.camera = camera

lights = [
    ("Key Light", (2.8, -3.4, 3.8), 1000.0, 3.0),
    ("Fill Light", (-2.6, -1.8, 2.2), 650.0, 2.5),
    ("Rim Light", (1.5, 2.5, 3.0), 900.0, 2.0),
]

for name, location, energy, size in lights:
    data = bpy.data.lights.new(name=name, type="AREA")
    data.energy = energy
    data.shape = "DISK"
    data.size = size
    light = bpy.data.objects.new(name=name, object_data=data)
    scene.collection.objects.link(light)
    light.location = location
    point_at(light, target=(0.0, 0.0, 0.52))

world = bpy.data.worlds.new("Neutral Studio World")
world.use_nodes = True
background = world.node_tree.nodes.get("Background")
background.inputs["Color"].default_value = (0.12, 0.135, 0.16, 1.0)
background.inputs["Strength"].default_value = 0.45
scene.world = world

# Selection and metadata for a convenient handoff.
bpy.ops.object.select_all(action="DESELECT")
base.select_set(True)
bpy.context.view_layer.objects.active = base
scene["model_scope"] = "Pedestal only"
scene["total_height_m"] = 1.02
scene["reference_directory"] = "../../images"

bpy.ops.render.render(write_still=True)
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_PATH))
