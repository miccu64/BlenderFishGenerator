from bpy import context, ops, data
from mathutils import Vector
import random
import numpy as np
import bmesh

# dane potrzebne do miejsca generowania innych elementów
corpus_length = 10.
corpus_height = 5.
corpus_width = 5.


# reguła 30, reguła 54 - do generowania łusek
def rule54_find(x: int, y: int, z: int) -> int:
    if x == y == z == 1:
        return 0
    if x == y == 1 and z == 0:
        return 0
    if x == z == 1 and y == 0:
        return 1
    if x == 1 and y == z == 0:
        return 1
    if x == 0 and y == z == 1:
        return 0
    if x == z == 0 and y == 1:
        return 1
    if x == y == 0 and z == 1:
        return 1
    return 0


def rule54_gen():
    ops.object.mode_set(mode='EDIT')
    dims = 144
    values = np.zeros([dims, dims])
    for x in range(dims):
        values[x][0] = random.randint(0, 1)

    for y in range(1, dims):
        for x in range(1, dims - 1):
            values[x][y] = rule54_find(values[x - 1][y - 1], values[x][y - 1], values[x + 1][y - 1])
        values[0][y] = rule54_find(0, values[0][y - 1], values[1][y - 1])
        values[dims - 1][y] = rule54_find(values[dims - 2][y - 1], values[dims - 1][y - 1], 0)
    
    # trzeba transponować, żeby obrócić zdj o 90 stopni
    values = np.transpose(values)
    pixels = [None] * dims * dims
    
    color1 = [random.random(), random.random(), random.random(), 1]
    color2 = [1-color1[0], 1-color1[1], 1-color1[2], 1]
    
    for y in range(dims):
        for x in range(dims):
            if values[x][y] == 1:
                pixels[(x * dims) + y] = color1
            else:
                pixels[(x * dims) + y] = color2
                
    # spłaszczam listę
    pixels = [item for sublist in pixels for item in sublist]
    
    image = data.images.new("ShellsImage", width=dims, height=dims)
    image.pixels = pixels
    #image.filepath_raw = "D:/Studia/PWK/temp.png"
    #image.file_format = 'PNG'
    #image.save()
        
    return image


def solidify(mesh_name: str, width: float):
    ops.object.mode_set(mode='OBJECT')

    # konwersja w siatke
    ops.object.convert(target='MESH', keep_original=True)
    mesh = context.active_object
    mesh.name = mesh_name

    ops.object.mode_set(mode='EDIT')

    # wybranie wszystkich wierzcholkow
    ops.mesh.select_all(action='SELECT')

    # wypelnienie
    ops.mesh.edge_face_add()

    # dodanie trojkatow
    ops.mesh.quads_convert_to_tris(ngon_method='BEAUTY')

    ops.mesh.select_all(action='SELECT')

    # konwersja trojkatow do czworokatow
    ops.mesh.tris_convert_to_quads(
        face_threshold=1.396264, shape_threshold=1.396264)

    # wstawienie scian
    # iter_range = range(0, 1, 1)
    # for i in iter_range:
    ops.mesh.inset(thickness=0.25, use_relative_offset=True)

    ops.object.mode_set(mode='OBJECT')

    solidify = mesh.modifiers.new(type='SOLIDIFY', name='Solidify')
    solidify.offset = 0.0
    solidify.thickness = width

    subsurf = mesh.modifiers.new(type='SUBSURF', name='Subsurf')
    subsurf.levels = subsurf.render_levels = 3
    
    #kolorowanie
    ob = context.active_object
    mat = data.materials.new(name="Colour")
    mat.diffuse_color = [random.random(), random.random(), random.random(), 1]
    ob.data.materials.append(mat)
    

# losowanie typów krawędzi bezier pointsów
def draw_point_type() -> str:
    return random.choice(['FREE', 'VECTOR', 'ALIGNED', 'AUTO'])


def generate_corpus(length: float, height: float, width: float):
    # utworzenie krzywej
    ops.curve.primitive_bezier_circle_add(enter_editmode=True)
    # ops.curve. subdivide()
    curve = context.active_object
    curve.name = 'Corpus Curve'
    bez_points = curve.data.splines[0].bezier_points

    for bez_point in bez_points:
        bez_point.handle_left_type = draw_point_type()
        bez_point.handle_right_type = draw_point_type()

    proportions = random.uniform(1.3, 8.9)

    # lewy
    bez_points[0].co = Vector((-length, 0.0, 0.0))
    bez_points[0].handle_left = Vector((-length, -1.0, 0.0))
    bez_points[0].handle_right = Vector((-length, 1.0, 0.0))

    # gora
    bez_points[1].co = Vector((-length / proportions, height / 2, 0.0))
    bez_points[1].handle_left = Vector((-length / proportions - 1, height / 2, 0.0))
    bez_points[1].handle_right = Vector((-length / proportions + 1, height / 2, 0.0))

    # poczatek ogona
    bez_points[2].co = Vector((0.0, 0.0, 0.0))
    bez_points[2].handle_left = Vector((0.0, 1.0, 0.0))
    bez_points[2].handle_right = Vector((0.0, -1.0, 0.0))

    # dolny
    bez_points[3].co = Vector((-length / proportions, -height / 2, 0.0))
    bez_points[3].handle_left = Vector((-length / proportions + 1, -height / 2, 0.0))
    bez_points[3].handle_right = Vector((-length / proportions - 1, -height / 2, 0.0))

    solidify('Corpus Mesh', width)
    obj = context.active_object

    # dostęp do nadpisania zmiennych globalnych
    global corpus_length, corpus_height, corpus_width
    corpus_length = length
    corpus_height = height / 2
    corpus_width = width / 2


def generate_tail(length: float, height: float, width: float, indentation: float):
    # utworzenie krzywej
    ops.curve.primitive_bezier_circle_add(enter_editmode=True)
    curve = context.active_object
    curve.name = 'Tail Curve'
    bez_points = curve.data.splines[0].bezier_points

    for bez_point in bez_points:
        bez_point.handle_left_type = draw_point_type()
        bez_point.handle_right_type = draw_point_type()

    # lewy
    bez_points[0].co = Vector((-1, 0.0, 0.0))
    bez_points[0].handle_left = Vector((-1, -1.0, 0.0))
    bez_points[0].handle_right = Vector((-1, 1.0, 0.0))

    # gora
    twist = random.uniform(-length / 3, length / 3)
    bez_points[1].co = Vector((length, height / 2, twist))
    bez_points[1].handle_left = Vector((length, height / 2 + 1, twist))
    bez_points[1].handle_right = Vector((length, height / 2 - 1, twist))

    # srodek
    twist = random.uniform(-length / 3, length / 3)
    bez_points[2].co = Vector((length - indentation, 0.0, twist))
    bez_points[2].handle_left = Vector((length - indentation, 0.1, twist))
    bez_points[2].handle_right = Vector((length - indentation, -0.1, twist))

    # dolny
    twist = random.uniform(-length / 3, length / 3)
    bez_points[3].co = Vector((length, -height / 2, twist))
    bez_points[3].handle_left = Vector((length, -height / 2 + 1, twist))
    bez_points[3].handle_right = Vector((length, -height / 2 - 1, twist))

    solidify('Tail Mesh', width)


def generate_upper_fin(length: float, height: float, width: float):
    if width > corpus_width:
        width = corpus_width - 2

    # utworzenie krzywej
    ops.curve.primitive_bezier_circle_add(enter_editmode=True)
    curve = context.active_object
    curve.name = 'Upper Fin Curve'
    bez_points = curve.data.splines[0].bezier_points

    for bez_point in bez_points:
        bez_point.handle_left_type = draw_point_type()
        bez_point.handle_right_type = draw_point_type()

    most_left_point_x = random.uniform(-2 * corpus_length / 3, -corpus_length / 4)

    # lewy dolny
    bez_points[0].co = Vector((most_left_point_x, corpus_height / 2, 0.0))
    bez_points[0].handle_left = Vector((most_left_point_x - 1, corpus_height / 2, 0.0))
    bez_points[0].handle_right = Vector((most_left_point_x + 1, corpus_height / 2, 0.0))

    # prawy dolny
    bez_points[1].co = Vector((most_left_point_x + length, corpus_height / 2, 0.0))
    bez_points[1].handle_left = Vector((most_left_point_x + length, corpus_height / 2 - 1, 0.0))
    bez_points[1].handle_right = Vector((most_left_point_x + length, corpus_height / 2 + 1, 0.0))

    # prawy górny
    twist = random.uniform(-length / 3, length / 3)
    bez_points[2].co = Vector((most_left_point_x + length, corpus_height / 2 + height, twist))
    bez_points[2].handle_left = Vector((most_left_point_x + length, corpus_height / 2 + height, twist))
    bez_points[2].handle_right = Vector((most_left_point_x + length, corpus_height / 2 + height, twist))

    # lewy górny
    twist = random.uniform(-length / 3, length / 3)
    bez_points[3].co = Vector((most_left_point_x, corpus_height / 2 + height / 2, twist))
    bez_points[3].handle_left = Vector((most_left_point_x, corpus_height / 2 + height / 2, twist))
    bez_points[3].handle_right = Vector((most_left_point_x, corpus_height / 2 + height / 2, twist))

    solidify('Upper Fin Mesh', width)
    
    
def generate_eyes():
    # utworzenie krzywej
    ops.curve.primitive_bezier_circle_add(enter_editmode=True)
    curve = context.active_object
    curve.name = 'Eyes Curve'
    bez_points = curve.data.splines[0].bezier_points

    for bez_point in bez_points:
        bez_point.handle_left_type = draw_point_type()
        bez_point.handle_right_type = draw_point_type()

    x_center = -2*corpus_length/3
    y_center = corpus_height / 3
    # lewy
    bez_points[0].co = Vector((x_center - 1, y_center, 0.0))
    bez_points[0].handle_left = Vector((x_center - 1, y_center - 1, 0.0))
    bez_points[0].handle_right = Vector((x_center - 1, y_center + 1, 0.0))

    # góra
    bez_points[1].co = Vector((x_center, y_center + 1, 0.0))
    bez_points[1].handle_left = Vector((x_center - 1, y_center + 1, 0.0))
    bez_points[1].handle_right = Vector((x_center + 1, y_center + 1, 0.0))

    # prawo
    bez_points[2].co = Vector((x_center + 1, y_center, 0.0))
    bez_points[2].handle_left = Vector((x_center + 1, y_center + 1, 0.0))
    bez_points[2].handle_right = Vector((x_center + 1, y_center - 1, 0.0))

    # dół
    bez_points[3].co = Vector((x_center, y_center - 1, 0.0))
    bez_points[3].handle_left = Vector((x_center + 1, y_center - 1, 0.0))
    bez_points[3].handle_right = Vector((x_center - 1, y_center - 1, 0.0))

    solidify('Eyes Mesh', corpus_width + 2)


def generate_side_fins(length: float, height: float, width: float):
    # utworzenie krzywej
    ops.curve.primitive_bezier_circle_add(enter_editmode=True)
    curve = context.active_object
    curve.name = 'Left Fin Curve'
    bez_points = curve.data.splines[0].bezier_points

    for bez_point in bez_points:
        bez_point.handle_left_type = draw_point_type()
        bez_point.handle_right_type = draw_point_type()

    x = random.uniform(-2 * corpus_length / 3, -corpus_length / 4)
    x2 = x
    y = random.uniform(-corpus_height / 3, 0)
    # środek
    bez_points[0].co = Vector((x, y, 0.0))
    bez_points[0].handle_left = Vector((x - 1, y, 0.0))
    bez_points[0].handle_right = Vector((x + 1, y, 0.0))

    y = random.uniform(-corpus_height / 3, 0)
    # prawy
    bez_points[1].co = Vector((x + length, y, height))
    bez_points[1].handle_left = Vector((x + length + 1, y, height))
    bez_points[1].handle_right = Vector((x + length - 1, y, height))

    # środkowy 2
    cut = random.uniform(height / 2, height)
    x = random.uniform(-corpus_length / 3, x)
    bez_points[2].co = Vector((x, y, cut))
    bez_points[2].handle_left = Vector((x - 1, y, cut))
    bez_points[2].handle_right = Vector((x + 1, y, cut))

    # lewy
    bez_points[3].co = Vector((x2, y, height))
    bez_points[3].handle_left = Vector((x2 - 1, y, height))
    bez_points[3].handle_right = Vector((x2 + 1, y, height))

    solidify('Left Fin Mesh', width)
    

def delete_all_from_scene():
    # Select objects by type
    ops.object.mode_set(mode='OBJECT')
    for o in context.scene.objects:
        if o.type == 'MESH':
            o.select_set(True)
        else:
            o.select_set(False)
    # Call the operator only once
    ops.object.delete()
    
    for bpy_data_iter in (data.objects, data.meshes):
        for id_data in bpy_data_iter:
            bpy_data_iter.remove(id_data)
    # iterate over all images in the file
    for image in data.images:
        # don't do anything if the image has any users.
        if image.users:
            continue
        # remove the image otherwise
        data.images.remove(image)
            
            
def dump(obj, level=0):
   for attr in dir(obj):
       if hasattr( obj, "attr" ):
           print( "obj.%s = %s" % (attr, getattr(obj, attr)))
       else:
           print( attr )


delete_all_from_scene()

generate_corpus(15, 11, 3)
generate_eyes()
generate_tail(4, 4, 2, 0.5)
generate_upper_fin(4, 5, 5)
generate_side_fins(2, 2, 1)


ops.object.mode_set(mode='OBJECT')
ops.object.select_all(action='DESELECT')

context.view_layer.objects.active = data.objects["Corpus Mesh"]
ob = context.object
me = ob.data
# nowy mesh
bm = bmesh.new()
# wczytanie mesha
bm.from_mesh(me)
# podział na więcej ścian
#bmesh.ops.subdivide_edges(bm,edges=bm.edges,cuts=1,use_grid_fill=True)
# zapisanie spowrotem
bm.to_mesh(me)
me.update()

ops.object.mode_set(mode='EDIT')
bm = bmesh.from_edit_mesh(me)
bm.faces.ensure_lookup_table()
# ustawienie face select mode
#context.tool_settings.mesh_select_mode = [False, False, True]

i=0
for face in bm.faces:
    face.select = True
    mat = data.materials.new(name="Colour")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    texImage = mat.node_tree.nodes.new('ShaderNodeTexImage')
    texImage.image = rule54_gen()
    mat.node_tree.links.new(bsdf.inputs['Base Color'], texImage.outputs['Color'])
    # uwydatnienie kolorów
    mat.node_tree.nodes['Image Texture'].projection = 'BOX'
    mat.node_tree.nodes['Image Texture'].interpolation = 'Closest'
    ob.data.materials.append(mat)
    context.object.active_material_index=i
    ops.object.material_slot_assign()
    ops.uv.cube_project()
    i += 1
    face.select = False



bmesh.update_edit_mesh(me)

